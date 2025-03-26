import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.adb_utils import ADBUtils
from src.utils.error_utils import ErrorLogger

def check_environment():
    """Check if the environment is properly set up"""
    error_logger = ErrorLogger()
    
    try:
        # Check if ADB is installed and accessible
        success, msg = ADBUtils.check_adb_installed()
        if not success:
            error_logger.log_error(f"ADB is not properly installed: {msg}")
            return False, f"ADB is not properly installed: {msg}"
            
        # Check if ADB server is running
        success, msg = ADBUtils.start_adb_server()
        if not success:
            error_logger.log_error(f"Failed to start ADB server: {msg}")
            return False, f"Failed to start ADB server: {msg}"
            
        return True, "Environment check passed"
        
    except Exception as e:
        error_logger.log_error(f"Environment check failed: {str(e)}")
        return False, f"Environment check failed: {str(e)}"

def main():
    """Main entry point"""
    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Check environment
    success, msg = check_environment()
    if not success:
        QMessageBox.critical(None, "Error", msg)
        return 1
        
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        error_logger = ErrorLogger()
        error_logger.log_error(f"Application failed to start: {str(e)}")
        QMessageBox.critical(None, "Error", f"Application failed to start: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
