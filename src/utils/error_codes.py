"""Error codes for ADB Insight application."""

from enum import Enum, auto

class ErrorCode(Enum):
    """Enumeration of error codes used throughout the application."""
    
    # ADB Related Errors
    ADB_NOT_FOUND = auto()
    ADB_SERVER_NOT_RUNNING = auto()
    ADB_COMMAND_FAILED = auto()
    ADB_SHELL_ERROR = auto()
    
    # Device Related Errors
    DEVICE_NOT_CONNECTED = auto()
    DEVICE_NOT_AUTHORIZED = auto()
    DEVICE_STATE_MISMATCH = auto()
    MULTIPLE_DEVICES = auto()
    
    # App Related Errors
    APP_NOT_FOUND = auto()
    APP_LIST_REFRESH_FAILED = auto()
    APP_INSTALL_FAILED = auto()
    APP_UNINSTALL_FAILED = auto()
    
    # Command Related Errors
    COMMAND_TIMEOUT = auto()
    COMMAND_PARSE_ERROR = auto()
    COMMAND_EXECUTION_ERROR = auto()
    PIPE_ERROR = auto()
    
    # Permission Related Errors
    PERMISSION_DENIED = auto()
    INSUFFICIENT_PRIVILEGES = auto()
    
    # System Related Errors
    SYSTEM_COMMAND_FAILED = auto()
    SYSTEM_RESOURCE_ERROR = auto()
    
    # UI Related Errors
    UI_UPDATE_FAILED = auto()
    UI_COMPONENT_ERROR = auto()
    
    # Cache Related Errors
    CACHE_ERROR = auto()
    CACHE_INVALID = auto()
    
    # General Errors
    UNKNOWN_ERROR = auto()
    INVALID_ARGUMENT = auto()
    NOT_IMPLEMENTED = auto()

def get_error_message(code: ErrorCode) -> str:
    """Get a human-readable error message for an error code."""
    messages = {
        ErrorCode.ADB_NOT_FOUND: "ADB executable not found. Please ensure Android SDK platform-tools are installed and in your PATH.",
        ErrorCode.ADB_SERVER_NOT_RUNNING: "ADB server is not running. Please check your Android SDK installation.",
        ErrorCode.ADB_COMMAND_FAILED: "ADB command failed to execute. Please check device connection and try again.",
        ErrorCode.ADB_SHELL_ERROR: "Error executing ADB shell command. Check device connection and permissions.",
        
        ErrorCode.DEVICE_NOT_CONNECTED: "No Android device connected. Please connect a device and enable USB debugging.",
        ErrorCode.DEVICE_NOT_AUTHORIZED: "Device not authorized for debugging. Please accept the debugging prompt on your device.",
        ErrorCode.DEVICE_STATE_MISMATCH: "Device state is inconsistent. Try disconnecting and reconnecting the device.",
        ErrorCode.MULTIPLE_DEVICES: "Multiple devices connected. Please disconnect extra devices or specify a target device.",
        
        ErrorCode.APP_NOT_FOUND: "Application not found on device. Please check the package name.",
        ErrorCode.APP_LIST_REFRESH_FAILED: "Failed to refresh application list. Check device connection.",
        ErrorCode.APP_INSTALL_FAILED: "Failed to install application. Check APK file and device storage.",
        ErrorCode.APP_UNINSTALL_FAILED: "Failed to uninstall application. Check package name and permissions.",
        
        ErrorCode.COMMAND_TIMEOUT: "Command execution timed out. Check device connection and try again.",
        ErrorCode.COMMAND_PARSE_ERROR: "Failed to parse command output. Please report this issue.",
        ErrorCode.COMMAND_EXECUTION_ERROR: "Error executing command. Check permissions and try again.",
        ErrorCode.PIPE_ERROR: "Pipe error during command execution. Check device connection.",
        
        ErrorCode.PERMISSION_DENIED: "Permission denied. Check ADB and device permissions.",
        ErrorCode.INSUFFICIENT_PRIVILEGES: "Insufficient privileges to perform operation.",
        
        ErrorCode.SYSTEM_COMMAND_FAILED: "System command failed. Check system configuration.",
        ErrorCode.SYSTEM_RESOURCE_ERROR: "System resource error. Check available memory and storage.",
        
        ErrorCode.UI_UPDATE_FAILED: "Failed to update user interface. Please restart the application.",
        ErrorCode.UI_COMPONENT_ERROR: "Error in UI component. Please report this issue.",
        
        ErrorCode.CACHE_ERROR: "Cache operation failed. Try clearing application cache.",
        ErrorCode.CACHE_INVALID: "Cache data is invalid. Refreshing data from device.",
        
        ErrorCode.UNKNOWN_ERROR: "An unknown error occurred. Please check logs for details.",
        ErrorCode.INVALID_ARGUMENT: "Invalid argument provided to operation.",
        ErrorCode.NOT_IMPLEMENTED: "This feature is not yet implemented."
    }
    return messages.get(code, f"Unknown error code: {code}")
