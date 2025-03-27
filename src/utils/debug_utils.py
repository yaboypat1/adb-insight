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
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

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
    _instance = None
    _lock = threading.Lock()
    
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DebugLogger, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        self.entries: List[DebugEntry] = []
        self.max_entries = 1000  # Keep last 1000 entries
        self.listeners: List[Callable] = []
        self.entry_queue = Queue()
        self._start_queue_processor()
        
        # Set up file logger
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'adb_insight_{datetime.now().strftime("%Y%m%d")}.log')
        
        self.logger = logging.getLogger('debug')
        self.logger.setLevel(logging.DEBUG)
>>>>>>> parent of 5c1894b (all current bugs fixed)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
=======
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DebugLogger, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        self.entries: List[DebugEntry] = []
        self.max_entries = 1000  # Keep last 1000 entries
        self.listeners: List[Callable] = []
        self.entry_queue = Queue()
        self._start_queue_processor()
        
        # Set up file logger
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'adb_insight_{datetime.now().strftime("%Y%m%d")}.log')
        
        self.logger = logging.getLogger('debug')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
>>>>>>> parent of 5c1894b (all current bugs fixed)
        # Formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(category)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _start_queue_processor(self):
        def process_queue():
            while True:
                entry = self.entry_queue.get()
                if entry is None:  # Shutdown signal
                    break
                    
                with self._lock:
                    self.entries.append(entry)
                    if len(self.entries) > self.max_entries:
                        self.entries.pop(0)
                    
                    # Notify listeners
                    for listener in self.listeners:
                        try:
                            listener(entry)
                        except Exception as e:
                            print(f"Error in debug listener: {str(e)}")
        
        self.queue_thread = threading.Thread(target=process_queue, daemon=True)
        self.queue_thread.start()
    
    def add_listener(self, listener: Callable):
        """Add a listener to be notified of new debug entries"""
        with self._lock:
            if listener not in self.listeners:
                self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
        """Remove a debug entry listener"""
        with self._lock:
            if listener in self.listeners:
                self.listeners.remove(listener)
    
    def log_operation(self, operation: str, status: str, details: str, 
                     duration: float, package_name: Optional[str] = None):
        """Log a debug entry for an operation"""
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
        entry = DebugEntry(
            timestamp=datetime.now(),
            operation=operation,
            status=status,
            details=details,
            duration=duration,
            package_name=package_name
        )
        self.entry_queue.put(entry)
        
        # Log to file
        if status == 'error':
            self.logger.error(f"{operation}: {details}")
        elif status == 'warning':
            self.logger.warning(f"{operation}: {details}")
        else:
            self.logger.info(f"{operation}: {details}")
            
    def log_debug(self, message: str, category: str = "general", level: str = "debug",
                extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message with category and optional extra info"""
        try:
            # Validate and convert category
            try:
                cat = LogCategory[category.upper()]
            except KeyError:
                cat = LogCategory.SYSTEM
                
            # Validate and convert level
            try:
                lvl = LogLevel[level.upper()]
            except KeyError:
                lvl = LogLevel.DEBUG
                
            # Format extra info
            if extra:
                extra_str = " | " + " | ".join(f"{k}={v}" for k, v in extra.items())
            else:
                extra_str = ""
                
            # Create log record
            record = self.logger.makeRecord(
                'debug_logger',
                logging.DEBUG,
                __file__,
                0,
                message + extra_str,
                None,
                None,
                func=None,
                extra={'category': cat.value}
            )
            
            # Log the message
            self.logger.handle(record)
            
            # Notify listeners
            self._notify_listeners(message, lvl, cat)
            
        except Exception as e:
            # Fallback logging
            print(f"Debug logging failed: {str(e)}")
            print(f"Original message: {message}")
            
    def _notify_listeners(self, message: str, level: LogLevel, category: LogCategory) -> None:
        """Notify all listeners of a new debug message"""
        for listener in self.listeners:
            try:
                listener(message, level, category)
            except Exception as e:
                self.logger.error(f"Error in debug listener: {str(e)}")
                
    def get_entries(self, limit: int = None, 
                   operation_filter: str = None,
                   status_filter: str = None,
                   package_filter: str = None) -> List[DebugEntry]:
        """Get debug entries with optional filtering"""
        with self._lock:
            entries = self.entries.copy()
        
        # Apply filters
        if operation_filter:
            entries = [e for e in entries if operation_filter.lower() in e.operation.lower()]
        if status_filter:
            entries = [e for e in entries if status_filter.lower() in e.status.lower()]
        if package_filter:
            entries = [e for e in entries if e.package_name and package_filter.lower() in e.package_name.lower()]
        
        # Apply limit
        if limit:
            entries = entries[-limit:]
            
        return entries
    
    def clear(self):
        """Clear all debug entries"""
<<<<<<< HEAD
<<<<<<< HEAD
        self.entries.clear()
        
        # Also clear log file
        try:
            with open(self.debug_handler.baseFilename, 'w'):
                pass
        except Exception as e:
            self.logger.error(f"Failed to clear debug log file: {str(e)}")

=======
        with self._lock:
            self.entries.clear()
    
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
        with self._lock:
            self.entries.clear()
    
>>>>>>> parent of 5c1894b (all current bugs fixed)
    def shutdown(self):
        """Shutdown the debug logger"""
        self.entry_queue.put(None)  # Signal queue processor to stop
        self.queue_thread.join(timeout=1.0)  # Wait for thread to finish
        
    def get_recent_logs(self, count: int = 50, level: Optional[str] = None,
                     category: Optional[str] = None) -> List[str]:
        """Get recent debug logs with optional filtering"""
        try:
<<<<<<< HEAD
<<<<<<< HEAD
            with open(self.debug_handler.baseFilename, 'r') as f:
=======
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
            log_file = os.path.join(self.log_dir, 'debug.log')
            if not os.path.exists(log_file):
                return []
                
            with open(log_file, 'r') as f:
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
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
<<<<<<< HEAD
<<<<<<< HEAD
            with open(self.debug_handler.baseFilename, 'w'):
                pass
=======
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
            log_file = os.path.join(self.log_dir, 'debug.log')
            if os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    f.write('')
                    
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
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
            
<<<<<<< HEAD
<<<<<<< HEAD
            with open(self.debug_handler.baseFilename, 'r') as f:
=======
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
            log_file = os.path.join(self.log_dir, 'debug.log')
            if not os.path.exists(log_file):
                return stats
                
            with open(log_file, 'r') as f:
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
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
