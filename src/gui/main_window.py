from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox,
    QProgressBar, QLineEdit, QStatusBar, QFrame,
    QToolBar, QStyle, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QFont

from src.gui.app_tab import AppTab
from src.gui.wireless_dialog import WirelessDialog
from src.gui.wireless_handler_widget import WirelessHandlerWidget
from src.utils.adb_utils import ADBUtils
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger

import logging

class MainWindow(QMainWindow):
    """Main window of the ADB Insight application"""
    
    def __init__(self, adb_utils: ADBUtils, debug_logger: DebugLogger, error_logger: ErrorLogger, parent=None):
        super().__init__(parent)
        
        # Store utils
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Set up UI
        self.setWindowTitle("ADB Insight")
        self.setMinimumSize(800, 600)
        self.setStyle(QApplication.style())
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        refresh_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh")
        refresh_action.triggered.connect(self.refresh_all)
        
        toolbar.addSeparator()
        
        wireless_action = toolbar.addAction(self.style().standardIcon(QStyle.SP_ComputerIcon), "Wireless ADB")
        wireless_action.triggered.connect(self.show_wireless_dialog)
        
        # Create header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("ADB Insight")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add ADB status indicator
        self.adb_status = QLabel()
        self.adb_status.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        header_layout.addWidget(self.adb_status)
        
        layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.North)
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.wireless_tab = WirelessHandlerWidget(self.adb_utils, self.debug_logger, self.error_logger)
        self.tab_widget.addTab(self.wireless_tab, self.style().standardIcon(QStyle.SP_ComputerIcon), "Wireless ADB")
        
        self.app_tab = AppTab(self.adb_utils, self.debug_logger, self.error_logger)
        self.tab_widget.addTab(self.app_tab, self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Applications")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status widgets
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set up timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_adb_status)
        self.update_timer.start(5000)  # Check every 5 seconds
        
        # Initial status check
        self.check_adb_status()
        
    def check_adb_status(self):
        """Check ADB server status and update UI"""
        try:
            if self.adb_utils.is_server_running():
                self.adb_status.setText("ADB Server: Running")
                self.adb_status.setStyleSheet("color: green")
            else:
                self.adb_status.setText("ADB Server: Stopped")
                self.adb_status.setStyleSheet("color: red")
        except Exception as e:
            logging.error(f"Error checking ADB status: {str(e)}")
            self.adb_status.setText("ADB Server: Error")
            self.adb_status.setStyleSheet("color: red")
    
    def refresh_all(self):
        """Refresh all tabs"""
        try:
            self.status_label.setText("Refreshing...")
            self.progress_bar.setRange(0, 0)
            self.progress_bar.show()
            
            current_tab = self.tab_widget.currentWidget()
            if hasattr(current_tab, 'refresh_apps'):
                current_tab.refresh_apps()
            
            self.check_adb_status()
            self.status_label.setText("Refresh complete")
        except Exception as e:
            logging.error(f"Error refreshing: {str(e)}")
            self.status_label.setText("Error refreshing")
            QMessageBox.critical(self, "Error", f"Failed to refresh:\n{str(e)}")
        finally:
            self.progress_bar.hide()
            self.progress_bar.setRange(0, 100)
    
    def show_wireless_dialog(self):
        """Show wireless connection dialog"""
        dialog = WirelessDialog(self.adb_utils, self)
        dialog.exec_()
        
        # Refresh wireless tab after dialog closes
        if hasattr(self.wireless_tab, 'refresh_devices'):
            self.wireless_tab.refresh_devices()
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            # Clean up resources
            self.update_timer.stop()
            if hasattr(self.wireless_tab, 'cleanup'):
                self.wireless_tab.cleanup()
            if hasattr(self.app_tab, 'cleanup'):
                self.app_tab.cleanup()
            
            # Stop ADB server
            self.adb_utils.kill_server()
            
            event.accept()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            event.accept()  # Still close even if there's an error
