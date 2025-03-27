import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.utils.adb_utils import ADBUtils

# Set up logging
os.makedirs('logs', exist_ok=True)
debug_log = os.path.join('logs', 'debug.log')
error_log = os.path.join('logs', 'errors.log')

logging.basicConfig(level=logging.DEBUG)

# Configure debug logger
debug_handler = logging.FileHandler(debug_log)
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
))

# Configure error logger
error_handler = logging.FileHandler(error_log)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    '%(asctime)s - ERROR - %(message)s\n'
))

# Add handlers
logger = logging.getLogger()
logger.addHandler(debug_handler)
logger.addHandler(error_handler)

def verify_environment() -> bool:
    """Verify required environment setup"""
    try:
        # Check ADB
        adb_utils = ADBUtils()
        if not adb_utils.adb_path:
            logging.error("ADB executable not found")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Environment verification failed: {str(e)}")
        return False

def main():
    """Main application entry point"""
    try:
        # Verify environment
        if not verify_environment():
            return 1
            
        # Create Qt application
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Enable high DPI support
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
