"""
Performance optimization utilities for production deployment.

This module provides tools for optimizing application performance in production,
including caching, connection pooling, and resource management.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
import weakref
import psutil
import gc

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Central performance optimization manager.
    
    Provides caching, connection pooling, resource management,
    and performance monitoring capabilities.
    """
    
    def __init__(self):
        """Initialize the performance optimizer."""
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        self.connection_pools = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="optimizer")
        self.background_tasks = set()
        self._monitoring_enabled = True
        
        # Performance metrics
        self.metrics = {
            'request_count': 0,
            'total_response_time': 0.0,
            'max_response_time': 0.0,
            'min_response_time': float('inf'),
            'error_count': 0,
            'cache_hit_rate': 0.0
        }
        
        logger.info("PerformanceOptimizer initialized")
    
    def enable_monitoring(self):
        """Enable performance monitoring."""
        self._monitoring_enabled = True
        logger.info("Performance monitoring enabled")
    
    def disable_monitoring(self):
        """Disable performance monitoring."""
        self._monitoring_enabled = False
        logger.info("Performance monitoring disabled")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        total_cache_operations = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / total_cache_operations * 100 
                         if total_cache_operations > 0 else 0)
        
        avg_response_time = (self.metrics['total_response_time'] / self.metrics['request_count'] 
                           if self.metrics['request_count'] > 0 else 0)
        
        return {
            'cache': {
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'evictions': self.cache_stats['evictions'],
                'hit_rate': cache_hit_rate
            },
            'requests': {
                'total_count': self.metrics['request_count'],
                'error_count': self.metrics['error_count'],
                'avg_response_time': avg_response_time,
                'max_response_time': self.metrics['max_response_time'],
                'min_response_time': self.metrics['min_response_time'] if self.metrics['min_response_time'] != float('inf') else 0
            },
            'system': self._get_system_metrics(),
            'connection_pools': {name: pool.get_stats() for name, pool in self.connection_pools.items()}
        }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'thread_count': process.num_threads(),
                'file_descriptors': process.num_fds() if hasattr(process, 'num_fds') else 0
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {}


class CacheManager:
    """
    Advanced caching manager with TTL and LRU eviction.
    
    Provides thread-safe caching with automatic expiration and statistics.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of cached items
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._access_times = {}
        self._expiry_times = {}
        self._lock = threading.RLock()
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
        
        logger.info(f"CacheManager initialized with max_size={max_size}, default_ttl={default_ttl}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache."""
        with self._lock:
            current_time = time.time()
            
            # Check if key exists and not expired
            if key in self._cache:
                if current_time < self._expiry_times.get(key, 0):
                    self._access_times[key] = current_time
                    self._stats['hits'] += 1
                    return self._cache[key]
                else:
                    # Expired, remove
                    self._remove_key(key)
            
            self._stats['misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache."""
        with self._lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            # Evict if at max capacity and key is new
            if key not in self._cache and len(self._cache) >= self.max_size:
                self._evict_lru()
            
            self._cache[key] = value
            self._access_times[key] = current_time
            self._expiry_times[key] = current_time + ttl
    
    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._expiry_times.clear()
            logger.info("Cache cleared")
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all internal structures."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._expiry_times.pop(key, None)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._remove_key(lru_key)
        self._stats['evictions'] += 1
        logger.debug(f"Evicted LRU key: {lru_key}")
    
    def _cleanup_expired(self) -> None:
        """Background thread to cleanup expired entries."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                current_time = time.time()
                
                with self._lock:
                    expired_keys = [
                        key for key, expiry_time in self._expiry_times.items()
                        if current_time >= expiry_time
                    ]
                    
                    for key in expired_keys:
                        self._remove_key(key)
                    
                    if expired_keys:
                        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                        
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_operations = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_operations * 100 
                       if total_operations > 0 else 0)
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'hit_rate': hit_rate
            }


class ConnectionPool:
    """
    Generic connection pool for external services.
    
    Manages connections with automatic retry and health checking.
    """
    
    def __init__(self, name: str, factory: Callable, max_size: int = 10, 
                 health_check: Optional[Callable] = None):
        """
        Initialize connection pool.
        
        Args:
            name: Pool name for identification
            factory: Function to create new connections
            max_size: Maximum number of connections
            health_check: Function to check connection health
        """
        self.name = name
        self.factory = factory
        self.max_size = max_size
        self.health_check = health_check
        
        self._pool = []
        self._in_use = set()
        self._lock = threading.RLock()
        self._stats = {
            'total_created': 0,
            'total_acquired': 0,
            'total_released': 0,
            'total_failed': 0,
            'current_size': 0,
            'current_in_use': 0
        }
        
        logger.info(f"ConnectionPool '{name}' initialized with max_size={max_size}")
    
    def acquire(self, timeout: float = 30.0):
        """Acquire a connection from the pool."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                # Try to get existing connection
                if self._pool:
                    conn = self._pool.pop()
                    
                    # Health check if available
                    if self.health_check and not self._is_healthy(conn):
                        logger.debug(f"Unhealthy connection discarded from pool '{self.name}'")
                        continue
                    
                    self._in_use.add(conn)
                    self._stats['total_acquired'] += 1
                    self._stats['current_in_use'] = len(self._in_use)
                    return conn
                
                # Create new connection if under limit
                if len(self._in_use) < self.max_size:
                    try:
                        conn = self.factory()
                        self._in_use.add(conn)
                        self._stats['total_created'] += 1
                        self._stats['total_acquired'] += 1
                        self._stats['current_size'] += 1
                        self._stats['current_in_use'] = len(self._in_use)
                        logger.debug(f"New connection created for pool '{self.name}'")
                        return conn
                    except Exception as e:
                        self._stats['total_failed'] += 1
                        logger.error(f"Failed to create connection for pool '{self.name}': {e}")
                        raise
            
            # Wait a bit before retrying
            time.sleep(0.1)
        
        raise TimeoutError(f"Could not acquire connection from pool '{self.name}' within {timeout}s")
    
    def release(self, conn) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                
                # Return to pool if healthy and under capacity
                if (len(self._pool) < self.max_size and 
                    (not self.health_check or self._is_healthy(conn))):
                    self._pool.append(conn)
                else:
                    # Close connection if pool is full or unhealthy
                    self._close_connection(conn)
                    self._stats['current_size'] -= 1
                
                self._stats['total_released'] += 1
                self._stats['current_in_use'] = len(self._in_use)
                logger.debug(f"Connection released to pool '{self.name}'")
    
    def _is_healthy(self, conn) -> bool:
        """Check if connection is healthy."""
        try:
            return self.health_check(conn)
        except Exception as e:
            logger.debug(f"Health check failed for connection in pool '{self.name}': {e}")
            return False
    
    def _close_connection(self, conn) -> None:
        """Close a connection."""
        try:
            if hasattr(conn, 'close'):
                conn.close()
        except Exception as e:
            logger.debug(f"Error closing connection in pool '{self.name}': {e}")
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            # Close pooled connections
            for conn in self._pool:
                self._close_connection(conn)
            
            # Close in-use connections
            for conn in list(self._in_use):
                self._close_connection(conn)
            
            self._pool.clear()
            self._in_use.clear()
            self._stats['current_size'] = 0
            self._stats['current_in_use'] = 0
            
            logger.info(f"All connections closed for pool '{self.name}'")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                'name': self.name,
                'max_size': self.max_size,
                'current_size': len(self._pool) + len(self._in_use),
                'available': len(self._pool),
                'in_use': len(self._in_use),
                'total_created': self._stats['total_created'],
                'total_acquired': self._stats['total_acquired'],
                'total_released': self._stats['total_released'],
                'total_failed': self._stats['total_failed']
            }


