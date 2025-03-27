import enum
import logging
import os
from enum import Enum, auto
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

class ErrorCode(Enum):
    """Detailed error codes for better tracking"""
    # ADB Related
    ADB_NOT_FOUND = auto()
    ADB_SERVER_NOT_RUNNING = auto()
    ADB_SERVER_START_FAILED = auto()
    ADB_DEVICE_NOT_FOUND = auto()
    ADB_DEVICE_UNAUTHORIZED = auto()
    ADB_DEVICE_OFFLINE = auto()
    ADB_COMMAND_FAILED = auto()
    ADB_TIMEOUT = auto()
    ADB_CONNECTION_FAILED = auto()
    
    # Device Related
    DEVICE_NOT_CONNECTED = auto()
    DEVICE_MULTIPLE_CONNECTED = auto()
    DEVICE_PERMISSION_DENIED = auto()
    DEVICE_IO_ERROR = auto()
    
    # App Related
    APP_NOT_FOUND = auto()
    APP_INSTALL_FAILED = auto()
    APP_UNINSTALL_FAILED = auto()
    APP_LAUNCH_FAILED = auto()
    APP_STOP_FAILED = auto()
    APP_CLEAR_DATA_FAILED = auto()
    
    # Memory Related
    MEMORY_READ_FAILED = auto()
    MEMORY_PARSE_FAILED = auto()
    MEMORY_DUMP_FAILED = auto()
    
    # Analytics Related
    ANALYTICS_CPU_FAILED = auto()
    ANALYTICS_BATTERY_FAILED = auto()
    ANALYTICS_NETWORK_FAILED = auto()
    ANALYTICS_DISK_FAILED = auto()
    
    # System Related
    SYSTEM_IO_ERROR = auto()
    SYSTEM_PERMISSION_ERROR = auto()
    SYSTEM_RESOURCE_ERROR = auto()
    
    # Unknown
    UNKNOWN_ERROR = auto()

@dataclass
class ErrorInfo:
    """Detailed error information"""
    code: ErrorCode
    message: str
    timestamp: datetime
    context: Optional[Dict] = None
    stacktrace: Optional[str] = None

class ADBError(Exception):
    """Base exception for ADB-related errors"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, context: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.now()

class DeviceError(ADBError):
    """Exception for device-related errors"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.DEVICE_NOT_CONNECTED, context: Optional[Dict] = None):
        super().__init__(message, code, context)

class AppError(ADBError):
    """Exception for app-related errors"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.APP_NOT_FOUND, context: Optional[Dict] = None):
        super().__init__(message, code, context)

class MemoryError(ADBError):
    """Exception for memory-related errors"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.MEMORY_READ_FAILED, context: Optional[Dict] = None):
        super().__init__(message, code, context)

class AnalyticsError(ADBError):
    """Exception for analytics-related errors"""
    def __init__(self, message: str, code: ErrorCode = ErrorCode.ANALYTICS_CPU_FAILED, context: Optional[Dict] = None):
        super().__init__(message, code, context)

def get_error_message(code: ErrorCode) -> str:
    """Get error message for a specific error code"""
    error_messages = {
        ErrorCode.ADB_NOT_FOUND: "ADB not found",
        ErrorCode.ADB_SERVER_NOT_RUNNING: "ADB server not running",
        ErrorCode.ADB_SERVER_START_FAILED: "Failed to start ADB server",
        ErrorCode.ADB_DEVICE_NOT_FOUND: "ADB device not found",
        ErrorCode.ADB_DEVICE_UNAUTHORIZED: "ADB device unauthorized",
        ErrorCode.ADB_DEVICE_OFFLINE: "ADB device offline",
        ErrorCode.ADB_COMMAND_FAILED: "ADB command failed",
        ErrorCode.ADB_TIMEOUT: "ADB timeout",
        ErrorCode.ADB_CONNECTION_FAILED: "ADB connection failed",
        
        ErrorCode.DEVICE_NOT_CONNECTED: "Device not connected",
        ErrorCode.DEVICE_MULTIPLE_CONNECTED: "Multiple devices connected",
        ErrorCode.DEVICE_PERMISSION_DENIED: "Device permission denied",
        ErrorCode.DEVICE_IO_ERROR: "Device I/O error",
        
        ErrorCode.APP_NOT_FOUND: "App not found",
        ErrorCode.APP_INSTALL_FAILED: "App installation failed",
        ErrorCode.APP_UNINSTALL_FAILED: "App uninstallation failed",
        ErrorCode.APP_LAUNCH_FAILED: "App launch failed",
        ErrorCode.APP_STOP_FAILED: "App stop failed",
        ErrorCode.APP_CLEAR_DATA_FAILED: "App clear data failed",
        
        ErrorCode.MEMORY_READ_FAILED: "Memory read failed",
        ErrorCode.MEMORY_PARSE_FAILED: "Memory parse failed",
        ErrorCode.MEMORY_DUMP_FAILED: "Memory dump failed",
        
        ErrorCode.ANALYTICS_CPU_FAILED: "Analytics CPU failed",
        ErrorCode.ANALYTICS_BATTERY_FAILED: "Analytics battery failed",
        ErrorCode.ANALYTICS_NETWORK_FAILED: "Analytics network failed",
        ErrorCode.ANALYTICS_DISK_FAILED: "Analytics disk failed",
        
        ErrorCode.SYSTEM_IO_ERROR: "System I/O error",
        ErrorCode.SYSTEM_PERMISSION_ERROR: "System permission error",
        ErrorCode.SYSTEM_RESOURCE_ERROR: "System resource error",
        
        ErrorCode.UNKNOWN_ERROR: "Unknown error"
    }
    return error_messages.get(code, "Unknown error")

