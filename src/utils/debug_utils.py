from datetime import datetime
from queue import Queue
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import threading
import logging
import os

@dataclass
class DebugEntry:
    timestamp: datetime
    operation: str
    status: str
    details: str
    duration: float
    package_name: Optional[str] = None

class DebugLogger:
    _instance = None
    _lock = threading.Lock()
    
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
        
        # Format
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
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
        """Remove a debug entry listener"""
        with self._lock:
            if listener in self.listeners:
                self.listeners.remove(listener)
    
    def log_operation(self, operation: str, status: str, details: str, 
                     duration: float, package_name: Optional[str] = None):
        """Log a debug entry for an operation"""
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
    
    def log_debug(self, message: str, operation: str = '', status: str = 'info', **kwargs):
        """Log a debug message"""
        entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'operation': operation,
            'status': status,
            'message': message,
            **kwargs
        }
        
        # Log to file
        if status == 'error':
            self.logger.error(f"{operation}: {message}")
        elif status == 'warning':
            self.logger.warning(f"{operation}: {message}")
        else:
            self.logger.info(f"{operation}: {message}")
            
        # Notify listeners
        for listener in self.listeners:
            try:
                listener(entry)
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
        with self._lock:
            self.entries.clear()
    
    def shutdown(self):
        """Shutdown the debug logger"""
        self.entry_queue.put(None)  # Signal queue processor to stop
        self.queue_thread.join(timeout=1.0)  # Wait for thread to finish
