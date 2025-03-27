import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger, ErrorCode, ADBError
from src.utils.adb_utils import ADBUtils
from src.utils.app_utils import AppUtils

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("adb_insight.log", mode='w'),
        logging.StreamHandler()
    ]
)

# Get the absolute path to the directory containing main.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to the Python path for absolute imports
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def verify_environment() -> bool:
    """Verify required environment setup"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            error_logger = ErrorLogger()
            error_logger.log_error(
                "Python 3.7 or higher is required",
                ErrorCode.SYSTEM_RESOURCE_ERROR,
                {'current_version': sys.version}
            )
            return False
            
        # Verify ADB installation
        adb_utils = ADBUtils(DebugLogger(), ErrorLogger())
        try:
            adb_path = adb_utils._find_adb()
            debug_logger = DebugLogger()
            debug_logger.log_debug(f"Found ADB at: {adb_path}", "system", "info")
        except FileNotFoundError as e:
            error_logger = ErrorLogger()
            error_logger.log_error(
                str(e),
                ErrorCode.ADB_NOT_FOUND,
                {'paths_checked': os.environ.get('PATH', '')}
            )
            return False
            
        # Check ADB server
        success, output = adb_utils._run_adb(['start-server'])
        if not success:
            error_logger = ErrorLogger()
            error_logger.log_error(
                "Failed to start ADB server",
                ErrorCode.ADB_SERVER_START_FAILED,
                {'output': output}
            )
            return False
            
        debug_logger = DebugLogger()
        debug_logger.log_debug("Environment verification successful", "system", "info")
        return True
        
    except Exception as e:
        error_logger = ErrorLogger()
        error_logger.log_error(
            f"Environment verification failed: {str(e)}",
            ErrorCode.SYSTEM_RESOURCE_ERROR,
            {'error': str(e)}
        )
        return False

def main():
    """Main application entry point"""
    # Initialize loggers
    debug_logger = DebugLogger()
    error_logger = ErrorLogger()
    
    try:
        # Verify environment
        if not verify_environment():
            print("Environment verification failed. Please check the logs for details.")
            sys.exit(1)
            
        # Create Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for better cross-platform appearance
        
        # Enable high DPI scaling
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
        # Create main window
        window = MainWindow(debug_logger, error_logger)
        window.show()
        
        # Set up exception hook for uncaught exceptions
        def exception_hook(exctype, value, traceback):
            error_logger = ErrorLogger()
            error_logger.log_error(
                str(value),
                ErrorCode.UNKNOWN_ERROR,
                {'type': str(exctype), 'traceback': str(traceback)}
            )
            sys.__excepthook__(exctype, value, traceback)  # Call the default handler
            
        sys.excepthook = exception_hook
        
        # Start application
        debug_logger = DebugLogger()
        debug_logger.log_debug("Application started", "system", "info")
        return app.exec_()
        
    except Exception as e:
        error_logger = ErrorLogger()
        error_logger.log_error(
            f"Application startup failed: {str(e)}",
            ErrorCode.SYSTEM_RESOURCE_ERROR,
            {'error': str(e)}
        )
        return 1

if __name__ == "__main__":
    # Initialize loggers
    debug_logger = DebugLogger()
    error_logger = ErrorLogger()
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow(debug_logger, error_logger)
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception(f"Fatal error in main: {e}")
        sys.exit(1)
