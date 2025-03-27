from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox,
    QProgressBar, QLineEdit, QStatusBar, QFrame,
    QToolBar, QStyle, QApplication, QGroupBox,
    QScrollArea, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

from src.gui.app_tab import AppTab
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
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle('ADB Insight')
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("ADB Insight")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_button.clicked.connect(self.refresh_all)
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create wireless handler widget
        self.wireless_widget = WirelessHandlerWidget(self.adb_utils, self.debug_logger, self.error_logger)
        self.tab_widget.addTab(self.wireless_widget, "Wireless ADB")
        
        # Create app manager tab
        self.app_tab = AppTab(self.adb_utils, self.debug_logger, self.error_logger)
        self.tab_widget.addTab(self.app_tab, "Applications")
        
        layout.addWidget(self.tab_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
        # Initial refresh
        self.refresh_all()
    
    def refresh_all(self):
        """Refresh all tabs and components"""
        try:
            self.debug_logger.log_debug("Starting device refresh...", category="device", level="info")
            
            # Get device list
            devices = self.adb_utils.get_devices()
            
            # Update status bar
            if not devices:
                self.status_bar.showMessage("No devices connected")
            else:
                self.status_bar.showMessage(f"Connected devices: {len(devices)}")
            
            # Refresh tabs
            self.wireless_widget.refresh_devices()
            self.app_tab.refresh_devices()
            
            self.debug_logger.log_debug("Device refresh complete", category="device", level="info")
            
        except Exception as e:
            self.error_logger.log_error(f"Error refreshing device list: {str(e)}", category="device")
            self.status_bar.showMessage("Error refreshing devices")
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Stop refresh timer
            self.refresh_timer.stop()
            
            # Clean up tabs
            self.wireless_widget.cleanup()
            self.app_tab.cleanup()
            
            # Accept close event
            event.accept()
            
        except Exception as e:
            self.error_logger.log_error(f"Error during cleanup: {str(e)}", category="system")
            event.accept()

class PairingDialog(QDialog):
    def __init__(self, address: str, pairing_code: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pair Device")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add pairing code display
        code_label = QLabel(f"Pairing Code: {pairing_code}")
        code_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(code_label)
        
        # Add address display
        addr_label = QLabel(f"Address: {address}")
        addr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(addr_label)
        
        # Add instructions
        instructions = QLabel(
            "1. On your Android device, go to Developer options\n"
            "2. Enable 'Wireless debugging'\n"
            "3. Tap 'Pair device with QR code' or 'Pair device with pairing code'\n"
            "4. Enter the pairing code shown above\n"
            "5. Click OK when done"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class NetworkScanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_logger = ErrorLogger()
        self.setWindowTitle("Scanning Network")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add status label
        self.status_label = QLabel("Scanning network for Android devices...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add progress bars for each interface
        self.progress_bars = {}
        
        # Add cancel button
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Start scanning
        self.devices = []
        QTimer.singleShot(100, self.start_scan)

class PairingDialog(QDialog):
    def __init__(self, address: str, pairing_code: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pair Device")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add pairing code display
        code_label = QLabel(f"Pairing Code: {pairing_code}")
        code_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(code_label)
        
        # Add address display
        addr_label = QLabel(f"Address: {address}")
        addr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(addr_label)
        
        # Add instructions
        instructions = QLabel(
            "1. On your Android device, go to Developer options\n"
            "2. Enable 'Wireless debugging'\n"
            "3. Tap 'Pair device with QR code' or 'Pair device with pairing code'\n"
            "4. Enter the pairing code shown above\n"
            "5. Click OK when done"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class NetworkScanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_logger = ErrorLogger()
        self.setWindowTitle("Scanning Network")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add status label
        self.status_label = QLabel("Scanning network for Android devices...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add progress bars for each interface
        self.progress_bars = {}
        
        # Add cancel button
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Start scanning
        self.devices = []
        QTimer.singleShot(100, self.start_scan)

class MainWindow(QMainWindow):
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        """Initialize main window"""
        super().__init__()
        self.setWindowTitle("ADB Insight")
        self.setMinimumSize(800, 600)
        self.setStyle(QApplication.style())
        
        # Initialize utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.adb_utils = ADBUtils(debug_logger, error_logger)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.app_tab = AppTab(debug_logger, error_logger)
        self.tab_widget.addTab(self.app_tab, "Apps")
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._check_device_status)
        self.refresh_timer.start(5000)  # Check every 5 seconds
        
    def _check_device_status(self):
        """Check device status and update UI"""
        try:
            devices = self.adb_utils.get_connected_devices()
            if devices:
                device, state, name = devices[0]
                if state == "device":
                    self.status_bar.showMessage(f"Connected to {name or device}")
                else:
                    self.status_bar.showMessage(f"Device {device} is {state}")
            else:
                self.status_bar.showMessage("No device connected")
                
        except Exception as e:
            self.error_logger.log_error(f"Error checking device status: {str(e)}")
            self.status_bar.showMessage("Error checking device status")
    
    def start_pairing(self):
        """Start the pairing process with code"""
        try:
            success, address, code = self.adb_utils.start_pairing()
            if success:
                dialog = PairingDialog(address, code, self)
                if dialog.exec() == QDialog.Accepted:
                    self.refresh_devices()
            else:
                QMessageBox.critical(self, "Error", f"Failed to start pairing: {code}")
        except Exception as e:
            self.error_logger.log_error(f"Failed to start pairing: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start pairing: {str(e)}")
    
    def scan_network(self):
        """Scan network for Android devices"""
        try:
            dialog = NetworkScanDialog(self)
            if dialog.exec() == QDialog.Accepted and dialog.devices:
                # Try to connect to found devices
                for device in dialog.devices:
                    success, msg = self.adb_utils.connect_wireless(device['ip'])
                    if success:
                        self.refresh_devices()
                        QMessageBox.information(self, "Success", f"Connected to {device['ip']}")
                    else:
                        QMessageBox.warning(self, "Warning", f"Failed to connect to {device['ip']}: {msg}")
        except Exception as e:
            self.error_logger.log_error(f"Failed to scan network: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to scan network: {str(e)}")
    
    def refresh_devices(self):
        """Refresh the list of connected devices"""
        try:
            devices = self.adb_utils.get_connected_devices()
            self.devices_text.clear()
            
            if not devices:
                self.devices_text.append("No devices connected")
                return
            
            for device_id, state, model in devices:
                device_info = f"Device: {device_id}\n"
                device_info += f"State: {state}\n"
                if model:
                    device_info += f"Model: {model}\n"
                device_info += "-" * 40 + "\n"
                self.devices_text.append(device_info)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to refresh devices: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to refresh devices: {str(e)}")
    
    def connect_wireless(self):
        """Connect to a device using IP address"""
        try:
            ip = self.ip_input.text().strip()
            port = self.port_input.text().strip()
            
            if not ip:
                QMessageBox.warning(self, "Warning", "Please enter an IP address")
                return
            
            if not port:
                port = "5555"
            
            success, msg = self.adb_utils.connect_wireless(ip, port)
            if success:
                self.refresh_devices()
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to connect: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to connect: {str(e)}")
    
    def restart_adb_server(self):
        """Restart the ADB server"""
        try:
            success, msg = self.adb_utils.restart_adb_server()
            if success:
                self.refresh_devices()
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Warning", msg)
        except Exception as e:
            self.error_logger.log_error(f"Failed to restart ADB server: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to restart ADB server: {str(e)}")
