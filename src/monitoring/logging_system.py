"""
Production logging system with structured logging and log aggregation.

This module provides comprehensive logging capabilities for production deployment,
including structured logging, log rotation, filtering, and aggregation.
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import threading
from dataclasses import dataclass
import traceback


@dataclass
class LogConfig:
    """Configuration for logging system."""
    level: str = "INFO"
    format_type: str = "json"  # 'json' or 'text'
    console_enabled: bool = True
    file_enabled: bool = True
    file_path: str = "logs/app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 10
    rotation_enabled: bool = True
    sensitive_fields: List[str] = None
    include_traceback: bool = True
    include_thread_info: bool = True


class SensitiveDataFilter(logging.Filter):
    """
    Filter to remove or mask sensitive data from logs.
    
    Automatically detects and masks common sensitive patterns
    like passwords, tokens, and API keys.
    """
    
    def __init__(self, sensitive_fields: Optional[List[str]] = None):
        """
        Initialize sensitive data filter.
        
        Args:
            sensitive_fields: List of field names to mask
        """
        super().__init__()
        self.sensitive_fields = sensitive_fields or [
            'password', 'token', 'key', 'secret', 'auth', 'credential',
            'telegram_token', 'openai_api_key', 'assistant_id'
        ]
        self.mask_value = "***REDACTED***"
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to remove sensitive data."""
        try:
            # Mask sensitive data in message
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                record.msg = self._mask_sensitive_data(record.msg)
            
            # Mask sensitive data in formatted message
            if hasattr(record, 'getMessage'):
                original_getMessage = record.getMessage
                def masked_getMessage():
                    msg = original_getMessage()
                    return self._mask_sensitive_data(msg)
                record.getMessage = masked_getMessage
            
            # Mask sensitive data in extra fields
            if hasattr(record, '__dict__'):
                for key, value in record.__dict__.items():
                    if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                        if isinstance(value, str) and len(value) > 4:
                            setattr(record, key, self.mask_value)
                        elif isinstance(value, dict):
                            setattr(record, key, self._mask_dict(value))
            
            return True
            
        except Exception as e:
            # Don't break logging if filtering fails
            print(f"Error in sensitive data filter: {e}", file=sys.stderr)
            return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data patterns in text."""
        import re
        
        # Common patterns to mask
        patterns = [
            # Tokens and keys
            (r'(?i)(token|key|secret|password|auth)["\s]*[:=]["\s]*([^\s"]{8,})', r'\1: ***REDACTED***'),
            # Bearer tokens
            (r'(?i)bearer\s+([a-zA-Z0-9._-]{20,})', r'bearer ***REDACTED***'),
            # API keys
            (r'(?i)(api[_-]?key)["\s]*[:=]["\s]*([^\s"]{15,})', r'\1: ***REDACTED***'),
            # Long alphanumeric strings that might be tokens
            (r'\b[a-zA-Z0-9]{32,}\b', '***REDACTED***'),
        ]
        
        masked_text = text
        for pattern, replacement in patterns:
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text
    
    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive data in dictionary."""
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                masked[key] = self.mask_value
            elif isinstance(value, dict):
                masked[key] = self._mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [self._mask_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                masked[key] = value
        
        return masked


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Formats log records as JSON with additional metadata
    for better searchability and analysis.
    """
    
    def __init__(self, include_traceback: bool = True, include_thread_info: bool = True):
        """
        Initialize JSON formatter.
        
        Args:
            include_traceback: Whether to include traceback in logs
            include_thread_info: Whether to include thread information
        """
        super().__init__()
        self.include_traceback = include_traceback
        self.include_thread_info = include_thread_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            # Base log data
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
            
            # Add thread information if enabled
            if self.include_thread_info:
                log_data.update({
                    'thread_id': record.thread,
                    'thread_name': record.threadName,
                    'process_id': record.process,
                })
            
            # Add exception information if present
            if record.exc_info and self.include_traceback:
                log_data['exception'] = {
                    'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                    'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            
            # Add extra fields from record
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                    extra_fields[key] = value
            
            if extra_fields:
                log_data['extra'] = extra_fields
            
            return json.dumps(log_data, ensure_ascii=False, default=str)
            
        except Exception as e:
            # Fallback to simple message if JSON formatting fails
            return f"LOG_FORMAT_ERROR: {record.getMessage()} (Error: {e})"


class LogAggregator:
    """
    Log aggregation system for collecting and analyzing logs.
    
    Provides capabilities for log collection, filtering, searching,
    and basic analytics on log data.
    """
    
    def __init__(self, max_logs: int = 10000):
        """
        Initialize log aggregator.
        
        Args:
            max_logs: Maximum number of logs to keep in memory
        """
        self.max_logs = max_logs
        self.logs = []
        self.log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
        self._lock = threading.RLock()
        
        logger = logging.getLogger(__name__)
        logger.info(f"LogAggregator initialized with max_logs={max_logs}")
    
    def add_log(self, record: logging.LogRecord):
        """Add a log record to the aggregator."""
        with self._lock:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.threadName,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = str(record.exc_info[1])
            
            self.logs.append(log_entry)
            self.log_counts[record.levelname] += 1
            
            # Maintain max size
            if len(self.logs) > self.max_logs:
                removed = self.logs.pop(0)
                self.log_counts[removed['level']] -= 1
    
    def get_logs(self, level: Optional[str] = None, logger: Optional[str] = None, 
                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get logs with optional filtering.
        
        Args:
            level: Filter by log level
            logger: Filter by logger name
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        with self._lock:
            filtered_logs = self.logs
            
            if level:
                filtered_logs = [log for log in filtered_logs if log['level'] == level.upper()]
            
            if logger:
                filtered_logs = [log for log in filtered_logs if logger in log['logger']]
            
            # Return most recent logs first
            return filtered_logs[-limit:][::-1]
    
    def search_logs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search logs by message content.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching log entries
        """
        with self._lock:
            query_lower = query.lower()
            matching_logs = [
                log for log in self.logs
                if query_lower in log['message'].lower()
            ]
            
            return matching_logs[-limit:][::-1]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get log statistics and counts."""
        with self._lock:
            total_logs = sum(self.log_counts.values())
            
            return {
                'total_logs': total_logs,
                'counts_by_level': dict(self.log_counts),
                'current_size': len(self.logs),
                'max_size': self.max_logs,
                'usage_percent': (len(self.logs) / self.max_logs * 100) if self.max_logs > 0 else 0
            }
    
    def clear_logs(self):
        """Clear all logs from the aggregator."""
        with self._lock:
            self.logs.clear()
            self.log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}


class LoggingHandler(logging.Handler):
    """Custom logging handler that sends logs to the aggregator."""
    
    def __init__(self, aggregator: LogAggregator):
        """Initialize with log aggregator."""
        super().__init__()
        self.aggregator = aggregator
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to aggregator."""
        try:
            self.aggregator.add_log(record)
        except Exception:
            # Don't break logging if aggregation fails
            pass


class LoggingSystem:
    """
    Comprehensive logging system for production deployment.
    
    Provides structured logging, filtering, rotation, and aggregation
    with production-ready configuration and monitoring.
    """
    
    def __init__(self, config: Optional[LogConfig] = None):
        """
        Initialize logging system.
        
        Args:
            config: Logging configuration
        """
        self.config = config or LogConfig()
        self.aggregator = LogAggregator() if self.config.file_enabled else None
        self.handlers = []
        self.filters = []
        
        # Setup logging
        self._setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("LoggingSystem initialized with production configuration")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Setup console handler
        if self.config.console_enabled:
            self._setup_console_handler(root_logger)
        
        # Setup file handler
        if self.config.file_enabled:
            self._setup_file_handler(root_logger)
        
        # Setup aggregation handler
        if self.aggregator:
            self._setup_aggregation_handler(root_logger)
        
        # Add sensitive data filter
        sensitive_filter = SensitiveDataFilter(self.config.sensitive_fields)
        self._add_filter_to_all_handlers(sensitive_filter)
    
    def _setup_console_handler(self, logger: logging.Logger):
        """Setup console logging handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.level.upper()))
        
        if self.config.format_type == 'json':
            formatter = JSONFormatter(
                include_traceback=self.config.include_traceback,
                include_thread_info=self.config.include_thread_info
            )
        else:
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        self.handlers.append(console_handler)
    
    def _setup_file_handler(self, logger: logging.Logger):
        """Setup file logging handler with rotation."""
        # Ensure log directory exists
        log_path = Path(self.config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config.rotation_enabled:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.config.file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(
                filename=self.config.file_path,
                encoding='utf-8'
            )
        
        file_handler.setLevel(getattr(logging, self.config.level.upper()))
        
        # Always use JSON format for file logs
        formatter = JSONFormatter(
            include_traceback=self.config.include_traceback,
            include_thread_info=self.config.include_thread_info
        )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        self.handlers.append(file_handler)
    
    def _setup_aggregation_handler(self, logger: logging.Logger):
        """Setup log aggregation handler."""
        aggregation_handler = LoggingHandler(self.aggregator)
        aggregation_handler.setLevel(getattr(logging, self.config.level.upper()))
        
        logger.addHandler(aggregation_handler)
        self.handlers.append(aggregation_handler)
    
    def _add_filter_to_all_handlers(self, filter_obj: logging.Filter):
        """Add filter to all handlers."""
        for handler in self.handlers:
            handler.addFilter(filter_obj)
        self.filters.append(filter_obj)
    
    def add_custom_filter(self, filter_obj: logging.Filter):
        """Add custom filter to all handlers."""
        self._add_filter_to_all_handlers(filter_obj)
    
    def get_logs(self, **kwargs) -> List[Dict[str, Any]]:
        """Get logs from aggregator."""
        if self.aggregator:
            return self.aggregator.get_logs(**kwargs)
        return []
    
    def search_logs(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs in aggregator."""
        if self.aggregator:
            return self.aggregator.search_logs(query, limit)
        return []
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            'level': self.config.level,
            'console_enabled': self.config.console_enabled,
            'file_enabled': self.config.file_enabled,
            'file_path': self.config.file_path,
            'handlers_count': len(self.handlers),
            'filters_count': len(self.filters)
        }
        
        if self.aggregator:
            stats.update(self.aggregator.get_log_statistics())
        
        return stats
    
    def set_log_level(self, level: str):
        """Change log level dynamically."""
        self.config.level = level.upper()
        
        # Update all handlers
        log_level = getattr(logging, level.upper())
        for handler in self.handlers:
            handler.setLevel(log_level)
        
        # Update root logger
        logging.getLogger().setLevel(log_level)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Log level changed to {level.upper()}")
    
    def rotate_logs(self):
        """Manually rotate log files."""
        for handler in self.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.doRollover()
                logger = logging.getLogger(__name__)
                logger.info("Log files rotated manually")
    
    def cleanup(self):
        """Cleanup logging system."""
        # Close all handlers
        for handler in self.handlers:
            handler.close()
        
        # Clear aggregator
        if self.aggregator:
            self.aggregator.clear_logs()
        
        logger = logging.getLogger(__name__)
        logger.info("LoggingSystem cleaned up")


