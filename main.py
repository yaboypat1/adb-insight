import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable High DPI support before importing Qt
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from src.gui.main_window import MainWindow
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.utils.adb_utils import ADBUtils
import logging

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
    sys.exit(main())
