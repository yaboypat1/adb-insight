<<<<<<< HEAD
<<<<<<< HEAD
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
=======
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QHBoxLayout, QLineEdit, QLabel, QMessageBox,
    QDialog, QDialogButtonBox, QProgressBar, QProgressDialog,
    QInputDialog, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QProcess, QTimer
>>>>>>> parent of 5c1894b (all current bugs fixed)
from src.utils.adb_utils import ADBUtils
from src.utils.error_utils import ErrorLogger
from src.utils.debug_utils import DebugLogger
<<<<<<< HEAD
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
=======
from .app_tab import AppTab

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
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QHBoxLayout, QLineEdit, QLabel, QMessageBox,
    QDialog, QDialogButtonBox, QProgressBar, QProgressDialog,
    QInputDialog, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QProcess, QTimer
from src.utils.adb_utils import ADBUtils
from src.utils.error_utils import ErrorLogger
from src.utils.debug_utils import DebugLogger
from .app_tab import AppTab

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
>>>>>>> parent of 5c1894b (all current bugs fixed)
        self.setWindowTitle("ADB Insight")
        self.setMinimumSize(800, 600)
        self.setStyle(QApplication.style())
        
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
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
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
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
>>>>>>> parent of 5c1894b (all current bugs fixed)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
<<<<<<< HEAD
        
<<<<<<< HEAD
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
=======
=======
        
>>>>>>> parent of 5c1894b (all current bugs fixed)
        # Set up refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._check_device_status)
        self.refresh_timer.start(5000)  # Check every 5 seconds
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
        
        # Initial status check
        self.check_adb_status()
        
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
        # Create Devices tab
        devices_tab = QWidget()
        devices_layout = QVBoxLayout(devices_tab)
        
        # Add USB connection controls
        usb_group = QGroupBox("USB Connection")
        usb_layout = QHBoxLayout(usb_group)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        usb_layout.addWidget(refresh_btn)
        
        # Add restart ADB server button
        restart_btn = QPushButton("Restart ADB Server")
        restart_btn.clicked.connect(self.restart_adb_server)
        usb_layout.addWidget(restart_btn)
        
        devices_layout.addWidget(usb_group)
        
        # Add wireless connection controls
        wireless_group = QGroupBox("Wireless Connection")
        wireless_layout = QVBoxLayout(wireless_group)
        
        # Network scanning section
        scan_widget = QWidget()
        scan_layout = QHBoxLayout(scan_widget)
        scan_btn = QPushButton("Scan Network for Devices")
        scan_btn.clicked.connect(self.scan_network)
        scan_layout.addWidget(scan_btn)
        wireless_layout.addWidget(scan_widget)
        
        # Manual IP input section
        ip_widget = QWidget()
        ip_layout = QHBoxLayout(ip_widget)
        ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("5555")
        connect_btn = QPushButton("Connect Wireless")
        connect_btn.clicked.connect(self.connect_wireless)
        
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(port_label)
        ip_layout.addWidget(self.port_input)
        ip_layout.addWidget(connect_btn)
        
        # Pairing code section
        pair_widget = QWidget()
        pair_layout = QHBoxLayout(pair_widget)
        pair_btn = QPushButton("Pair Device with Code")
        pair_btn.clicked.connect(self.start_pairing)
        pair_layout.addWidget(pair_btn)
        
        wireless_layout.addWidget(ip_widget)
        wireless_layout.addWidget(pair_widget)
        devices_layout.addWidget(wireless_group)
        
        # Add text area for device list
        devices_group = QGroupBox("Connected Devices")
        devices_list_layout = QVBoxLayout(devices_group)
        
        self.devices_text = QTextEdit()
        self.devices_text.setReadOnly(True)
        devices_list_layout.addWidget(self.devices_text)
        
        devices_layout.addWidget(devices_group)
        
        self.tab_widget.addTab(devices_tab, "Devices")
        
        # Create Memory tab
        memory_tab = QWidget()
        memory_layout = QVBoxLayout(memory_tab)
        
        # Memory usage overview
        memory_overview = QGroupBox("Memory Overview")
        overview_layout = QVBoxLayout(memory_overview)
        
        # Add memory charts and graphs here
        overview_layout.addWidget(QLabel("Memory usage charts will be displayed here"))
        memory_layout.addWidget(memory_overview)
        
        # Memory leaks section
        leaks_group = QGroupBox("Memory Leaks")
        leaks_layout = QVBoxLayout(leaks_group)
        
        # Add leak detection controls and display here
        leaks_layout.addWidget(QLabel("Memory leak detection will be displayed here"))
        memory_layout.addWidget(leaks_group)
        
        self.tab_widget.addTab(memory_tab, "Memory")
        
        # Create Issues tab
        issues_tab = QWidget()
        issues_layout = QVBoxLayout(issues_tab)
        
        # Crashes section
        crashes_group = QGroupBox("Crashes")
        crashes_layout = QVBoxLayout(crashes_group)
        crashes_layout.addWidget(QLabel("App crash information will be displayed here"))
        issues_layout.addWidget(crashes_group)
        
        # ANRs section
        anrs_group = QGroupBox("Application Not Responding (ANRs)")
        anrs_layout = QVBoxLayout(anrs_group)
        anrs_layout.addWidget(QLabel("ANR information will be displayed here"))
        issues_layout.addWidget(anrs_group)
        
        self.tab_widget.addTab(issues_tab, "Issues")
        
        # Create Resources tab
        resources_tab = QWidget()
        resources_layout = QVBoxLayout(resources_tab)
        
        # CPU usage section
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout(cpu_group)
        cpu_layout.addWidget(QLabel("CPU usage information will be displayed here"))
        resources_layout.addWidget(cpu_group)
        
        # Battery usage section
        battery_group = QGroupBox("Battery Usage")
        battery_layout = QVBoxLayout(battery_group)
        battery_layout.addWidget(QLabel("Battery usage information will be displayed here"))
        resources_layout.addWidget(battery_group)
        
        # Network usage section
        network_group = QGroupBox("Network Usage")
        network_layout = QVBoxLayout(network_group)
        network_layout.addWidget(QLabel("Network usage information will be displayed here"))
        resources_layout.addWidget(network_group)
        
        self.tab_widget.addTab(resources_tab, "Resources")
        
    def _check_device_status(self):
        """Check device status and update UI"""
        try:
=======
        # Create Devices tab
        devices_tab = QWidget()
        devices_layout = QVBoxLayout(devices_tab)
        
        # Add USB connection controls
        usb_group = QGroupBox("USB Connection")
        usb_layout = QHBoxLayout(usb_group)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        usb_layout.addWidget(refresh_btn)
        
        # Add restart ADB server button
        restart_btn = QPushButton("Restart ADB Server")
        restart_btn.clicked.connect(self.restart_adb_server)
        usb_layout.addWidget(restart_btn)
        
        devices_layout.addWidget(usb_group)
        
        # Add wireless connection controls
        wireless_group = QGroupBox("Wireless Connection")
        wireless_layout = QVBoxLayout(wireless_group)
        
        # Network scanning section
        scan_widget = QWidget()
        scan_layout = QHBoxLayout(scan_widget)
        scan_btn = QPushButton("Scan Network for Devices")
        scan_btn.clicked.connect(self.scan_network)
        scan_layout.addWidget(scan_btn)
        wireless_layout.addWidget(scan_widget)
        
        # Manual IP input section
        ip_widget = QWidget()
        ip_layout = QHBoxLayout(ip_widget)
        ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("5555")
        connect_btn = QPushButton("Connect Wireless")
        connect_btn.clicked.connect(self.connect_wireless)
        
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(port_label)
        ip_layout.addWidget(self.port_input)
        ip_layout.addWidget(connect_btn)
        
        # Pairing code section
        pair_widget = QWidget()
        pair_layout = QHBoxLayout(pair_widget)
        pair_btn = QPushButton("Pair Device with Code")
        pair_btn.clicked.connect(self.start_pairing)
        pair_layout.addWidget(pair_btn)
        
        wireless_layout.addWidget(ip_widget)
        wireless_layout.addWidget(pair_widget)
        devices_layout.addWidget(wireless_group)
        
        # Add text area for device list
        devices_group = QGroupBox("Connected Devices")
        devices_list_layout = QVBoxLayout(devices_group)
        
        self.devices_text = QTextEdit()
        self.devices_text.setReadOnly(True)
        devices_list_layout.addWidget(self.devices_text)
        
        devices_layout.addWidget(devices_group)
        
        self.tab_widget.addTab(devices_tab, "Devices")
        
        # Create Memory tab
        memory_tab = QWidget()
        memory_layout = QVBoxLayout(memory_tab)
        
        # Memory usage overview
        memory_overview = QGroupBox("Memory Overview")
        overview_layout = QVBoxLayout(memory_overview)
        
        # Add memory charts and graphs here
        overview_layout.addWidget(QLabel("Memory usage charts will be displayed here"))
        memory_layout.addWidget(memory_overview)
        
        # Memory leaks section
        leaks_group = QGroupBox("Memory Leaks")
        leaks_layout = QVBoxLayout(leaks_group)
        
        # Add leak detection controls and display here
        leaks_layout.addWidget(QLabel("Memory leak detection will be displayed here"))
        memory_layout.addWidget(leaks_group)
        
        self.tab_widget.addTab(memory_tab, "Memory")
        
        # Create Issues tab
        issues_tab = QWidget()
        issues_layout = QVBoxLayout(issues_tab)
        
        # Crashes section
        crashes_group = QGroupBox("Crashes")
        crashes_layout = QVBoxLayout(crashes_group)
        crashes_layout.addWidget(QLabel("App crash information will be displayed here"))
        issues_layout.addWidget(crashes_group)
        
        # ANRs section
        anrs_group = QGroupBox("Application Not Responding (ANRs)")
        anrs_layout = QVBoxLayout(anrs_group)
        anrs_layout.addWidget(QLabel("ANR information will be displayed here"))
        issues_layout.addWidget(anrs_group)
        
        self.tab_widget.addTab(issues_tab, "Issues")
        
        # Create Resources tab
        resources_tab = QWidget()
        resources_layout = QVBoxLayout(resources_tab)
        
        # CPU usage section
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout(cpu_group)
        cpu_layout.addWidget(QLabel("CPU usage information will be displayed here"))
        resources_layout.addWidget(cpu_group)
        
        # Battery usage section
        battery_group = QGroupBox("Battery Usage")
        battery_layout = QVBoxLayout(battery_group)
        battery_layout.addWidget(QLabel("Battery usage information will be displayed here"))
        resources_layout.addWidget(battery_group)
        
        # Network usage section
        network_group = QGroupBox("Network Usage")
        network_layout = QVBoxLayout(network_group)
        network_layout.addWidget(QLabel("Network usage information will be displayed here"))
        resources_layout.addWidget(network_group)
        
        self.tab_widget.addTab(resources_tab, "Resources")
        
    def _check_device_status(self):
        """Check device status and update UI"""
        try:
>>>>>>> parent of 5c1894b (all current bugs fixed)
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
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