def performance_monitor(func: Callable) -> Callable:
    """
    Decorator to monitor function performance.
    
    Tracks execution time, errors, and call frequency.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Record successful execution
            execution_time = time.time() - start_time
            logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            # Record failed execution
            execution_time = time.time() - start_time
            logger.warning(f"Function {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def cached(ttl: int = 3600, max_size: int = 128):
    """
    Decorator for caching function results with TTL.
    
    Args:
        ttl: Time to live in seconds
        max_size: Maximum cache size
    """
    def decorator(func: Callable) -> Callable:
        cache = CacheManager(max_size=max_size, default_ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            
            return result
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats
        
        return wrapper
    
    return decorator


def async_background(executor: Optional[ThreadPoolExecutor] = None):
    """
    Decorator to run function in background thread.
    
    Args:
        executor: Thread pool executor to use
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal executor
            if executor is None:
                executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix=func.__name__)
            
            future = executor.submit(func, *args, **kwargs)
            return future
        
        return wrapper
    
    return decorator


class MemoryManager:
    """
    Memory management utilities for production optimization.
    
    Provides memory monitoring, garbage collection optimization,
    and memory leak detection.
    """
    
    def __init__(self):
        """Initialize memory manager."""
        self.initial_memory = self._get_memory_usage()
        self.peak_memory = self.initial_memory
        self.gc_stats = {'collections': 0, 'freed_objects': 0}
        
        logger.info(f"MemoryManager initialized. Initial memory: {self.initial_memory:.2f} MB")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def optimize_gc(self) -> Dict[str, int]:
        """
        Optimize garbage collection.
        
        Returns:
            Dict with GC statistics
        """
        # Force garbage collection
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))
        
        self.gc_stats['collections'] += 1
        freed_objects = sum(collected)
        self.gc_stats['freed_objects'] += freed_objects
        
        current_memory = self._get_memory_usage()
        memory_freed = self.peak_memory - current_memory
        
        logger.debug(f"GC optimized: freed {freed_objects} objects, {memory_freed:.2f} MB memory")
        
        return {
            'freed_objects': freed_objects,
            'memory_before': self.peak_memory,
            'memory_after': current_memory,
            'memory_freed': memory_freed
        }
    
    def check_memory_usage(self, threshold_mb: float = 500.0) -> Dict[str, Any]:
        """
        Check current memory usage against threshold.
        
        Args:
            threshold_mb: Memory threshold in MB
            
        Returns:
            Dict with memory status
        """
        current_memory = self._get_memory_usage()
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        status = {
            'current_mb': current_memory,
            'peak_mb': self.peak_memory,
            'initial_mb': self.initial_memory,
            'growth_mb': current_memory - self.initial_memory,
            'threshold_mb': threshold_mb,
            'over_threshold': current_memory > threshold_mb
        }
        
        if status['over_threshold']:
            logger.warning(f"Memory usage {current_memory:.2f} MB exceeds threshold {threshold_mb} MB")
        
        return status
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        current_memory = self._get_memory_usage()
        
        # Get GC stats
        gc_stats = {}
        for i in range(3):
            gc_stats[f'generation_{i}'] = {
                'count': gc.get_count()[i],
                'threshold': gc.get_threshold()[i]
            }
        
        return {
            'current_mb': current_memory,
            'peak_mb': self.peak_memory,
            'initial_mb': self.initial_memory,
            'growth_mb': current_memory - self.initial_memory,
            'gc_collections': self.gc_stats['collections'],
            'gc_freed_objects': self.gc_stats['freed_objects'],
            'gc_details': gc_stats,
            'object_count': len(gc.get_objects())
        }


# Global instances for easy access
performance_optimizer = PerformanceOptimizer()
cache_manager = CacheManager()
memory_manager = MemoryManager()






