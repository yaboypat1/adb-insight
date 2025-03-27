import sys
import os
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStatusBar, QTabWidget,
    QLineEdit, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon

from src.utils.adb_utils import ADBUtils
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger, ErrorCode, ADBError
from src.gui.app_tab import AppTab

class MainWindow(QMainWindow):
    """Main window of the ADB Insight application"""
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        super().__init__()
        
        # Initialize loggers
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Initialize ADB utils
        self.adb_utils = ADBUtils(debug_logger, error_logger)
        
        # Set up UI
        self.setWindowTitle("ADB Insight")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create device section
        self.create_device_section()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.app_tab = AppTab(self.adb_utils, self.debug_logger, self.error_logger)
        self.tab_widget.addTab(self.app_tab, "Applications")
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Set up device check timer
        self.device_check_timer = QTimer()
        self.device_check_timer.timeout.connect(self._check_device_status)
        self.device_check_timer.start(2000)  # Check every 2 seconds
        
        # Initial device check
        self._check_device_status()
        
        # Connect signals
        self.adb_utils.device_state_changed.connect(self._handle_device_state_changed)

    def create_device_section(self):
        """Create the device management section"""
        device_layout = QHBoxLayout()
        
        # Device status
        self.devices_label = QLabel("Devices:")
        device_layout.addWidget(self.devices_label)
        
        self.devices_text = QLabel("No devices connected")
        device_layout.addWidget(self.devices_text)
        
        device_layout.addStretch()
        
        # Wireless connection
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP:PORT")
        self.ip_input.setMaximumWidth(150)
        device_layout.addWidget(self.ip_input)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect_wireless)
        device_layout.addWidget(self.connect_button)
        
        # Add to main layout
        self.layout.addLayout(device_layout)

    @pyqtSlot()
    def _check_device_status(self):
        """Check connected devices and update UI"""
        try:
            devices = self.adb_utils.get_devices()
            
            if not devices:
                self.devices_text.setText("No devices connected")
                self.status_bar.showMessage("No device connected")
                self.adb_utils.device_state_changed.emit(False)
                return
                
            # Format device list text
            device_texts = []
            has_ready_device = False
            
            for device in devices:
                if device['state'] == "device":
                    has_ready_device = True
                    device_texts.append(f"{device['id']} ({device['model']})")
                else:
                    device_texts.append(f"{device['id']} ({device['state']})")
                    
            self.devices_text.setText(", ".join(device_texts))
            
            # Update status bar and emit signal
            if has_ready_device:
                if len(devices) == 1:
                    self.status_bar.showMessage("Device connected")
                else:
                    self.status_bar.showMessage(f"{len(devices)} devices connected")
                self.adb_utils.device_state_changed.emit(True)
            else:
                self.status_bar.showMessage("No ready device")
                self.adb_utils.device_state_changed.emit(False)
                
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to check device status: {str(e)}",
                ErrorCode.DEVICE_NOT_CONNECTED
            )
            self.status_bar.showMessage("Error checking device status")
            self.adb_utils.device_state_changed.emit(False)

    @pyqtSlot(bool)
    def _handle_device_state_changed(self, connected: bool):
        """Handle device connection state changes"""
        # Update UI elements based on connection state
        self.connect_button.setEnabled(not connected)
        self.ip_input.setEnabled(not connected)
        
        # Notify tabs of device state change
        self.app_tab.handle_device_state_changed(connected)

    def _connect_wireless(self):
        """Connect to device wirelessly"""
        address = self.ip_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Error", "Please enter device address (IP:PORT)")
            return
            
        try:
            # Try to connect
            if self.adb_utils.connect_wireless(address):
                self.status_bar.showMessage(f"Successfully connected to {address}")
                self.ip_input.clear()
            else:
                QMessageBox.warning(self, "Error", f"Failed to connect to {address}")
                
        except ADBError as e:
            self.error_logger.log_error(
                f"Failed to connect to {address}: {str(e)}",
                e.code,
                {"address": address}
            )
            QMessageBox.warning(self, "Error", str(e))
            
        except Exception as e:
            self.error_logger.log_error(
                f"Unexpected error connecting to {address}: {str(e)}",
                ErrorCode.UNKNOWN,
                {"address": address}
            )
            QMessageBox.warning(self, "Error", f"Unexpected error: {str(e)}")

    def show_progress(self, show: bool = True):
        """Show or hide the progress bar"""
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def set_progress(self, value: int, maximum: int = 100):
        """Set progress bar value"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop device check timer
        self.device_check_timer.stop()
        
        # Clean up tabs
        self.app_tab.cleanup()
        
        # Accept close event
        event.accept()
