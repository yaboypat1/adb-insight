import sys
import os
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QMessageBox, QLineEdit,
    QGroupBox, QSplitter, QFrame, QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.adb_utils import ADBUtils
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.workers import create_thread_worker, cleanup_thread

import logging

class WirelessHandlerWidget(QWidget):
    def __init__(self, adb_utility_module: ADBUtils, main_debug_logger: DebugLogger, main_error_logger: ErrorLogger, parent=None):
        super().__init__(parent)
        self.adb_utils = adb_utility_module
        self.debug_logger = main_debug_logger
        self.error_logger = main_error_logger
        self.active_threads = []  # Store active threads
        self._setup_ui()
        self.start_device_refresh()

    def _setup_ui(self):
        """Setup the UI components with improved layout and styling."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create header with title and refresh button
        header_layout = QHBoxLayout()
        title_label = QLabel("Wireless ADB Manager")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        self.refreshButton = QPushButton("Refresh Devices")
        self.refreshButton.setIcon(QIcon.fromTheme("view-refresh"))
        self.refreshButton.clicked.connect(self.start_device_refresh)
        header_layout.addWidget(self.refreshButton)
        main_layout.addLayout(header_layout)

        # Create device list group
        device_group = QGroupBox("Connected Devices")
        device_layout = QVBoxLayout(device_group)
        
        self.deviceListWidget = QListWidget()
        self.deviceListWidget.setMinimumHeight(150)
        device_layout.addWidget(self.deviceListWidget)
        
        # TCP/IP mode controls
        tcpip_layout = QHBoxLayout()
        self.tcpipButton = QPushButton("Enable TCP/IP Mode")
        self.tcpipButton.clicked.connect(self.on_enable_tcpip_clicked)
        tcpip_layout.addWidget(self.tcpipButton)
        
        port_label = QLabel("Port:")
        port_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tcpip_layout.addWidget(port_label)
        
        self.portInput = QLineEdit()
        self.portInput.setPlaceholderText("5555")
        self.portInput.setMaximumWidth(80)
        self.portInput.setAlignment(Qt.AlignCenter)
        tcpip_layout.addWidget(self.portInput)
        
        device_layout.addLayout(tcpip_layout)
        main_layout.addWidget(device_group)

        # Create connection controls group
        connect_group = QGroupBox("Wireless Connection")
        connect_layout = QVBoxLayout(connect_group)
        
        # IP input with validation
        ip_layout = QHBoxLayout()
        ip_label = QLabel("Device IP:")
        ip_layout.addWidget(ip_label)
        
        self.ipInput = QLineEdit()
        self.ipInput.setPlaceholderText("192.168.1.x")
        ip_layout.addWidget(self.ipInput)
        
        port_label = QLabel("Port:")
        ip_layout.addWidget(port_label)
        
        self.connectPortInput = QLineEdit()
        self.connectPortInput.setPlaceholderText("5555")
        self.connectPortInput.setMaximumWidth(80)
        self.connectPortInput.setAlignment(Qt.AlignCenter)
        ip_layout.addWidget(self.connectPortInput)
        
        connect_layout.addLayout(ip_layout)

        # Connect/Disconnect buttons
        button_layout = QHBoxLayout()
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.on_connect_clicked)
        button_layout.addWidget(self.connectButton)
        
        self.disconnectButton = QPushButton("Disconnect")
        self.disconnectButton.clicked.connect(self.on_disconnect_clicked)
        button_layout.addWidget(self.disconnectButton)
        
        connect_layout.addLayout(button_layout)
        main_layout.addWidget(connect_group)

        # Status bar
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.statusLabel = QLabel("Status: Ready")
        status_layout.addWidget(self.statusLabel)
        main_layout.addWidget(status_frame)

        # Add stretch to push everything up
        main_layout.addStretch()

    def _start_worker(self, target, callback, *args):
        """Start a worker thread for background operations."""
        thread, worker = create_thread_worker(target, *args)
        worker.finished.connect(callback)
        worker.error.connect(self.handle_worker_error)
        worker.result.connect(self.handle_worker_result)
        thread.start()
        
        # Store thread and worker references
        self.active_threads.append((thread, worker))
        
        # Clean up thread and worker when finished
        worker.finished.connect(lambda: self._cleanup_thread(thread, worker))
        
        return thread, worker

    def _cleanup_thread(self, thread, worker):
        """Clean up a thread and worker and remove from active threads."""
        cleanup_thread(thread, worker)
        if (thread, worker) in self.active_threads:
            self.active_threads.remove((thread, worker))

    def start_device_refresh(self):
        """Starts worker to refresh the device list."""
        self.debug_logger.log_debug("Starting device refresh...", category="device", level="info")
        self.statusLabel.setText("Status: Refreshing devices...")
        self.refreshButton.setEnabled(False)
        self._start_worker(self.adb_utils.get_devices, self.handle_device_refresh_complete)

    def on_enable_tcpip_clicked(self):
        """Starts worker to enable TCP/IP on the selected USB device."""
        selected_items = self.deviceListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a device first")
            return

        device_id = selected_items[0].text().split('\t')[0]
        port = self.portInput.text().strip() or "5555"
        
        try:
            port = int(port)
            if port < 1024 or port > 65535:
                raise ValueError("Port must be between 1024 and 65535")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        self.debug_logger.log_debug(f"Enabling TCP/IP mode for device {device_id} on port {port}...", 
                                  category="device", level="info")
        self.statusLabel.setText("Status: Enabling TCP/IP mode...")
        self.tcpipButton.setEnabled(False)
        self._start_worker(self.adb_utils.enable_tcpip, self.handle_tcpip_complete, device_id, port)

    def on_connect_clicked(self):
        """Starts worker to connect to a wireless device."""
        ip = self.ipInput.text().strip()
        port = self.connectPortInput.text().strip() or "5555"
        
        if not ip:
            QMessageBox.warning(self, "Error", "Please enter a device IP address")
            return
            
        try:
            port = int(port)
            if port < 1024 or port > 65535:
                raise ValueError("Port must be between 1024 and 65535")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        self.debug_logger.log_debug(f"Connecting to {ip}:{port}...", category="device", level="info")
        self.statusLabel.setText("Status: Connecting to device...")
        self.connectButton.setEnabled(False)
        self._start_worker(self.adb_utils.connect_wireless, self.handle_connect_complete, ip, port)

    def on_disconnect_clicked(self):
        """Starts worker to disconnect a wireless device."""
        selected_items = self.deviceListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a device to disconnect")
            return

        device_id = selected_items[0].text().split('\t')[0]
        self.debug_logger.log_debug(f"Disconnecting device {device_id}...", category="device", level="info")
        self.statusLabel.setText("Status: Disconnecting device...")
        self.disconnectButton.setEnabled(False)
        self._start_worker(self.adb_utils.disconnect_wireless, self.handle_disconnect_complete, device_id)

    def handle_worker_error(self, error_msg: str):
        """Handle worker thread errors."""
        self.error_logger.log_error(error_msg, category="device")
        self.statusLabel.setText(f"Status: Error - {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)

    def handle_worker_result(self, result):
        """Store worker result for the completion handler."""
        self._last_result = result

    def handle_device_refresh_complete(self):
        """Handle device refresh completion."""
        devices = getattr(self, '_last_result', [])
        self.deviceListWidget.clear()
        
        for device in devices:
            self.deviceListWidget.addItem(f"{device['id']}\t{device['state']}")
            
        self.refreshButton.setEnabled(True)
        self.statusLabel.setText("Status: Device refresh complete")
        self.debug_logger.log_debug("Device refresh complete", category="device", level="info")

    def handle_tcpip_complete(self):
        """Handle TCP/IP mode enable completion."""
        self.tcpipButton.setEnabled(True)
        if getattr(self, '_last_result', False):
            self.statusLabel.setText("Status: TCP/IP mode enabled")
            QMessageBox.information(self, "Success", "TCP/IP mode enabled successfully")
        else:
            self.statusLabel.setText("Status: Failed to enable TCP/IP mode")
        self.start_device_refresh()

    def handle_connect_complete(self):
        """Handle wireless connection completion."""
        self.connectButton.setEnabled(True)
        if getattr(self, '_last_result', False):
            self.statusLabel.setText("Status: Device connected")
            QMessageBox.information(self, "Success", "Device connected successfully")
        else:
            self.statusLabel.setText("Status: Connection failed")
        self.start_device_refresh()

    def handle_disconnect_complete(self):
        """Handle wireless disconnection completion."""
        self.disconnectButton.setEnabled(True)
        if getattr(self, '_last_result', False):
            self.statusLabel.setText("Status: Device disconnected")
            QMessageBox.information(self, "Success", "Device disconnected successfully")
        else:
            self.statusLabel.setText("Status: Disconnection failed")
        self.start_device_refresh()

    def cleanup(self):
        """Clean up resources."""
        # Clean up all active threads
        for thread, worker in self.active_threads[:]:  # Copy list to avoid modification during iteration
            self._cleanup_thread(thread, worker)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from src.utils.adb_utils import ADBUtils
    from src.utils.debug_utils import DebugLogger
    from src.utils.error_utils import ErrorLogger
    
    app = QApplication(sys.argv)
    adb_utils = ADBUtils()
    debug_logger = DebugLogger()
    error_logger = ErrorLogger()
    widget = WirelessHandlerWidget(adb_utils, debug_logger, error_logger)
    widget.show()
    sys.exit(app.exec_())
