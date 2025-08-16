#!/usr/bin/env python3
"""
Professional Auto-Update System for Telegram Bot Manager
Provides safe, reliable, and monitored application updates with rollback capability.
"""

import os
import sys
import json
import time
import shutil
import logging
import datetime
import subprocess
import threading
from pathlib import Path
from typing import Dict, Tuple, Optional, List

import config_manager as cm
import bot_manager as bm
import version


class AutoUpdater:
    """Professional auto-update system with backup and rollback capabilities"""
    
    def __init__(self, app_dir: str = None):
        self.app_dir = Path(app_dir or os.getcwd())
        self.backup_dir = self.app_dir / "backups"
        self.log_dir = self.app_dir / "logs"
        self.update_lock_file = self.app_dir / ".update_lock"
        
        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup dedicated logger
        self.logger = self._setup_logger()
        
        # Update state tracking
        self.update_state = {
            "status": "idle",  # idle, checking, backing_up, updating, restarting, completed, failed
            "progress": 0,     # 0-100
            "message": "",
            "start_time": None,
            "error": None,
            "backup_id": None,
            "local_commit": None,
            "remote_commit": None
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup dedicated logger for update operations"""
        logger = logging.getLogger("auto_updater")
        logger.setLevel(logging.INFO)
        
        # File handler for update logs
        update_log_file = self.log_dir / "auto_update.log"
        file_handler = logging.FileHandler(update_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] AUTO-UPDATE %(levelname)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _run_git_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute git command safely with proper error handling"""
        try:
            result = subprocess.run(
                f"git {command}",
                shell=True,
                cwd=self.app_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            if success:
                self.logger.info(f"✅ Git command succeeded: git {command}")
            else:
                self.logger.error(f"❌ Git command failed: git {command} - {stderr}")
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ Git command timeout: git {command}")
            return False, "", "Command timeout"
        except Exception as e:
            self.logger.error(f"💥 Git command error: git {command} - {str(e)}")
            return False, "", str(e)
    
    def is_update_in_progress(self) -> bool:
        """Check if update is currently in progress"""
        return self.update_lock_file.exists() or self.update_state["status"] != "idle"
    
    def _create_backup(self) -> Tuple[bool, str]:
        """Create backup of current state before update"""
        try:
            # Generate backup ID with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"
            backup_path = self.backup_dir / backup_id
            
            self.logger.info(f"📦 Creating backup: {backup_id}")
            self.update_state.update({
                "status": "backing_up",
                "progress": 10,
                "message": f"Creating backup: {backup_id}",
                "backup_id": backup_id
            })
            
            # Create backup directory
            backup_path.mkdir(exist_ok=True)
            
            # Backup critical files
            critical_files = [
                "src/config_manager.py",
                "src/bot_manager.py", 
                "src/telegram_bot.py",
                "src/app.py",
                "src/version.py",
                "bot_configs.json",
                "requirements.txt",
                "README.md"
            ]
            
            for file_path in critical_files:
                src_file = self.app_dir / file_path
                if src_file.exists():
                    dst_file = backup_path / file_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    self.logger.debug(f"📋 Backed up: {file_path}")
            
            # Save current git commit
            success, commit_hash, _ = self._run_git_command("rev-parse HEAD")
            if success:
                (backup_path / "commit_hash.txt").write_text(commit_hash)
            
            # Save current bot configs
            try:
                with cm.BOT_CONFIGS_LOCK:
                    backup_configs = {}
                    for bot_id, bot_data in cm.BOT_CONFIGS.items():
                        backup_configs[bot_id] = {
                            "id": bot_data["id"],
                            "config": bot_data["config"],
                            "status": bot_data.get("status", "unknown")
                        }
                    
                    with open(backup_path / "bot_configs_backup.json", "w", encoding="utf-8") as f:
                        json.dump(backup_configs, f, indent=2, ensure_ascii=False)
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Could not backup bot configs: {e}")
            
            # Save backup metadata
            backup_metadata = {
                "backup_id": backup_id,
                "created_at": datetime.datetime.now().isoformat(),
                "commit_hash": commit_hash if success else "unknown",
                "version": version.get_version(),
                "files_count": len(list(backup_path.rglob("*"))),
                "app_dir": str(self.app_dir)
            }
            
            with open(backup_path / "backup_metadata.json", "w") as f:
                json.dump(backup_metadata, f, indent=2)
            
            self.logger.info(f"✅ Backup created successfully: {backup_id}")
            return True, backup_id
            
        except Exception as e:
            self.logger.error(f"💥 Backup creation failed: {str(e)}")
            return False, str(e)
    
    def _restore_backup(self, backup_id: str) -> Tuple[bool, str]:
        """Restore from backup in case of failed update"""
        try:
            backup_path = self.backup_dir / backup_id
            if not backup_path.exists():
                return False, f"Backup {backup_id} not found"
            
            self.logger.info(f"🔄 Restoring from backup: {backup_id}")
            
            # Load backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    self.logger.info(f"📋 Restoring to commit: {metadata.get('commit_hash', 'unknown')}")
            
            # Restore critical files
            for file_path in backup_path.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith(("_metadata.json", "commit_hash.txt")):
                    relative_path = file_path.relative_to(backup_path)
                    target_path = self.app_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, target_path)
                    self.logger.debug(f"📋 Restored: {relative_path}")
            
            # Restore git commit if possible
            commit_file = backup_path / "commit_hash.txt"
            if commit_file.exists():
                commit_hash = commit_file.read_text().strip()
                success, _, stderr = self._run_git_command(f"reset --hard {commit_hash}")
                if not success:
                    self.logger.warning(f"⚠️ Could not restore git commit: {stderr}")
            
            self.logger.info(f"✅ Backup restored successfully: {backup_id}")
            return True, f"Restored from backup {backup_id}"
            
        except Exception as e:
            self.logger.error(f"💥 Backup restore failed: {str(e)}")
            return False, str(e)
    
    def check_for_updates(self) -> Dict:
        """Check for available updates with detailed information"""
        try:
            self.logger.info("🔍 Checking for updates...")
            self.update_state.update({
                "status": "checking",
                "progress": 5,
                "message": "Checking for updates..."
            })
            
            # Fetch latest changes
            success, _, stderr = self._run_git_command("fetch origin")
            if not success:
                return {
                    "success": False,
                    "error": f"Failed to fetch updates: {stderr}",
                    "has_updates": False
                }
            
            # Get current and remote commits
            success, local_commit, _ = self._run_git_command("rev-parse HEAD")
            if not success:
                return {"success": False, "error": "Could not get local commit"}
            
            success, remote_commit, _ = self._run_git_command("rev-parse origin/master")
            if not success:
                return {"success": False, "error": "Could not get remote commit"}
            
            # Check if updates available
            has_updates = local_commit != remote_commit
            
            # Get commit log if updates available
            commit_log = []
            if has_updates:
                success, log_output, _ = self._run_git_command(
                    f"log {local_commit}..{remote_commit} --oneline --max-count=10"
                )
                if success and log_output:
                    commit_log = log_output.split('\n')
            
            result = {
                "success": True,
                "has_updates": has_updates,
                "local_commit": local_commit[:8],
                "remote_commit": remote_commit[:8],
                "commit_log": commit_log,
                "current_version": version.get_version(),
                "message": "Updates available" if has_updates else "No updates available"
            }
            
            self.update_state.update({
                "status": "idle",
                "progress": 0,
                "message": result["message"],
                "local_commit": local_commit[:8],
                "remote_commit": remote_commit[:8]
            })
            
            self.logger.info(f"✅ Update check completed: {result['message']}")
            return result
            
        except Exception as e:
            self.logger.error(f"💥 Update check failed: {str(e)}")
            self.update_state.update({
                "status": "idle",
                "progress": 0,
                "error": str(e)
            })
            return {"success": False, "error": str(e), "has_updates": False}
    
    def perform_update(self) -> Dict:
        """Perform complete update with backup and rollback capability"""
        if self.is_update_in_progress():
            return {
                "success": False,
                "error": "Update already in progress",
                "status": self.update_state["status"]
            }
        
        try:
            # Create update lock
            self.update_lock_file.touch()
            self.update_state.update({
                "status": "updating",
                "progress": 0,
                "message": "Starting update process...",
                "start_time": datetime.datetime.now().isoformat(),
                "error": None
            })
            
            self.logger.info("🚀 Starting professional update process...")
            
            # Step 1: Pre-update checks
            self.update_state.update({"progress": 5, "message": "Running pre-update checks..."})
            check_result = self.check_for_updates()
            if not check_result["success"]:
                raise Exception(f"Pre-update check failed: {check_result['error']}")
            
            if not check_result["has_updates"]:
                raise Exception("No updates available")
            
            # Step 2: Professional bot stopping (NO DEADLOCK)
            self.update_state.update({"progress": 15, "message": "Professional bot stopping..."})
            self.logger.info("🛑 Professional bot stopping for auto-update...")
            
            try:
                success, message = bm.stop_all_bots_for_update(total_timeout=20)
                if success:
                    self.logger.info(f"✅ Professional bot stopping completed: {message}")
                else:
                    self.logger.warning(f"⚠️ Bot stopping completed with issues: {message}")
                    # Continue anyway - non-critical for update
                    
            except Exception as e:
                self.logger.error(f"❌ Error in professional bot stopping: {e}")
                self.logger.info("🔄 Continuing with update despite bot stopping issues...")
            
            # Step 3: Create backup
            self.update_state.update({"progress": 25, "message": "Creating backup..."})
            backup_success, backup_result = self._create_backup()
            if not backup_success:
                raise Exception(f"Backup creation failed: {backup_result}")
            
            backup_id = backup_result
            self.update_state["backup_id"] = backup_id
            
            # Step 4: Perform git pull
            self.update_state.update({"progress": 50, "message": "Downloading updates..."})
            self.logger.info("📥 Performing git pull...")
            success, stdout, stderr = self._run_git_command("pull origin master")
            if not success:
                # Rollback on failure
                self.logger.error(f"📥 Git pull failed: {stderr}")
                self._restore_backup(backup_id)
                raise Exception(f"Git pull failed: {stderr}")
            
            # Step 5: Validate update
            self.update_state.update({"progress": 70, "message": "Validating update..."})
            self.logger.info("✅ Validating update...")
            
            # Check if critical files exist
            critical_files = ["src/app.py", "src/bot_manager.py", "requirements.txt"]
            for file_path in critical_files:
                if not (self.app_dir / file_path).exists():
                    self.logger.error(f"💥 Critical file missing after update: {file_path}")
                    self._restore_backup(backup_id)
                    raise Exception(f"Critical file missing: {file_path}")
            
            # Step 6: Save updated configs
            self.update_state.update({"progress": 80, "message": "Saving configurations..."})
            cm.save_configs_async()
            time.sleep(1)  # Ensure save completes
            
            # Step 7: Prepare for restart
            self.update_state.update({"progress": 90, "message": "Preparing restart..."})
            self.logger.info("🔄 Preparing application restart...")
            
            # Create restart script
            restart_script = self._create_restart_script()
            
            # Step 8: Schedule restart
            self.update_state.update({"progress": 95, "message": "Restarting application..."})
            self.logger.info("✅ Update completed successfully, restarting application...")
            
            # Clean up lock file before restart
            if self.update_lock_file.exists():
                self.update_lock_file.unlink()
            
            # Execute restart
            self._execute_restart(restart_script)
            
            return {
                "success": True,
                "message": "Update completed successfully",
                "backup_id": backup_id,
                "new_version": version.get_version()
            }
            
        except Exception as e:
            self.logger.error(f"💥 Update failed: {str(e)}")
            self.update_state.update({
                "status": "failed",
                "progress": 0,
                "error": str(e)
            })
            
            # Clean up lock file
            if self.update_lock_file.exists():
                self.update_lock_file.unlink()
            
            return {
                "success": False,
                "error": str(e),
                "backup_id": self.update_state.get("backup_id")
            }
    
    def _create_restart_script(self) -> str:
        """Create a restart script for reliable application restart"""
        restart_script = self.app_dir / "restart_app.sh"
        
        script_content = f"""#!/bin/bash
# Professional Application Restart Script
# Generated by Auto-Updater

echo "🔄 Starting application restart process..."
cd "{self.app_dir}"

# Kill any existing processes
echo "🛑 Stopping existing processes..."
pkill -f "python.*app.py" || true
sleep 2

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Navigate to src directory
cd src

# Start application in background
echo "🚀 Starting application..."
nohup python app.py > ../logs/app_restart.log 2>&1 &

# Get PID
APP_PID=$!
echo "📋 Application started with PID: $APP_PID"

# Wait a moment and check if it's running
sleep 3
if kill -0 "$APP_PID" 2>/dev/null; then
    echo "✅ Application started successfully!"
    
    # Wait for health check
    for i in {{1..30}}; do
        if curl -s -u admin:securepassword123 http://localhost:60183/api/v2/system/health > /dev/null 2>&1; then
            echo "✅ Health check passed!"
            break
        fi
        echo "⏳ Waiting for application to be ready... ($i/30)"
        sleep 2
    done
else
    echo "❌ Application failed to start!"
    exit 1
fi

# Clean up this script
rm -f "{restart_script}"
echo "🎉 Restart completed successfully!"
"""
        
        restart_script.write_text(script_content)
        restart_script.chmod(0o755)
        
        return str(restart_script)
    
    def _execute_restart(self, restart_script: str):
        """Execute restart script in background"""
        def delayed_restart():
            time.sleep(2)  # Give time for response to be sent
            try:
                subprocess.Popen(["/bin/bash", restart_script], 
                               cwd=self.app_dir,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            except Exception as e:
                self.logger.error(f"💥 Restart execution failed: {e}")
        
        thread = threading.Thread(target=delayed_restart, daemon=True)
        thread.start()
    
    def get_update_status(self) -> Dict:
        """Get current update status for web interface"""
        return {
            "status": self.update_state["status"],
            "progress": self.update_state["progress"],
            "message": self.update_state["message"],
            "start_time": self.update_state["start_time"],
            "error": self.update_state["error"],
            "backup_id": self.update_state["backup_id"],
            "is_in_progress": self.is_update_in_progress()
        }
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                metadata_file = backup_dir / "backup_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                            backups.append({
                                "backup_id": metadata["backup_id"],
                                "created_at": metadata["created_at"],
                                "commit_hash": metadata.get("commit_hash", "unknown")[:8],
                                "version": metadata.get("version", "unknown"),
                                "files_count": metadata.get("files_count", 0),
                                "size_mb": round(sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()) / 1024 / 1024, 2)
                            })
                    except Exception as e:
                        self.logger.warning(f"Could not read backup metadata for {backup_dir.name}: {e}")
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 5) -> Dict:
        """Clean up old backups, keeping only the specified number"""
        try:
            backups = self.list_backups()
            if len(backups) <= keep_count:
                return {"success": True, "message": f"No cleanup needed, {len(backups)} backups found"}
            
            backups_to_remove = backups[keep_count:]
            removed_count = 0
            
            for backup in backups_to_remove:
                backup_path = self.backup_dir / backup["backup_id"]
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    removed_count += 1
                    self.logger.info(f"🗑️ Removed old backup: {backup['backup_id']}")
            
            return {
                "success": True,
                "message": f"Cleaned up {removed_count} old backups, kept {keep_count} newest",
                "removed_count": removed_count
            }
            
        except Exception as e:
            self.logger.error(f"💥 Backup cleanup failed: {str(e)}")
            return {"success": False, "error": str(e)}


# Global instance
auto_updater = AutoUpdater()
