import sys
import os
<<<<<<< HEAD

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable High DPI support before importing Qt
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

=======
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
>>>>>>> parent of 5c1894b (all current bugs fixed)
from src.gui.main_window import MainWindow
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.utils.adb_utils import ADBUtils
import logging

<<<<<<< HEAD
# Set up logging directory
os.makedirs('logs', exist_ok=True)

=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
def verify_environment() -> bool:
    """Verify required environment setup"""
    debug_logger = DebugLogger()
    error_logger = ErrorLogger()
    
    try:
<<<<<<< HEAD
        adb = ADBUtils()
        if not adb.adb_path:
            logging.error("ADB executable not found")
            return False
=======
        # Check Python version
        if sys.version_info < (3, 7):
            error_logger.log_error(
                "Python 3.7 or higher is required",
                ErrorCode.SYSTEM_RESOURCE_ERROR,
                {'current_version': sys.version}
            )
            return False
            
        # Verify ADB installation
        adb_utils = ADBUtils(debug_logger, error_logger)
        try:
            adb_path = adb_utils._find_adb()
            debug_logger.log_debug(f"Found ADB at: {adb_path}", "system", "info")
        except FileNotFoundError as e:
            error_logger.log_error(
                str(e),
                ErrorCode.ADB_NOT_FOUND,
                {'paths_checked': os.environ.get('PATH', '')}
            )
            return False
            
        # Check ADB server
        success, output = adb_utils._run_adb(['start-server'])
        if not success:
            error_logger.log_error(
                "Failed to start ADB server",
                ErrorCode.ADB_SERVER_START_FAILED,
                {'output': output}
            )
            return False
            
        debug_logger.log_debug("Environment verification successful", "system", "info")
>>>>>>> parent of 5c1894b (all current bugs fixed)
        return True
    except Exception as e:
<<<<<<< HEAD
        logging.error(f"Environment verification failed: {str(e)}")
        return False

def main():
    """Main entry point"""
    # Create application
    app = QApplication(sys.argv)
    
    # Verify environment
    if not verify_environment():
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", "Failed to initialize ADB environment")
        return 1
    
    # Create utilities
    adb_utils = ADBUtils()
    debug_logger = DebugLogger()
    error_logger = ErrorLogger()
    
    # Create main window
    window = MainWindow(adb_utils, debug_logger, error_logger)
    window.show()
    
    # Run event loop
    return app.exec_()

if __name__ == "__main__":
=======
        error_logger.log_error(
            f"Environment verification failed: {str(e)}",
            ErrorCode.SYSTEM_RESOURCE_ERROR,
            {'error': str(e)}
        )
        return False

def main():
    """Main application entry point"""
    # Initialize logging
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
            error_logger.log_error(
                str(value),
                ErrorCode.UNKNOWN_ERROR,
                {'type': str(exctype), 'traceback': str(traceback)}
            )
            sys.__excepthook__(exctype, value, traceback)  # Call the default handler
            
        sys.excepthook = exception_hook
        
        # Start application
        debug_logger.log_debug("Application started", "system", "info")
        return app.exec()
        
    except Exception as e:
        error_logger.log_error(
            f"Application startup failed: {str(e)}",
            ErrorCode.SYSTEM_RESOURCE_ERROR,
            {'error': str(e)}
        )
        return 1

if __name__ == '__main__':
>>>>>>> parent of 5c1894b (all current bugs fixed)
    sys.exit(main())
