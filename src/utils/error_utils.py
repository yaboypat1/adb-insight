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
        # Set up logger
        self.logger = logging.getLogger('error')
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Set up log directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up error log file if no handlers exist
        if not self.logger.handlers:
            self.error_handler = logging.FileHandler(os.path.join(log_dir, 'errors.log'))
            self.error_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter('%(asctime)s - ERROR - %(message)s\n')
            self.error_handler.setFormatter(formatter)
            self.logger.addHandler(self.error_handler)
            self.logger.setLevel(logging.ERROR)
    
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
        
        # Log to file
        error_msg = f"{code.name}: {message}"
        if details:
            error_msg += f" | Details: {details}"
        if package_name:
            error_msg += f" | Package: {package_name}"
            
        self.logger.error(error_msg)

    def get_recent_errors(self, limit: int = 100) -> List[str]:
        """Get recent error messages"""
        try:
            with open(self.error_handler.baseFilename, 'r') as f:
                lines = f.readlines()
            return lines[-limit:] if limit else lines
        except Exception as e:
            print(f"Failed to read error log: {str(e)}")
            return []
    
    def clear_log(self):
        """Clear the error log file"""
        try:
            with open(self.error_handler.baseFilename, 'w'):
                pass
        except Exception as e:
            print(f"Failed to clear error log: {str(e)}")
    
    def get_error_count(self) -> int:
        """Get total number of errors logged"""
        try:
            with open(self.error_handler.baseFilename, 'r') as f:
                return sum(1 for line in f if line.strip())
        except Exception as e:
            print(f"Failed to count errors: {str(e)}")
            return 0
