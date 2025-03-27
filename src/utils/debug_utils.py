from datetime import datetime
from queue import Queue
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import threading
import logging
import os
from pathlib import Path

@dataclass
class DebugEntry:
    timestamp: datetime
    operation: str
    status: str
    details: str
    duration: float
    package_name: Optional[str] = None

class LogLevel(Enum):
    """Log levels for debug messages"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class LogCategory(Enum):
    """Categories for debug messages"""
    ADB = "adb"
    DEVICE = "device"
    APP = "app"
    MEMORY = "memory"
    ANALYTICS = "analytics"
    UI = "ui"
    SYSTEM = "system"

class DebugLogger:
    """Debug logging utility"""
    
    def __init__(self):
        """Initialize debug logger"""
        # Set up logger
        self.logger = logging.getLogger('debug')
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Set up log directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up debug log file if no handlers exist
        if not self.logger.handlers:
            self.debug_handler = logging.FileHandler(os.path.join(log_dir, 'debug.log'))
            self.debug_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
            self.debug_handler.setFormatter(formatter)
            self.logger.addHandler(self.debug_handler)
            self.logger.setLevel(logging.DEBUG)
        
        # Debug entries
        self.entries: List[DebugEntry] = []
        self.max_entries = 1000  # Keep last 1000 entries
        
        # Listeners for debug events
        self.listeners: List[Callable] = []
        
        # Message queue for thread safety
        self.queue = Queue()
        self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.queue_thread.start()

    def _process_queue(self):
        """Process messages from queue"""
        while True:
            try:
                message, level, category = self.queue.get()
                self._notify_listeners(message, level, category)
                self.queue.task_done()
            except Exception as e:
                self.logger.error(f"Error processing debug message: {str(e)}")

    def add_listener(self, listener: Callable):
        """Add a listener for debug messages"""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def remove_listener(self, listener: Callable):
        """Remove a debug message listener"""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def log_debug(self, message: str, category: str = None, level: str = "debug"):
        """Log a debug message"""
        if category:
            message = f"[{category.upper()}] {message}"
        
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        
        # Add to queue for listeners
        self.queue.put((message, level, category))
        
        # Create debug entry
        entry = DebugEntry(
            timestamp=datetime.now(),
            operation=category,
            status=level,
            details=message,
            duration=0.0
        )
        
        # Add to entries list
        self.entries.append(entry)
        
        # Trim entries if needed
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def _notify_listeners(self, message: str, level: str, category: str):
        """Notify all listeners of a debug message"""
        for listener in self.listeners:
            try:
                listener(message, level, category)
            except Exception as e:
                self.logger.error(f"Error in debug listener: {str(e)}")

    def get_entries(self, limit: Optional[int] = None, 
                   category: Optional[str] = None,
                   level: Optional[str] = None) -> List[DebugEntry]:
        """Get debug entries with optional filtering"""
        entries = self.entries
        
        if category:
            entries = [e for e in entries if e.operation == category]
            
        if level:
            entries = [e for e in entries if e.status == level]
            
        if limit:
            entries = entries[-limit:]
            
        return entries

    def clear(self):
        """Clear all debug entries"""
        self.entries.clear()
        
        # Also clear log file
        try:
            with open(self.debug_handler.baseFilename, 'w'):
                pass
        except Exception as e:
            self.logger.error(f"Failed to clear debug log file: {str(e)}")

    def shutdown(self):
        """Shutdown the debug logger"""
        self.queue.put(None)  # Signal queue processor to stop
        self.queue_thread.join(timeout=1.0)  # Wait for thread to finish

    def get_recent_logs(self, count: int = 50, level: Optional[str] = None,
                     category: Optional[str] = None) -> List[str]:
        """Get recent debug logs with optional filtering"""
        try:
            with open(self.debug_handler.baseFilename, 'r') as f:
                lines = f.readlines()
                
            # Apply filters
            filtered = []
            for line in reversed(lines):
                if len(filtered) >= count:
                    break
                    
                if level and f" - {level.upper()} - " not in line:
                    continue
                    
                if category and f"[{category.upper()}]" not in line:
                    continue
                    
                filtered.append(line.strip())
                
            return list(reversed(filtered))
            
        except Exception as e:
            print(f"Failed to read debug log: {str(e)}")
            return []
            
    def clear_log(self) -> None:
        """Clear the debug log file"""
        try:
            with open(self.debug_handler.baseFilename, 'w'):
                pass
        except Exception as e:
            print(f"Failed to clear debug log: {str(e)}")
            
    def get_log_stats(self) -> Dict[str, int]:
        """Get statistics about logged messages"""
        try:
            stats = {
                'total': 0,
                'debug': 0,
                'info': 0,
                'warning': 0,
                'error': 0
            }
            
            with open(self.debug_handler.baseFilename, 'r') as f:
                for line in f:
                    stats['total'] += 1
                    for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                        if f" - {level} - " in line:
                            stats[level.lower()] += 1
                            break
                            
            return stats
            
        except Exception as e:
            print(f"Failed to get log stats: {str(e)}")
            return {
                'total': 0,
                'debug': 0,
                'info': 0,
                'warning': 0,
                'error': 0
            }