class ErrorLogger:
    """Enhanced error logging utility"""
    
    def __init__(self, log_dir: str = None):
        """Initialize error logger"""
        # Set up logger
        self.logger = logging.getLogger('error')
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Set up log directory
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
        # Set up error log file
        self.error_log_file = os.path.join(log_dir, 'error.log')
        self.error_handler = logging.FileHandler(self.error_log_file)
        self.error_handler.setLevel(logging.ERROR)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s'
        )
        self.error_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.error_handler)
        
        # Error history
        self.error_history: List[ErrorInfo] = []
        self.max_history = 1000  # Keep last 1000 errors
        
    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, context: Dict = None) -> None:
        """Log an error with enhanced context"""
        try:
            # Create error info
            error_info = ErrorInfo(
                code=code,
                message=message,
                timestamp=datetime.now(),
                context=context or {},
                stacktrace=None  # Will be filled if exception context exists
            )
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
                
            # Get error code name and message
            error_name = code.name if isinstance(code, ErrorCode) else 'UNKNOWN_ERROR'
            error_message = get_error_message(code) if isinstance(code, ErrorCode) else message
            
            # Log with extra context
            extra = {
                'error_code': error_name,
                'context': context or {}
            }
            
            self.logger.error(
                f"{message} - {error_message}",
                extra=extra,
                exc_info=True  # Include stack trace if available
            )
            
        except Exception as e:
=======
        # Set up error log file
        self.error_log_file = os.path.join(log_dir, 'error.log')
        self.error_handler = logging.FileHandler(self.error_log_file)
        self.error_handler.setLevel(logging.ERROR)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s'
        )
        self.error_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.error_handler)
        
        # Error history
        self.error_history: List[ErrorInfo] = []
        self.max_history = 1000  # Keep last 1000 errors
        
    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, context: Dict = None) -> None:
        """Log an error with enhanced context"""
        try:
            # Create error info
            error_info = ErrorInfo(
                code=code,
                message=message,
                timestamp=datetime.now(),
                context=context or {},
                stacktrace=None  # Will be filled if exception context exists
            )
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
                
            # Get error code name and message
            error_name = code.name if isinstance(code, ErrorCode) else 'UNKNOWN_ERROR'
            error_message = get_error_message(code) if isinstance(code, ErrorCode) else message
            
            # Log with extra context
            extra = {
                'error_code': error_name,
                'context': context or {}
            }
            
            self.logger.error(
                f"{message} - {error_message}",
                extra=extra,
                exc_info=True  # Include stack trace if available
            )
            
        except Exception as e:
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
        # Set up error log file
        self.error_log_file = os.path.join(log_dir, 'error.log')
        self.error_handler = logging.FileHandler(self.error_log_file)
        self.error_handler.setLevel(logging.ERROR)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s'
        )
        self.error_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.error_handler)
        
        # Error history
        self.error_history: List[ErrorInfo] = []
        self.max_history = 1000  # Keep last 1000 errors
        
    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, context: Dict = None) -> None:
        """Log an error with enhanced context"""
        try:
            # Create error info
            error_info = ErrorInfo(
                code=code,
                message=message,
                timestamp=datetime.now(),
                context=context or {},
                stacktrace=None  # Will be filled if exception context exists
            )
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
                
            # Get error code name and message
            error_name = code.name if isinstance(code, ErrorCode) else 'UNKNOWN_ERROR'
            error_message = get_error_message(code) if isinstance(code, ErrorCode) else message
            
            # Log with extra context
            extra = {
                'error_code': error_name,
                'context': context or {}
            }
            
            self.logger.error(
                f"{message} - {error_message}",
                extra=extra,
                exc_info=True  # Include stack trace if available
            )
            
        except Exception as e:
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
        # Set up error log file
        self.error_log_file = os.path.join(log_dir, 'error.log')
        self.error_handler = logging.FileHandler(self.error_log_file)
        self.error_handler.setLevel(logging.ERROR)
        
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s'
        )
        self.error_handler.setFormatter(formatter)
        
        # Configure logger
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(self.error_handler)
        
        # Error history
        self.error_history: List[ErrorInfo] = []
        self.max_history = 1000  # Keep last 1000 errors
        
    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR, context: Dict = None) -> None:
        """Log an error with enhanced context"""
        try:
            # Create error info
            error_info = ErrorInfo(
                code=code,
                message=message,
                timestamp=datetime.now(),
                context=context or {},
                stacktrace=None  # Will be filled if exception context exists
            )
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
                
            # Get error code name and message
            error_name = code.name if isinstance(code, ErrorCode) else 'UNKNOWN_ERROR'
            error_message = get_error_message(code) if isinstance(code, ErrorCode) else message
            
            # Log with extra context
            extra = {
                'error_code': error_name,
                'context': context or {}
            }
            
            self.logger.error(
                f"{message} - {error_message}",
                extra=extra,
                exc_info=True  # Include stack trace if available
            )
            
        except Exception as e:
>>>>>>> parent of 5c1894b (all current bugs fixed)
            # Fallback logging if something goes wrong
            print(f"Error in error logger: {str(e)}")
            print(f"Original error: {message}")
            
    def get_recent_errors(self, limit: int = 10) -> List[ErrorInfo]:
        """Get recent errors from history"""
        return self.error_history[-limit:]
        
    def get_errors_by_code(self, code: ErrorCode) -> List[ErrorInfo]:
        """Get all errors of a specific type"""
        return [e for e in self.error_history if e.code == code]
        
    def get_error_summary(self) -> Dict[ErrorCode, int]:
        """Get summary of error occurrences by type"""
        summary = {}
        for error in self.error_history:
            if error.code in summary:
                summary[error.code] += 1
            else:
                summary[error.code] = 1
        return summary
        
    def clear_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
