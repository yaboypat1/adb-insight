from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QMessageBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QTimer

class WirelessDialog(QDialog):
    def __init__(self, adb_utils, parent=None):
        super().__init__(parent)
        self.adb_utils = adb_utils
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Wireless ADB Connection")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "To connect wirelessly:\n"
            "1. Make sure your device is on the same network\n"
            "2. Enable wireless debugging on your device\n"
            "3. Either:\n"
            "   - Click 'Start Pairing' to start automatic pairing, or\n"
            "   - Enter the pairing code shown on your device manually"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # IP Address input
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP Address:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        
        # Port input
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("5555")
        ip_layout.addWidget(port_label)
        ip_layout.addWidget(self.port_input)
        
        layout.addLayout(ip_layout)
        
        # Pairing code input
        code_layout = QHBoxLayout()
        code_label = QLabel("Pairing Code:")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setMaxLength(6)
        self.code_input.textChanged.connect(self._on_code_changed)
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_input)
        layout.addLayout(code_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.pair_button = QPushButton("Start Pairing")
        self.pair_button.clicked.connect(self.start_pairing)
        button_layout.addWidget(self.pair_button)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)
        button_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        button_layout.addWidget(self.disconnect_button)
        
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        # Set initial button states
        self._on_code_changed()
        
    def _on_code_changed(self):
        """Handle pairing code changes"""
        code = self.code_input.text().strip()
        valid_code = len(code) == 6 and code.isdigit()
        
        # Enable connect button if we have a valid code
        self.connect_button.setEnabled(valid_code)
        
        # Update status
        if valid_code:
            self.status_label.setText("Ready to connect")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Enter a 6-digit code to connect")
            self.status_label.setStyleSheet("color: gray;")
            
    def start_pairing(self):
        """Start the wireless pairing process"""
        progress = QProgressDialog("Starting wireless pairing...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        QTimer.singleShot(100, lambda: self._do_start_pairing(progress))
        
    def _do_start_pairing(self, progress):
        """Actually perform the pairing process"""
        code = self.adb_utils.start_wireless_pairing()
        progress.close()
        
        if code:
            self.code_input.setText(code)
            self.pair_button.setText("Complete Pairing")
            self.pair_button.clicked.disconnect()
            self.pair_button.clicked.connect(self.complete_pairing)
            self.status_label.setText("Verify the code matches your device")
            self.status_label.setStyleSheet("color: blue;")
        else:
            QMessageBox.warning(self, "Error", "Failed to start wireless pairing")
            
    def complete_pairing(self):
        """Complete the pairing process with the entered code"""
        code = self.code_input.text().strip()
        if not code or len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Error", "Please enter a valid 6-digit code")
            return
            
        if self.adb_utils.pair_wireless_device(code):
            self.status_label.setText("Successfully paired! You can now connect.")
            self.status_label.setStyleSheet("color: green;")
            self.connect_button.setEnabled(True)
            self.pair_button.setEnabled(False)
        else:
            QMessageBox.warning(self, "Error", "Pairing failed. Please try again.")
            
    def connect_device(self):
        """Connect to the wireless device"""
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip() or "5555"
        
        if not ip:
            QMessageBox.warning(self, "Error", "Please enter an IP address")
            return
            
        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(self, "Error", "Port must be a number")
            return
            
        if self.adb_utils.connect_wireless_device(ip, port):
            self.status_label.setText(f"Connected to {ip}:{port}")
            self.status_label.setStyleSheet("color: green;")
        else:
            QMessageBox.warning(self, "Error", "Failed to connect to device")
            
    def disconnect_device(self):
        """Disconnect from wireless device"""
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip() or "5555"
        
        try:
            port = int(port)
        except ValueError:
            port = 5555
            
        if self.adb_utils.disconnect_wireless_device(ip if ip else None, port):
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: gray;")
        else:
            QMessageBox.warning(self, "Error", "Failed to disconnect")
