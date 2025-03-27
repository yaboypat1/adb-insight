import logging
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMenu,
    QAction, QMessageBox, QHeaderView, QFrame,
    QLineEdit, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QFont, QIcon

from src.utils.adb_utils import ADBUtils
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger
from src.utils.app_utils import AppInfo

class AppTab(QWidget):
    """Tab for managing installed applications"""
    
    def __init__(self, adb_utils: ADBUtils, debug_logger: DebugLogger, error_logger: ErrorLogger, parent=None):
        super().__init__(parent)
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.current_device_id = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI with improved layout and styling"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create header with title and controls
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Installed Applications")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add device selector
        self.deviceCombo = QComboBox()
        self.deviceCombo.currentIndexChanged.connect(self.on_device_changed)
        header_layout.addWidget(self.deviceCombo)
        
        self.refreshButton = QPushButton("Refresh")
        self.refreshButton.setIcon(QIcon.fromTheme("view-refresh"))
        self.refreshButton.clicked.connect(self.refresh_apps)
        header_layout.addWidget(self.refreshButton)
        
        layout.addLayout(header_layout)

        # Create filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("Search packages...")
        self.searchInput.textChanged.connect(self.filter_apps)
        filter_layout.addWidget(self.searchInput)
        
        self.filterCombo = QComboBox()
        self.filterCombo.addItems(["All", "System", "User", "Disabled"])
        self.filterCombo.currentTextChanged.connect(self.filter_apps)
        filter_layout.addWidget(self.filterCombo)
        
        layout.addWidget(filter_group)

        # Create app table
        self.appTable = QTableWidget()
        self.appTable.setColumnCount(4)
        self.appTable.setHorizontalHeaderLabels(["Package Name", "Version", "Size", "Status"])
        self.appTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.appTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.appTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.appTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.appTable.verticalHeader().setVisible(False)
        self.appTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.appTable.setSelectionMode(QTableWidget.SingleSelection)
        self.appTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.appTable.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.appTable)

        # Create status bar
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.statusLabel = QLabel("Ready")
        status_layout.addWidget(self.statusLabel)
        layout.addWidget(status_frame)

        # Initial refresh of devices
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh the list of connected devices"""
        try:
            self.debug_logger.log_debug("Refreshing device list...", category="apps", level="info")
            devices = self.adb_utils.get_devices()
            
            # Update device combo
            self.deviceCombo.clear()
            for device in devices:
                self.deviceCombo.addItem(f"{device['id']} ({device.get('model', 'Unknown')})", device['id'])
            
            # Set current device
            if self.deviceCombo.count() > 0:
                self.current_device_id = self.deviceCombo.currentData()
                self.refresh_apps()
            else:
                self.current_device_id = None
                self.statusLabel.setText("No devices connected")
                self.appTable.setRowCount(0)
                
        except Exception as e:
            self.error_logger.log_error(f"Error refreshing devices: {str(e)}", category="apps")
            self.statusLabel.setText("Error refreshing devices")
            QMessageBox.critical(self, "Error", f"Failed to refresh devices:\n{str(e)}")

    def on_device_changed(self, index: int):
        """Handle device selection change"""
        if index >= 0:
            self.current_device_id = self.deviceCombo.currentData()
            self.refresh_apps()

    def refresh_apps(self):
        """Refresh the list of installed apps"""
        if not self.current_device_id:
            self.statusLabel.setText("No device selected")
            return
            
        try:
            self.debug_logger.log_debug("Starting app refresh...", category="apps", level="info")
            self.statusLabel.setText("Refreshing apps...")
            self.refreshButton.setEnabled(False)
            self.appTable.setRowCount(0)
            
            # Get installed packages
            packages = self.adb_utils.get_installed_packages(self.current_device_id)
            
            # Update table
            self.appTable.setRowCount(len(packages))
            for i, package in enumerate(packages):
                self.appTable.setItem(i, 0, QTableWidgetItem(package['name']))
                self.appTable.setItem(i, 1, QTableWidgetItem(package.get('version', 'Unknown')))
                self.appTable.setItem(i, 2, QTableWidgetItem(str(package.get('size', 0))))
                self.appTable.setItem(i, 3, QTableWidgetItem(package.get('status', 'Unknown')))
                
            self.statusLabel.setText(f"Found {len(packages)} packages")
            self.debug_logger.log_debug(f"App refresh complete. Found {len(packages)} packages.", category="apps", level="info")
            
        except Exception as e:
            self.error_logger.log_error(f"Error refreshing apps: {str(e)}", category="apps")
            self.statusLabel.setText("Error refreshing apps")
            QMessageBox.critical(self, "Error", f"Failed to refresh apps:\n{str(e)}")
        finally:
            self.refreshButton.setEnabled(True)

    def filter_apps(self):
        """Filter apps based on search text and combo selection"""
        search_text = self.searchInput.text().lower()
        filter_type = self.filterCombo.currentText()
        
        for row in range(self.appTable.rowCount()):
            package_name = self.appTable.item(row, 0).text().lower()
            status = self.appTable.item(row, 3).text() if self.appTable.item(row, 3) else ""
            
            show_row = True
            if search_text and search_text not in package_name:
                show_row = False
            elif filter_type != "All":
                if filter_type == "System" and "system" not in status.lower():
                    show_row = False
                elif filter_type == "User" and "user" not in status.lower():
                    show_row = False
                elif filter_type == "Disabled" and "disabled" not in status.lower():
                    show_row = False
                    
            self.appTable.setRowHidden(row, not show_row)

    def show_context_menu(self, pos):
        """Show context menu for selected app"""
        selected_items = self.appTable.selectedItems()
        if not selected_items:
            return
            
        package_name = selected_items[0].text()
        
        menu = QMenu(self)
        launch_action = menu.addAction("Launch")
        uninstall_action = menu.addAction("Uninstall")
        disable_action = menu.addAction("Disable")
        
        action = menu.exec_(self.appTable.mapToGlobal(pos))
        if action == launch_action:
            self.launch_app(package_name)
        elif action == uninstall_action:
            self.uninstall_app(package_name)
        elif action == disable_action:
            self.disable_app(package_name)

    def launch_app(self, package_name: str):
        """Launch the selected app"""
        if not self.current_device_id:
            QMessageBox.warning(self, "Error", "No device selected")
            return
            
        try:
            self.adb_utils.launch_app(self.current_device_id, package_name)
            self.debug_logger.log_debug(f"Launching app: {package_name}", category="apps", level="info")
            self.statusLabel.setText(f"Launching {package_name}...")
            
        except Exception as e:
            self.error_logger.log_error(f"Error launching app: {str(e)}", category="apps")
            self.statusLabel.setText("Error launching app")
            QMessageBox.critical(self, "Error", f"Failed to launch app:\n{str(e)}")

    def uninstall_app(self, package_name: str):
        """Uninstall the selected app"""
        if not self.current_device_id:
            QMessageBox.warning(self, "Error", "No device selected")
            return
            
        try:
            reply = QMessageBox.question(self, "Uninstall App", f"Are you sure you want to uninstall {package_name}?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.adb_utils.uninstall_package(self.current_device_id, package_name)
                self.debug_logger.log_debug(f"Uninstalling app: {package_name}", category="apps", level="info")
                self.statusLabel.setText(f"Uninstalling {package_name}...")
                self.refresh_apps()
                
        except Exception as e:
            self.error_logger.log_error(f"Error uninstalling app: {str(e)}", category="apps")
            self.statusLabel.setText("Error uninstalling app")
            QMessageBox.critical(self, "Error", f"Failed to uninstall app:\n{str(e)}")

    def disable_app(self, package_name: str):
        """Disable the selected app"""
        if not self.current_device_id:
            QMessageBox.warning(self, "Error", "No device selected")
            return
            
        try:
            reply = QMessageBox.question(self, "Disable App", f"Are you sure you want to disable {package_name}?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.adb_utils.disable_app(self.current_device_id, package_name)
                self.debug_logger.log_debug(f"Disabling app: {package_name}", category="apps", level="info")
                self.statusLabel.setText(f"Disabling {package_name}...")
                self.refresh_apps()
                
        except Exception as e:
            self.error_logger.log_error(f"Error disabling app: {str(e)}", category="apps")
            self.statusLabel.setText("Error disabling app")
            QMessageBox.critical(self, "Error", f"Failed to disable app:\n{str(e)}")

    def cleanup(self):
        """Clean up resources"""
        pass  # Nothing to clean up yet
