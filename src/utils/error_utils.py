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

class ErrorLogger:
    """Enhanced error logging utility"""
    
    def __init__(self, log_dir: str = None):
        """Initialize error logger"""
        # Set up log directory
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_dir = log_dir
        self.error_log = os.path.join(log_dir, 'errors.log')
        self.error_history: List[ErrorInfo] = []
        self.max_history = 1000
        
        # Configure logging
        self.logger = logging.getLogger('error_logger')
        self.logger.setLevel(logging.ERROR)
        
        # File handler
        file_handler = logging.FileHandler(self.error_log)
        file_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s\nContext: %(context)s\nStack: %(stacktrace)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(error_code)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def log_error(self, message: str, code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
                context: Optional[Dict] = None, stacktrace: Optional[str] = None) -> None:
        """Log an error with detailed information"""
        try:
            # Create error info
            error_info = ErrorInfo(
                code=code,
                message=message,
                timestamp=datetime.now(),
                context=context,
                stacktrace=stacktrace
            )
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
                
            # Log the error
            extra = {
                'error_code': code.name,
                'context': str(context) if context else 'None',
                'stacktrace': stacktrace if stacktrace else 'None'
            }
            
            self.logger.error(message, extra=extra)
            
        except Exception as e:
            # Fallback logging
            print(f"Error logging failed: {str(e)}")
            print(f"Original error: {message}")
            
    def get_recent_errors(self, count: int = 50, code: Optional[ErrorCode] = None) -> List[ErrorInfo]:
        """Get recent errors with optional filtering"""
        filtered = [e for e in self.error_history if not code or e.code == code]
        return list(reversed(filtered[-count:]))
        
    def get_error_stats(self) -> Dict[str, int]:
        """Get statistics about logged errors"""
        stats = {
            'total': len(self.error_history),
            'by_code': {},
            'by_type': {
                'adb': 0,
                'device': 0,
                'app': 0,
                'memory': 0,
                'analytics': 0,
                'system': 0,
                'unknown': 0
            }
        }
        
        for error in self.error_history:
            # Count by specific code
            code_name = error.code.name
            stats['by_code'][code_name] = stats['by_code'].get(code_name, 0) + 1
            
            # Count by error type
            if 'ADB_' in code_name:
                stats['by_type']['adb'] += 1
            elif 'DEVICE_' in code_name:
                stats['by_type']['device'] += 1
            elif 'APP_' in code_name:
                stats['by_type']['app'] += 1
            elif 'MEMORY_' in code_name:
                stats['by_type']['memory'] += 1
            elif 'ANALYTICS_' in code_name:
                stats['by_type']['analytics'] += 1
            elif 'SYSTEM_' in code_name:
                stats['by_type']['system'] += 1
            else:
                stats['by_type']['unknown'] += 1
                
        return stats
        
    def clear_error_history(self) -> None:
        """Clear error history and log file"""
        try:
            self.error_history.clear()
            with open(self.error_log, 'w') as f:
                f.write('')
        except Exception as e:
            print(f"Failed to clear error history: {str(e)}")
            
    def get_error_summary(self) -> str:
        """Get a human-readable summary of recent errors"""
        stats = self.get_error_stats()
        recent = self.get_recent_errors(5)
        
        summary = [
            "Error Summary:",
            f"Total Errors: {stats['total']}",
            "\nError Types:",
        ]
        
        for type_name, count in stats['by_type'].items():
            if count > 0:
                summary.append(f"- {type_name.title()}: {count}")
                
        if recent:
            summary.append("\nMost Recent Errors:")
            for error in recent:
                summary.append(f"- [{error.code.name}] {error.message}")
                
        return '\n'.join(summary)