# Global logging system instance
logging_system = None


def setup_production_logging(config: Optional[LogConfig] = None) -> LoggingSystem:
    """
    Setup production logging system.
    
    Args:
        config: Logging configuration
        
    Returns:
        Configured logging system
    """
    global logging_system
    
    if logging_system is None:
        logging_system = LoggingSystem(config)
    
    return logging_system


def get_logging_system() -> Optional[LoggingSystem]:
    """Get the global logging system instance."""
    return logging_system


# Setup structured logging for common loggers
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup a logger with production configuration.
    
    Args:
        name: Logger name
        level: Log level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Add contextual information
    def add_context(func):
        def wrapper(*args, **kwargs):
            # Add request context if available
            try:
                from flask import has_request_context, request
                if has_request_context():
                    extra = kwargs.get('extra', {})
                    extra.update({
                        'request_id': getattr(request, 'id', None),
                        'user_id': getattr(request, 'user_id', None),
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', '')
                    })
                    kwargs['extra'] = extra
            except ImportError:
                pass  # Flask not available
            
            return func(*args, **kwargs)
        return wrapper
    
    # Wrap logging methods to add context
    logger.debug = add_context(logger.debug)
    logger.info = add_context(logger.info)
    logger.warning = add_context(logger.warning)
    logger.error = add_context(logger.error)
    logger.critical = add_context(logger.critical)
    
    return logger








