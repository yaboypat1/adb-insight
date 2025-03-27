import sys
import os
import logging

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable High DPI support before importing Qt
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from src.gui.main_window import MainWindow
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.utils.adb_utils import ADBUtils

# Set up logging directory
os.makedirs('logs', exist_ok=True)

def verify_environment() -> bool:
    """Verify required environment setup"""
    try:
        adb = ADBUtils()
        if not adb.adb_path:
            logging.error("ADB executable not found")
            return False
        return True
    except Exception as e:
        logging.error(f"Environment verification failed: {str(e)}")
        return False

def main():
    """Main entry point"""
    try:
        # Create application
        app = QApplication(sys.argv)
        
        # Verify environment
        if not verify_environment():
            QMessageBox.critical(None, "Error", "Failed to initialize ADB environment.\nPlease ensure ADB is installed and in your PATH.")
            return 1
        
        # Create utilities with error handling
        try:
            adb_utils = ADBUtils()
            debug_logger = DebugLogger()
            error_logger = ErrorLogger()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to initialize application utilities:\n{str(e)}")
            return 1
        
        # Create main window with error handling
        try:
            window = MainWindow(adb_utils, debug_logger, error_logger)
            window.show()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to create application window:\n{str(e)}")
            return 1
        
        # Run event loop
        return app.exec_()
        
    except Exception as e:
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start:\n{str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
