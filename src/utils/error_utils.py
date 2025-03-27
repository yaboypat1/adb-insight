from enum import Enum, auto
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path

class ErrorCode(Enum):
    """Error codes for ADB operations"""
    UNKNOWN = auto()
    ADB_NOT_FOUND = auto()
    ADB_SERVER_NOT_RUNNING = auto()
    ADB_COMMAND_FAILED = auto()
    DEVICE_NOT_CONNECTED = auto()
    DEVICE_UNAUTHORIZED = auto()
    DEVICE_OFFLINE = auto()
    PACKAGE_NOT_FOUND = auto()
    PERMISSION_DENIED = auto()
    INVALID_ARGUMENT = auto()
    TIMEOUT = auto()
    NETWORK_ERROR = auto()
    PARSE_ERROR = auto()

@dataclass
class ErrorEntry:
    """Error entry data class"""
    timestamp: datetime
    code: ErrorCode
    message: str
    details: Optional[Dict] = None
    package_name: Optional[str] = None

class ADBError(Exception):
    """Custom exception for ADB operations"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN, details: Dict = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()

class ErrorLogger:
    """Error logging utility"""
    
    def __init__(self):
        """Initialize error logger"""
        # Set up log directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up error log file
        self.error_log_file = os.path.join(log_dir, 'error.log')
        self.error_handler = logging.FileHandler(self.error_log_file)
        self.error_handler.setLevel(logging.ERROR)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(filename)s:%(lineno)d - %(message)s'
        )
        self.error_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.error_handler)
        
        # Error entries
        self.errors: List[ErrorEntry] = []
        self.max_errors = 1000  # Keep last 1000 errors

    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN, 
                 details: Dict = None, package_name: str = None) -> None:
        """Log an error with optional details"""
        # Create error entry
        entry = ErrorEntry(
            timestamp=datetime.now(),
            code=code,
            message=message,
            details=details,
            package_name=package_name
        )
        
        # Add to errors list
        self.errors.append(entry)
        
        # Trim errors if needed
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log to file
        error_msg = f"{code.name}: {message}"
        if details:
            error_msg += f" | Details: {details}"
        if package_name:
            error_msg += f" | Package: {package_name}"
            
        self.logger.error(error_msg)

    def get_errors(self, limit: Optional[int] = None, 
                  code: Optional[ErrorCode] = None,
                  package_name: Optional[str] = None) -> List[ErrorEntry]:
        """Get error entries with optional filtering"""
        errors = self.errors
        
        if code:
            errors = [e for e in errors if e.code == code]
            
        if package_name:
            errors = [e for e in errors if e.package_name == package_name]
            
        if limit:
            errors = errors[-limit:]
            
        return errors

    def clear(self):
        """Clear all error entries"""
        self.errors.clear()
        
        # Also clear log file
        try:
            with open(self.error_log_file, 'w'):
                pass
        except Exception as e:
            self.logger.error(f"Failed to clear error log file: {str(e)}")

    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        stats = {code.name: 0 for code in ErrorCode}
        stats['total'] = len(self.errors)
        
        for error in self.errors:
            stats[error.code.name] += 1
            
        return stats

    def get_recent_errors(self, count: int = 50) -> List[str]:
        """Get recent error messages"""
        try:
            with open(self.error_log_file, 'r') as f:
                lines = f.readlines()
                
            return lines[-count:]
            
        except Exception as e:
            print(f"Failed to read error log: {str(e)}")
            return []
