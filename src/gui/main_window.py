from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox,
    QProgressBar, QLineEdit, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon

from .app_tab import AppTab
from .wireless_dialog import WirelessDialog
from ..utils.adb_utils import ADBUtils
from ..utils.debug_utils import DebugLogger
from ..utils.error_utils import ErrorLogger

import logging

class MainWindow(QMainWindow):
    """Main window of the ADB Insight application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize utils
        self.adb_utils = ADBUtils()
        self.debug_logger = DebugLogger()
        self.error_logger = ErrorLogger()
        
        # Set up UI
        self.setWindowTitle("ADB Insight")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._check_device_status)
        controls_layout.addWidget(self.refresh_button)
        
        self.wireless_button = QPushButton("Wireless ADB")
        self.wireless_button.clicked.connect(self.show_wireless_dialog)
        controls_layout.addWidget(self.wireless_button)
        
        controls_layout.addStretch()
        
        # Create device section
        self.create_device_section()
        controls_layout.addLayout(self.layout_device_section)
        
        self.layout.addLayout(controls_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create app tab
        self.app_tab = AppTab(self.adb_utils)
        self.tab_widget.addTab(self.app_tab, "Apps")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._check_device_status)
        self.refresh_timer.start(2000)  # Check every 2 seconds
        
        # Initial device check
        self._check_device_status()
        
    def create_device_section(self):
        """Create the device management section"""
        self.layout_device_section = QHBoxLayout()
        
        # Device status
        self.devices_label = QLabel("Devices:")
        self.layout_device_section.addWidget(self.devices_label)
        
        self.devices_text = QLabel("No devices connected")
        self.layout_device_section.addWidget(self.devices_text)
        
        self.layout_device_section.addStretch()
        
        # Wireless connection
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter device IP")
        self.ip_input.setMaximumWidth(150)
        self.layout_device_section.addWidget(self.ip_input)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_wireless)
        self.layout_device_section.addWidget(self.connect_button)
        
    def _check_device_status(self):
        """Check ADB device status"""
        try:
            devices = self.adb_utils.get_devices()
            if devices:
                device_text = ", ".join(devices)
                self.devices_text.setText(device_text)
                self.app_tab.refresh_apps()
            else:
                self.devices_text.setText("No devices connected")
                
        except Exception as e:
            logging.error(f"Error checking device status: {str(e)}")
            self.devices_text.setText("Error checking devices")
            
    def _connect_wireless(self):
        """Connect to wireless device"""
        ip = self.ip_input.text().strip()
        if not ip:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Please enter a device IP address")
            return
            
        try:
            if self.adb_utils.connect_wireless_device(ip):
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Connected to {ip}")
                self._check_device_status()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", f"Failed to connect to {ip}")
                
        except Exception as e:
            logging.error(f"Error connecting to wireless device: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Connection error: {str(e)}")
            
    def show_wireless_dialog(self):
        """Show the wireless ADB connection dialog"""
        dialog = WirelessDialog(self.adb_utils, self)
        dialog.exec_()
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop refresh timer
        self.refresh_timer.stop()
        
        # Clean up tabs
        self.app_tab.cleanup()
        
        # Accept close event
        event.accept()
