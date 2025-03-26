import enum
import logging
from datetime import datetime
import os
import traceback
from typing import Optional, Dict, Any, Union

class ErrorCode(enum.Enum):
    # ADB Connection Errors (1-99)
    ADB_SERVER_NOT_RUNNING = 1
    DEVICE_NOT_FOUND = 2
    DEVICE_UNAUTHORIZED = 3
    DEVICE_OFFLINE = 4
    ADB_COMMAND_FAILED = 5
    ADB_SERVER_START_FAILED = 6
    ADB_SERVER_KILL_FAILED = 7
    
    # App Management Errors (100-199)
    APP_LIST_FAILED = 100
    APP_DETAILS_FAILED = 101
    APP_NOT_FOUND = 102
    APP_PERMISSION_DENIED = 103
    PACKAGE_PARSE_ERROR = 104
    APP_MEMORY_INFO_FAILED = 105
    
    # Memory Analysis Errors (200-299)
    MEMORY_INFO_FAILED = 200
    MEMORY_DUMP_FAILED = 201
    HEAP_DUMP_FAILED = 202
    
    # Process Errors (300-399)
    PROCESS_NOT_FOUND = 300
    PROCESS_ACCESS_DENIED = 301
    PROCESS_DIED = 302
    
    # File System Errors (400-499)
    FILE_NOT_FOUND = 400
    FILE_ACCESS_DENIED = 401
    FILE_READ_ERROR = 402
    FILE_WRITE_ERROR = 403
    
    # System Errors (500-599)
    SYSTEM_COMMAND_FAILED = 500
    SYSTEM_RESOURCE_ERROR = 501
    TIMEOUT_ERROR = 502
    NETWORK_ERROR = 503

class ADBError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
        if self.traceback == "NoneType: None\n":
            self.traceback = None
        super().__init__(self.message)

class ErrorLogger:
    def __init__(self):
        """Initialize error logger"""
        self.logger = logging.getLogger('error')
        self.logger.setLevel(logging.ERROR)
        
        # Set up log directory
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Log file
        log_file = os.path.join(log_dir, f'adb_insight_{datetime.now().strftime("%Y%m%d")}.log')
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Format
        formatter = logging.Formatter('%(asctime)s [ERROR] %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
    def log_error(self, message: str, code: Union[ErrorCode, int] = None, **kwargs):
        """Log an error with optional error code"""
        try:
            # Format error details
            error_info = {
                'message': message,
                'code': code.value if isinstance(code, ErrorCode) else code,
                'code_name': code.name if isinstance(code, ErrorCode) else None,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            }
            
            # Log to file
            self.logger.error(f"Error {error_info['code'] or 500}: {message}")
            self.logger.error(f"Details: {error_info}")
            
            # Log stack trace for unexpected errors
            if not code:
                self.logger.error("Traceback:\n" + traceback.format_exc())
                
        except Exception as e:
            # Fallback error logging
            self.logger.error(f"Failed to log error: {str(e)}")
            self.logger.error(f"Original error: {message}")

    def log_warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log a warning message"""
        try:
            self.logger.warning(message, extra={'details': details or {}})
        except Exception as e:
            print(f"Failed to log warning: {str(e)}")
    
    def log_info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log an info message"""
        try:
            self.logger.info(message, extra={'details': details or {}})
        except Exception as e:
            print(f"Failed to log info: {str(e)}")
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors from the log file"""
        errors = []
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
            log_file = os.path.join(log_dir, f'adb_insight_{datetime.now().strftime("%Y%m%d")}.log')
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    
                current_error = []
                for line in reversed(lines):
                    if '[ERROR]' in line:
                        if len(errors) >= limit:
                            break
                        if current_error:
                            errors.append(''.join(reversed(current_error)))
                        current_error = [line.strip()]
                    elif current_error:
                        current_error.append(line.strip())
                
                if current_error and len(errors) < limit:
                    errors.append(''.join(reversed(current_error)))
            
        except Exception as e:
            print(f"Failed to get recent errors: {str(e)}")
        
        return errors
