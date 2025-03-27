<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTabWidget, QLabel, QPushButton, QProgressBar,
                             QCheckBox, QMessageBox, QScrollArea, QListWidgetItem,
                             QGroupBox, QComboBox, QTextEdit)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool, Signal
import humanize
from datetime import datetime
import concurrent.futures
import threading
import subprocess

from ..utils.app_utils import AppUtils
from ..utils.error_utils import ErrorLogger
from ..utils.debug_utils import DebugLogger
from ..utils.adb_utils import ADBUtils
from ..utils.error_codes import ErrorCode

class AppListItem(QListWidgetItem):
    """Custom list item for app list"""
    def __init__(self, name: str, package: str):
        super().__init__(name)
        self.package_name = package
        self.setData(Qt.UserRole, package)

class AppTabSignals(QObject):
    """Signals for AppTab worker threads"""
    apps_ready = Signal(dict)  # {'user': user_apps, 'system': system_apps}
    error = Signal(str)  # Error message
    device_state = Signal(bool, str)  # Connected, Device ID
    progress = Signal(str)  # Progress message

class AppTabWorker(QRunnable):
    """Worker thread for AppTab operations"""
    
    def __init__(self, adb_utils, debug_logger, error_logger):
        super().__init__()
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.signals = AppTabSignals()
        
    def fetch_apps(self, user_only: bool = True, system_only: bool = False):
        """Fetch installed apps in background"""
        try:
            self.signals.progress.emit("Fetching installed apps...")
            
            # Check device connection first
            devices = self.adb_utils.get_connected_devices()
            if not devices:
                self.error_logger.log_error(
                    "No device connected",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("No device connected. Please connect a device and try again.")
                return
                
            ready_devices = [d for d in devices if d['state'] == 'device']
            if not ready_devices:
                self.error_logger.log_error(
                    "Device not in ready state",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("Device not ready. Please check USB debugging is enabled.")
                return
                
            # Fetch apps based on filters
            apps = {}
            if user_only or not system_only:
                success, user_apps = self.adb_utils.get_installed_apps(system_apps=False)
                if success:
                    apps['user'] = user_apps
                    self.debug_logger.log_debug(
                        f"Found {len(user_apps)} user apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch user apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if system_only or not user_only:
                success, system_apps = self.adb_utils.get_installed_apps(system_apps=True)
                if success:
                    apps['system'] = system_apps
                    self.debug_logger.log_debug(
                        f"Found {len(system_apps)} system apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch system apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if not apps:
                self.signals.error.emit("Failed to fetch any apps. Check device connection and try again.")
                return
                
            self.signals.apps_ready.emit(apps)
            
        except FileNotFoundError as e:
            error_msg = "ADB not found. Please ensure Android SDK platform-tools are installed and in your PATH."
            self.error_logger.log_error(error_msg, ErrorCode.ADB_NOT_FOUND)
            self.signals.error.emit(error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"ADB command failed: {e.stderr.strip() if e.stderr else str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.ADB_COMMAND_FAILED)
            self.signals.error.emit(error_msg)
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out. Check device connection and try again."
            self.error_logger.log_error(error_msg, ErrorCode.COMMAND_TIMEOUT)
            self.signals.error.emit(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.UNKNOWN_ERROR)
            self.signals.error.emit(error_msg)
            
class AppTab(QWidget):
    update_ui_signal = pyqtSignal(object)
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        """Initialize AppTab"""
        super().__init__()
        
        # Store loggers
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Initialize worker thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.workers = []
        
        # Connect UI update signal
        self.update_ui_signal.connect(lambda func: func())
        
        # Initialize ADBUtils with loggers
        try:
            self.adb_utils = ADBUtils(debug_logger, error_logger)
            
            # Connect signals
            if self.adb_utils:
                # Debug logging
                if self.adb_utils.debug_logger:
                    self.adb_utils.debug_logger.add_listener(self._on_debug_entry)
                    
                # Device state changes
                self.adb_utils.device_state_changed.connect(self._on_device_state_changed)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to initialize ADBUtils: {str(e)}")
            self.adb_utils = None
            
        # Initialize UI
        self._init_ui()
        
        # Setup refresh timers
        self.setup_refresh_timers()
        
        # Initial refresh if device connected
        if self.adb_utils and self.adb_utils.adb_ready:
            self.refresh_app_list(silent=True)
            
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Checking device status...")
        self.status_label.setStyleSheet("color: gray")
        status_layout.addWidget(self.status_label)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(self.refresh_app_list)
        status_layout.addWidget(self.refresh_btn)
        
        # Auto refresh checkbox
        self.auto_refresh = QCheckBox("Auto Refresh")
        self.auto_refresh.setEnabled(False)
        self.auto_refresh.stateChanged.connect(self._on_auto_refresh_changed)
        status_layout.addWidget(self.auto_refresh)
        
        # Show system apps checkbox
        self.show_system_apps = QCheckBox("Show System Apps")
        self.show_system_apps.setEnabled(False)
        self.show_system_apps.stateChanged.connect(self._on_show_system_apps_changed)
        status_layout.addWidget(self.show_system_apps)
        
        layout.addLayout(status_layout)
        
        # App list
        self.app_list = QListWidget()
        self.app_list.itemSelectionChanged.connect(self._on_app_selected)
        layout.addWidget(self.app_list)
        
        # App details
        details_group = QGroupBox("App Details")
        details_layout = QVBoxLayout()
        
        # Memory usage
        self.memory_label = QLabel("Memory Usage: N/A")
        details_layout.addWidget(self.memory_label)
        
        # Analytics
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        self.analytics_text.setMinimumHeight(100)
        details_layout.addWidget(self.analytics_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        
    def _on_device_state_changed(self, connected: bool):
        """Handle device connection state change"""
        # Update UI elements
        self.refresh_btn.setEnabled(connected)
        self.auto_refresh.setEnabled(connected)
        self.show_system_apps.setEnabled(connected)
        
        # Update status
        if connected:
            self.status_label.setText("Device connected")
            self.status_label.setStyleSheet("color: green")
            self.refresh_app_list(silent=True)
        else:
            self.status_label.setText("No device connected")
            self.status_label.setStyleSheet("color: red")
            self.app_list.clear()
            self.details_text.clear()

    def _on_debug_entry(self, message: str, level: str, category: str):
        """Handle debug log entry"""
        # Update status label if it's a device status message
        if category == 'device':
            self.status_label.setText(message)
            if level == 'error':
                self.status_label.setStyleSheet("color: red")
            elif level == 'warning':
                self.status_label.setStyleSheet("color: orange")
            else:
                self.status_label.setStyleSheet("color: green")

    def _on_error(self, error_msg: str):
        """Handle error from worker thread"""
        self.error_logger.log_error(error_msg)
        QMessageBox.critical(self, "Error", error_msg)

    def setup_refresh_timers(self):
        """Set up refresh timers"""
        # App list refresh timer
        self.app_refresh_timer = QTimer()
        self.app_refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.app_refresh_timer.start(5000)  # Every 5 seconds
        
        # Memory refresh timer
        self.memory_refresh_timer = QTimer()
        self.memory_refresh_timer.timeout.connect(self._refresh_memory)
        self.memory_refresh_timer.start(2000)  # Every 2 seconds
        
    def refresh_app_list(self, silent=False):
        """Refresh the app list"""
        worker = AppTabWorker(self.adb_utils, self.debug_logger, self.error_logger)
        worker.signals.apps_ready.connect(self._handle_apps_ready)
        worker.signals.error.connect(self._handle_error)
        worker.signals.progress.connect(self._handle_progress)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)
        
    def _handle_apps_ready(self, apps: dict):
        """Handle apps fetched from worker thread"""
        try:
            self.app_list.clear()
            
            # Add user apps
            if 'user' in apps:
                user_apps = apps['user']
                self._add_apps_to_list("User Apps", user_apps)
                
            # Add system apps
            if 'system' in apps:
                system_apps = apps['system']
                self._add_apps_to_list("System Apps", system_apps)
                
            self.debug_logger.log_debug(
                f"Updated app list with {len(apps.get('user', []))} user apps and {len(apps.get('system', []))} system apps",
                "ui",
                "info"
            )
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to update app list: {str(e)}",
                ErrorCode.UI_UPDATE_FAILED
            )
            
    def _handle_error(self, message: str):
        """Handle error from worker thread"""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: red")
        
    def _handle_progress(self, message: str):
        """Handle progress update from worker thread"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("")
        
    def _add_apps_to_list(self, title: str, apps: list):
        """Add apps to list widget"""
        for app in apps:
            item = QListWidgetItem()
            item.setText(f"{app['name']} ({app['package']})")
            item.setData(Qt.UserRole, app['package'])
            
            if app.get('system', False):
                item.setForeground(QBrush(QColor('gray')))
                
            self.app_list.addItem(item)
            
    def _refresh_memory(self):
        """Refresh memory info for selected app"""
        if not self.adb_utils:
            QMessageBox.warning(self, "Warning", "ADBUtils not initialized")
            return
            
        try:
            item = self.app_list.currentItem()
            if item:
                self._on_selection_changed()
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to refresh memory: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh memory: {str(e)}")
            
    def _update_memory_info(self):
        """Update memory information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                memory_info = self.adb_utils.get_memory_info(package)
                if memory_info:
                    self.memory_info_label.setText(f"Memory Usage: {memory_info['total_mb']:.1f} MB")
        except Exception as e:
            self.error_logger.log_error(f"Failed to update memory info: {str(e)}")
            
    def _update_analytics(self):
        """Update analytics information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                # Use ThreadPoolExecutor for analytics updates
                self.executor.submit(self._fetch_analytics, package)
        except Exception as e:
            self.error_logger.log_error(f"Failed to update analytics: {str(e)}")
    
    def _fetch_analytics(self, package: str):
        """Fetch analytics data in background"""
        try:
            # Get analytics data
            analytics = self.adb_utils.get_app_analytics(package)
            if not analytics:
                return
                
            # Update UI in main thread using signals
            self.cpu_label.setText(f"CPU Usage: {analytics.get('cpu_usage', 0):.1f}%")
            self.battery_label.setText(f"Battery Drain: {analytics.get('battery_drain', 0):.1f}%/hr")
            
            # Network usage
            rx_bytes = analytics.get('network', {}).get('rx_bytes', 0)
            tx_bytes = analytics.get('network', {}).get('tx_bytes', 0)
            rx_mb = rx_bytes / (1024 * 1024)
            tx_mb = tx_bytes / (1024 * 1024)
            
            self.rx_label.setText(f"Received: {rx_mb:.1f} MB")
            self.tx_label.setText(f"Transmitted: {tx_mb:.1f} MB")
            
            # Storage usage
            storage = analytics.get('storage', {})
            app_mb = storage.get('app_size', 0) / (1024 * 1024)
            data_mb = storage.get('data_size', 0) / (1024 * 1024)
            
            self.app_size_label.setText(f"App Size: {app_mb:.1f} MB")
            self.data_size_label.setText(f"Data Size: {data_mb:.1f} MB")
            self.total_size_label.setText(f"Total Size: {app_mb + data_mb:.1f} MB")
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to fetch analytics: {str(e)}")
            
    def _on_selection_changed(self):
        """Handle app selection"""
        try:
            items = self.app_list.selectedItems()
            if not items:
                self.memory_label.setText("Memory Usage: N/A")
                self.analytics_text.clear()
                return
                
            # Get selected package
            package = items[0].data(Qt.UserRole)
            if not package:
                return
                
            # Update status
            self.status_label.setText(f"Loading details for {package}...")
            self.status_label.setStyleSheet("color: blue")
            
            # Get memory info
            memory = self.adb_utils.get_memory_info(package)
            if memory:
                total = humanize.naturalsize(memory.get('total_memory', 0))
                self.memory_label.setText(f"Memory Usage: {total}")
            else:
                self.memory_label.setText("Memory Usage: N/A")
                
            # Get analytics
            analytics = self.adb_utils.get_app_analytics(package)
            if analytics:
                # Format analytics text
                lines = []
                
                # CPU
                cpu = analytics.get('cpu', 0)
                lines.append(f"CPU Usage: {cpu:.1f}%")
                
                # Memory breakdown
                if 'memory' in analytics:
                    mem = analytics['memory']
                    lines.extend([
                        "\nMemory Breakdown:",
                        f"  Java Heap: {humanize.naturalsize(mem.get('java', 0))}",
                        f"  Native Heap: {humanize.naturalsize(mem.get('native', 0))}",
                        f"  Code: {humanize.naturalsize(mem.get('code', 0))}",
                        f"  Stack: {humanize.naturalsize(mem.get('stack', 0))}",
                        f"  Graphics: {humanize.naturalsize(mem.get('graphics', 0))}"
                    ])
                
                # Battery
                battery = analytics.get('battery', 0)
                lines.append(f"\nBattery Usage: {battery:.1f}%")
                
                # Network
                rx = humanize.naturalsize(analytics.get('rx_bytes', 0))
                tx = humanize.naturalsize(analytics.get('tx_bytes', 0))
                lines.append(f"\nNetwork Traffic:")
                lines.append(f"  Received: {rx}")
                lines.append(f"  Sent: {tx}")
                
                # Update text
                self.analytics_text.setText('\n'.join(lines))
                
                # Update status
                self.status_label.setText("Details loaded")
                self.status_label.setStyleSheet("color: green")
            else:
                self.analytics_text.setText("No analytics available")
                self.status_label.setText("Could not load details")
                self.status_label.setStyleSheet("color: orange")
                
        except Exception as e:
            error_msg = f"Failed to update app details: {str(e)}"
            self.error_logger.log_error(error_msg)
            self.debug_logger.log_debug(error_msg, "app_select", "error")
            
            self.status_label.setText("Error: Failed to load details")
            self.status_label.setStyleSheet("color: red")
            
    def _check_adb_status(self):
        """Check ADB status and update UI accordingly"""
        if not self.adb_utils:
            return
            
        def check_worker():
            try:
                if self.adb_utils.check_adb_status():
                    # ADB is ready, try to refresh app list
                    self._refresh_app_list()
                else:
                    # Update UI in main thread
                    self.update_ui_signal.emit(lambda: self._update_no_device_ui())
            except Exception as e:
                self.error_logger.log_error(f"Error checking device status: {str(e)}")
                
        # Run in worker thread
        self.executor.submit(check_worker)
        
    def _update_no_device_ui(self):
        """Update UI when no device is connected"""
        self.app_list.clear()
        self.app_list.addItem("No device connected")
        self.status_label.setText("No device connected")
        self.status_label.setStyleSheet("color: red")
        self.refresh_btn.setEnabled(False)
        self.auto_refresh.setEnabled(False)
        self.show_system_apps.setEnabled(False)
        
    def _refresh_app_list(self):
        """Refresh app list silently"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        # Use a worker thread for app list refresh
        def refresh_worker():
            try:
                apps = self.adb_utils.get_installed_apps()
                # Update UI in main thread
                if apps:
                    self.app_list.clear()
                    for app in apps:
                        name = app.get('name', app['package'])
                        package = app['package']
                        
                        # If name is same as package, try to make it more readable
                        if name == package:
                            name = package.split('.')[-1].replace('_', ' ').title()
                        
                        item = AppListItem(name, package)
                        if app.get('system', False):
                            item.setForeground(Qt.gray)
                        self.app_list.addItem(item)
            except Exception as e:
                self.error_logger.log_error(f"Failed to refresh app list: {str(e)}")
        
        # Run in worker thread
        self.executor.submit(refresh_worker)
    
    def _on_auto_refresh_changed(self, state: int):
        """Handle auto refresh checkbox state change"""
        if state == Qt.Checked:
            self.setup_refresh_timers()
        else:
            self.stop_refresh_timers()
            
    def setup_refresh_timers(self):
        """Setup refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def stop_refresh_timers(self):
        """Stop refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.executor.shutdown(wait=False)
        for worker in self.workers:
            worker.quit()
            worker.wait()
        super().closeEvent(event)
        
=======
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTabWidget, QLabel, QPushButton, QProgressBar,
                             QCheckBox, QMessageBox, QScrollArea, QListWidgetItem,
                             QGroupBox, QComboBox, QTextEdit)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool, Signal
import humanize
from datetime import datetime
import concurrent.futures
import threading
import subprocess

from ..utils.app_utils import AppUtils
from ..utils.error_utils import ErrorLogger
from ..utils.debug_utils import DebugLogger
from ..utils.adb_utils import ADBUtils
from ..utils.error_codes import ErrorCode

class AppListItem(QListWidgetItem):
    """Custom list item for app list"""
    def __init__(self, name: str, package: str):
        super().__init__(name)
        self.package_name = package
        self.setData(Qt.UserRole, package)

class AppTabSignals(QObject):
    """Signals for AppTab worker threads"""
    apps_ready = Signal(dict)  # {'user': user_apps, 'system': system_apps}
    error = Signal(str)  # Error message
    device_state = Signal(bool, str)  # Connected, Device ID
    progress = Signal(str)  # Progress message

class AppTabWorker(QRunnable):
    """Worker thread for AppTab operations"""
    
    def __init__(self, adb_utils, debug_logger, error_logger):
        super().__init__()
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.signals = AppTabSignals()
        
    def fetch_apps(self, user_only: bool = True, system_only: bool = False):
        """Fetch installed apps in background"""
        try:
            self.signals.progress.emit("Fetching installed apps...")
            
            # Check device connection first
            devices = self.adb_utils.get_connected_devices()
            if not devices:
                self.error_logger.log_error(
                    "No device connected",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("No device connected. Please connect a device and try again.")
                return
                
            ready_devices = [d for d in devices if d['state'] == 'device']
            if not ready_devices:
                self.error_logger.log_error(
                    "Device not in ready state",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("Device not ready. Please check USB debugging is enabled.")
                return
                
            # Fetch apps based on filters
            apps = {}
            if user_only or not system_only:
                success, user_apps = self.adb_utils.get_installed_apps(system_apps=False)
                if success:
                    apps['user'] = user_apps
                    self.debug_logger.log_debug(
                        f"Found {len(user_apps)} user apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch user apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if system_only or not user_only:
                success, system_apps = self.adb_utils.get_installed_apps(system_apps=True)
                if success:
                    apps['system'] = system_apps
                    self.debug_logger.log_debug(
                        f"Found {len(system_apps)} system apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch system apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if not apps:
                self.signals.error.emit("Failed to fetch any apps. Check device connection and try again.")
                return
                
            self.signals.apps_ready.emit(apps)
            
        except FileNotFoundError as e:
            error_msg = "ADB not found. Please ensure Android SDK platform-tools are installed and in your PATH."
            self.error_logger.log_error(error_msg, ErrorCode.ADB_NOT_FOUND)
            self.signals.error.emit(error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"ADB command failed: {e.stderr.strip() if e.stderr else str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.ADB_COMMAND_FAILED)
            self.signals.error.emit(error_msg)
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out. Check device connection and try again."
            self.error_logger.log_error(error_msg, ErrorCode.COMMAND_TIMEOUT)
            self.signals.error.emit(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.UNKNOWN_ERROR)
            self.signals.error.emit(error_msg)
            
class AppTab(QWidget):
    update_ui_signal = pyqtSignal(object)
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        """Initialize AppTab"""
        super().__init__()
        
        # Store loggers
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Initialize worker thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.workers = []
        
        # Connect UI update signal
        self.update_ui_signal.connect(lambda func: func())
        
        # Initialize ADBUtils with loggers
        try:
            self.adb_utils = ADBUtils(debug_logger, error_logger)
            
            # Connect signals
            if self.adb_utils:
                # Debug logging
                if self.adb_utils.debug_logger:
                    self.adb_utils.debug_logger.add_listener(self._on_debug_entry)
                    
                # Device state changes
                self.adb_utils.device_state_changed.connect(self._on_device_state_changed)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to initialize ADBUtils: {str(e)}")
            self.adb_utils = None
            
        # Initialize UI
        self._init_ui()
        
        # Setup refresh timers
        self.setup_refresh_timers()
        
        # Initial refresh if device connected
        if self.adb_utils and self.adb_utils.adb_ready:
            self.refresh_app_list(silent=True)
            
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Checking device status...")
        self.status_label.setStyleSheet("color: gray")
        status_layout.addWidget(self.status_label)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(self.refresh_app_list)
        status_layout.addWidget(self.refresh_btn)
        
        # Auto refresh checkbox
        self.auto_refresh = QCheckBox("Auto Refresh")
        self.auto_refresh.setEnabled(False)
        self.auto_refresh.stateChanged.connect(self._on_auto_refresh_changed)
        status_layout.addWidget(self.auto_refresh)
        
        # Show system apps checkbox
        self.show_system_apps = QCheckBox("Show System Apps")
        self.show_system_apps.setEnabled(False)
        self.show_system_apps.stateChanged.connect(self._on_show_system_apps_changed)
        status_layout.addWidget(self.show_system_apps)
        
        layout.addLayout(status_layout)
        
        # App list
        self.app_list = QListWidget()
        self.app_list.itemSelectionChanged.connect(self._on_app_selected)
        layout.addWidget(self.app_list)
        
        # App details
        details_group = QGroupBox("App Details")
        details_layout = QVBoxLayout()
        
        # Memory usage
        self.memory_label = QLabel("Memory Usage: N/A")
        details_layout.addWidget(self.memory_label)
        
        # Analytics
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        self.analytics_text.setMinimumHeight(100)
        details_layout.addWidget(self.analytics_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        
    def _on_device_state_changed(self, connected: bool):
        """Handle device connection state change"""
        # Update UI elements
        self.refresh_btn.setEnabled(connected)
        self.auto_refresh.setEnabled(connected)
        self.show_system_apps.setEnabled(connected)
        
        # Update status
        if connected:
            self.status_label.setText("Device connected")
            self.status_label.setStyleSheet("color: green")
            self.refresh_app_list(silent=True)
        else:
            self.status_label.setText("No device connected")
            self.status_label.setStyleSheet("color: red")
            self.app_list.clear()
            self.details_text.clear()

    def _on_debug_entry(self, message: str, level: str, category: str):
        """Handle debug log entry"""
        # Update status label if it's a device status message
        if category == 'device':
            self.status_label.setText(message)
            if level == 'error':
                self.status_label.setStyleSheet("color: red")
            elif level == 'warning':
                self.status_label.setStyleSheet("color: orange")
            else:
                self.status_label.setStyleSheet("color: green")

    def _on_error(self, error_msg: str):
        """Handle error from worker thread"""
        self.error_logger.log_error(error_msg)
        QMessageBox.critical(self, "Error", error_msg)

    def setup_refresh_timers(self):
        """Set up refresh timers"""
        # App list refresh timer
        self.app_refresh_timer = QTimer()
        self.app_refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.app_refresh_timer.start(5000)  # Every 5 seconds
        
        # Memory refresh timer
        self.memory_refresh_timer = QTimer()
        self.memory_refresh_timer.timeout.connect(self._refresh_memory)
        self.memory_refresh_timer.start(2000)  # Every 2 seconds
        
    def refresh_app_list(self, silent=False):
        """Refresh the app list"""
        worker = AppTabWorker(self.adb_utils, self.debug_logger, self.error_logger)
        worker.signals.apps_ready.connect(self._handle_apps_ready)
        worker.signals.error.connect(self._handle_error)
        worker.signals.progress.connect(self._handle_progress)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)
        
    def _handle_apps_ready(self, apps: dict):
        """Handle apps fetched from worker thread"""
        try:
            self.app_list.clear()
            
            # Add user apps
            if 'user' in apps:
                user_apps = apps['user']
                self._add_apps_to_list("User Apps", user_apps)
                
            # Add system apps
            if 'system' in apps:
                system_apps = apps['system']
                self._add_apps_to_list("System Apps", system_apps)
                
            self.debug_logger.log_debug(
                f"Updated app list with {len(apps.get('user', []))} user apps and {len(apps.get('system', []))} system apps",
                "ui",
                "info"
            )
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to update app list: {str(e)}",
                ErrorCode.UI_UPDATE_FAILED
            )
            
    def _handle_error(self, message: str):
        """Handle error from worker thread"""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: red")
        
    def _handle_progress(self, message: str):
        """Handle progress update from worker thread"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("")
        
    def _add_apps_to_list(self, title: str, apps: list):
        """Add apps to list widget"""
        for app in apps:
            item = QListWidgetItem()
            item.setText(f"{app['name']} ({app['package']})")
            item.setData(Qt.UserRole, app['package'])
            
            if app.get('system', False):
                item.setForeground(QBrush(QColor('gray')))
                
            self.app_list.addItem(item)
            
    def _refresh_memory(self):
        """Refresh memory info for selected app"""
        if not self.adb_utils:
            QMessageBox.warning(self, "Warning", "ADBUtils not initialized")
            return
            
        try:
            item = self.app_list.currentItem()
            if item:
                self._on_selection_changed()
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to refresh memory: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh memory: {str(e)}")
            
    def _update_memory_info(self):
        """Update memory information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                memory_info = self.adb_utils.get_memory_info(package)
                if memory_info:
                    self.memory_info_label.setText(f"Memory Usage: {memory_info['total_mb']:.1f} MB")
        except Exception as e:
            self.error_logger.log_error(f"Failed to update memory info: {str(e)}")
            
    def _update_analytics(self):
        """Update analytics information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                # Use ThreadPoolExecutor for analytics updates
                self.executor.submit(self._fetch_analytics, package)
        except Exception as e:
            self.error_logger.log_error(f"Failed to update analytics: {str(e)}")
    
    def _fetch_analytics(self, package: str):
        """Fetch analytics data in background"""
        try:
            # Get analytics data
            analytics = self.adb_utils.get_app_analytics(package)
            if not analytics:
                return
                
            # Update UI in main thread using signals
            self.cpu_label.setText(f"CPU Usage: {analytics.get('cpu_usage', 0):.1f}%")
            self.battery_label.setText(f"Battery Drain: {analytics.get('battery_drain', 0):.1f}%/hr")
            
            # Network usage
            rx_bytes = analytics.get('network', {}).get('rx_bytes', 0)
            tx_bytes = analytics.get('network', {}).get('tx_bytes', 0)
            rx_mb = rx_bytes / (1024 * 1024)
            tx_mb = tx_bytes / (1024 * 1024)
            
            self.rx_label.setText(f"Received: {rx_mb:.1f} MB")
            self.tx_label.setText(f"Transmitted: {tx_mb:.1f} MB")
            
            # Storage usage
            storage = analytics.get('storage', {})
            app_mb = storage.get('app_size', 0) / (1024 * 1024)
            data_mb = storage.get('data_size', 0) / (1024 * 1024)
            
            self.app_size_label.setText(f"App Size: {app_mb:.1f} MB")
            self.data_size_label.setText(f"Data Size: {data_mb:.1f} MB")
            self.total_size_label.setText(f"Total Size: {app_mb + data_mb:.1f} MB")
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to fetch analytics: {str(e)}")
            
    def _on_selection_changed(self):
        """Handle app selection"""
        try:
            items = self.app_list.selectedItems()
            if not items:
                self.memory_label.setText("Memory Usage: N/A")
                self.analytics_text.clear()
                return
                
            # Get selected package
            package = items[0].data(Qt.UserRole)
            if not package:
                return
                
            # Update status
            self.status_label.setText(f"Loading details for {package}...")
            self.status_label.setStyleSheet("color: blue")
            
            # Get memory info
            memory = self.adb_utils.get_memory_info(package)
            if memory:
                total = humanize.naturalsize(memory.get('total_memory', 0))
                self.memory_label.setText(f"Memory Usage: {total}")
            else:
                self.memory_label.setText("Memory Usage: N/A")
                
            # Get analytics
            analytics = self.adb_utils.get_app_analytics(package)
            if analytics:
                # Format analytics text
                lines = []
                
                # CPU
                cpu = analytics.get('cpu', 0)
                lines.append(f"CPU Usage: {cpu:.1f}%")
                
                # Memory breakdown
                if 'memory' in analytics:
                    mem = analytics['memory']
                    lines.extend([
                        "\nMemory Breakdown:",
                        f"  Java Heap: {humanize.naturalsize(mem.get('java', 0))}",
                        f"  Native Heap: {humanize.naturalsize(mem.get('native', 0))}",
                        f"  Code: {humanize.naturalsize(mem.get('code', 0))}",
                        f"  Stack: {humanize.naturalsize(mem.get('stack', 0))}",
                        f"  Graphics: {humanize.naturalsize(mem.get('graphics', 0))}"
                    ])
                
                # Battery
                battery = analytics.get('battery', 0)
                lines.append(f"\nBattery Usage: {battery:.1f}%")
                
                # Network
                rx = humanize.naturalsize(analytics.get('rx_bytes', 0))
                tx = humanize.naturalsize(analytics.get('tx_bytes', 0))
                lines.append(f"\nNetwork Traffic:")
                lines.append(f"  Received: {rx}")
                lines.append(f"  Sent: {tx}")
                
                # Update text
                self.analytics_text.setText('\n'.join(lines))
                
                # Update status
                self.status_label.setText("Details loaded")
                self.status_label.setStyleSheet("color: green")
            else:
                self.analytics_text.setText("No analytics available")
                self.status_label.setText("Could not load details")
                self.status_label.setStyleSheet("color: orange")
                
        except Exception as e:
            error_msg = f"Failed to update app details: {str(e)}"
            self.error_logger.log_error(error_msg)
            self.debug_logger.log_debug(error_msg, "app_select", "error")
            
            self.status_label.setText("Error: Failed to load details")
            self.status_label.setStyleSheet("color: red")
            
    def _check_adb_status(self):
        """Check ADB status and update UI accordingly"""
        if not self.adb_utils:
            return
            
        def check_worker():
            try:
                if self.adb_utils.check_adb_status():
                    # ADB is ready, try to refresh app list
                    self._refresh_app_list()
                else:
                    # Update UI in main thread
                    self.update_ui_signal.emit(lambda: self._update_no_device_ui())
            except Exception as e:
                self.error_logger.log_error(f"Error checking device status: {str(e)}")
                
        # Run in worker thread
        self.executor.submit(check_worker)
        
    def _update_no_device_ui(self):
        """Update UI when no device is connected"""
        self.app_list.clear()
        self.app_list.addItem("No device connected")
        self.status_label.setText("No device connected")
        self.status_label.setStyleSheet("color: red")
        self.refresh_btn.setEnabled(False)
        self.auto_refresh.setEnabled(False)
        self.show_system_apps.setEnabled(False)
        
    def _refresh_app_list(self):
        """Refresh app list silently"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        # Use a worker thread for app list refresh
        def refresh_worker():
            try:
                apps = self.adb_utils.get_installed_apps()
                # Update UI in main thread
                if apps:
                    self.app_list.clear()
                    for app in apps:
                        name = app.get('name', app['package'])
                        package = app['package']
                        
                        # If name is same as package, try to make it more readable
                        if name == package:
                            name = package.split('.')[-1].replace('_', ' ').title()
                        
                        item = AppListItem(name, package)
                        if app.get('system', False):
                            item.setForeground(Qt.gray)
                        self.app_list.addItem(item)
            except Exception as e:
                self.error_logger.log_error(f"Failed to refresh app list: {str(e)}")
        
        # Run in worker thread
        self.executor.submit(refresh_worker)
    
    def _on_auto_refresh_changed(self, state: int):
        """Handle auto refresh checkbox state change"""
        if state == Qt.Checked:
            self.setup_refresh_timers()
        else:
            self.stop_refresh_timers()
            
    def setup_refresh_timers(self):
        """Setup refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def stop_refresh_timers(self):
        """Stop refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.executor.shutdown(wait=False)
        for worker in self.workers:
            worker.quit()
            worker.wait()
        super().closeEvent(event)
        
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTabWidget, QLabel, QPushButton, QProgressBar,
                             QCheckBox, QMessageBox, QScrollArea, QListWidgetItem,
                             QGroupBox, QComboBox, QTextEdit)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool, Signal
import humanize
from datetime import datetime
import concurrent.futures
import threading
import subprocess

from ..utils.app_utils import AppUtils
from ..utils.error_utils import ErrorLogger
from ..utils.debug_utils import DebugLogger
from ..utils.adb_utils import ADBUtils
from ..utils.error_codes import ErrorCode

class AppListItem(QListWidgetItem):
    """Custom list item for app list"""
    def __init__(self, name: str, package: str):
        super().__init__(name)
        self.package_name = package
        self.setData(Qt.UserRole, package)

class AppTabSignals(QObject):
    """Signals for AppTab worker threads"""
    apps_ready = Signal(dict)  # {'user': user_apps, 'system': system_apps}
    error = Signal(str)  # Error message
    device_state = Signal(bool, str)  # Connected, Device ID
    progress = Signal(str)  # Progress message

class AppTabWorker(QRunnable):
    """Worker thread for AppTab operations"""
    
    def __init__(self, adb_utils, debug_logger, error_logger):
        super().__init__()
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.signals = AppTabSignals()
        
    def fetch_apps(self, user_only: bool = True, system_only: bool = False):
        """Fetch installed apps in background"""
        try:
            self.signals.progress.emit("Fetching installed apps...")
            
            # Check device connection first
            devices = self.adb_utils.get_connected_devices()
            if not devices:
                self.error_logger.log_error(
                    "No device connected",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("No device connected. Please connect a device and try again.")
                return
                
            ready_devices = [d for d in devices if d['state'] == 'device']
            if not ready_devices:
                self.error_logger.log_error(
                    "Device not in ready state",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                self.signals.error.emit("Device not ready. Please check USB debugging is enabled.")
                return
                
            # Fetch apps based on filters
            apps = {}
            if user_only or not system_only:
                success, user_apps = self.adb_utils.get_installed_apps(system_apps=False)
                if success:
                    apps['user'] = user_apps
                    self.debug_logger.log_debug(
                        f"Found {len(user_apps)} user apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch user apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if system_only or not user_only:
                success, system_apps = self.adb_utils.get_installed_apps(system_apps=True)
                if success:
                    apps['system'] = system_apps
                    self.debug_logger.log_debug(
                        f"Found {len(system_apps)} system apps",
                        "apps",
                        "info"
                    )
                else:
                    self.error_logger.log_error(
                        "Failed to fetch system apps",
                        ErrorCode.APP_LIST_REFRESH_FAILED
                    )
                    
            if not apps:
                self.signals.error.emit("Failed to fetch any apps. Check device connection and try again.")
                return
                
            self.signals.apps_ready.emit(apps)
            
        except FileNotFoundError as e:
            error_msg = "ADB not found. Please ensure Android SDK platform-tools are installed and in your PATH."
            self.error_logger.log_error(error_msg, ErrorCode.ADB_NOT_FOUND)
            self.signals.error.emit(error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"ADB command failed: {e.stderr.strip() if e.stderr else str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.ADB_COMMAND_FAILED)
            self.signals.error.emit(error_msg)
            
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out. Check device connection and try again."
            self.error_logger.log_error(error_msg, ErrorCode.COMMAND_TIMEOUT)
            self.signals.error.emit(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.error_logger.log_error(error_msg, ErrorCode.UNKNOWN_ERROR)
            self.signals.error.emit(error_msg)
            
class AppTab(QWidget):
    update_ui_signal = pyqtSignal(object)
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        """Initialize AppTab"""
        super().__init__()
        
        # Store loggers
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Initialize worker thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.workers = []
        
        # Connect UI update signal
        self.update_ui_signal.connect(lambda func: func())
        
        # Initialize ADBUtils with loggers
        try:
            self.adb_utils = ADBUtils(debug_logger, error_logger)
            
            # Connect signals
            if self.adb_utils:
                # Debug logging
                if self.adb_utils.debug_logger:
                    self.adb_utils.debug_logger.add_listener(self._on_debug_entry)
                    
                # Device state changes
                self.adb_utils.device_state_changed.connect(self._on_device_state_changed)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to initialize ADBUtils: {str(e)}")
            self.adb_utils = None
            
        # Initialize UI
        self._init_ui()
        
        # Setup refresh timers
        self.setup_refresh_timers()
        
        # Initial refresh if device connected
        if self.adb_utils and self.adb_utils.adb_ready:
            self.refresh_app_list(silent=True)
            
    def _init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Checking device status...")
        self.status_label.setStyleSheet("color: gray")
        status_layout.addWidget(self.status_label)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.clicked.connect(self.refresh_app_list)
        status_layout.addWidget(self.refresh_btn)
        
        # Auto refresh checkbox
        self.auto_refresh = QCheckBox("Auto Refresh")
        self.auto_refresh.setEnabled(False)
        self.auto_refresh.stateChanged.connect(self._on_auto_refresh_changed)
        status_layout.addWidget(self.auto_refresh)
        
        # Show system apps checkbox
        self.show_system_apps = QCheckBox("Show System Apps")
        self.show_system_apps.setEnabled(False)
        self.show_system_apps.stateChanged.connect(self._on_show_system_apps_changed)
        status_layout.addWidget(self.show_system_apps)
        
        layout.addLayout(status_layout)
        
        # App list
        self.app_list = QListWidget()
        self.app_list.itemSelectionChanged.connect(self._on_app_selected)
        layout.addWidget(self.app_list)
        
        # App details
        details_group = QGroupBox("App Details")
        details_layout = QVBoxLayout()
        
        # Memory usage
        self.memory_label = QLabel("Memory Usage: N/A")
        details_layout.addWidget(self.memory_label)
        
        # Analytics
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        self.analytics_text.setMinimumHeight(100)
        details_layout.addWidget(self.analytics_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        self.setLayout(layout)
        
    def _on_device_state_changed(self, connected: bool):
        """Handle device connection state change"""
        # Update UI elements
        self.refresh_btn.setEnabled(connected)
        self.auto_refresh.setEnabled(connected)
        self.show_system_apps.setEnabled(connected)
        
        # Update status
        if connected:
            self.status_label.setText("Device connected")
            self.status_label.setStyleSheet("color: green")
            self.refresh_app_list(silent=True)
        else:
            self.status_label.setText("No device connected")
            self.status_label.setStyleSheet("color: red")
            self.app_list.clear()
            self.details_text.clear()

    def _on_debug_entry(self, message: str, level: str, category: str):
        """Handle debug log entry"""
        # Update status label if it's a device status message
        if category == 'device':
            self.status_label.setText(message)
            if level == 'error':
                self.status_label.setStyleSheet("color: red")
            elif level == 'warning':
                self.status_label.setStyleSheet("color: orange")
            else:
                self.status_label.setStyleSheet("color: green")

    def _on_error(self, error_msg: str):
        """Handle error from worker thread"""
        self.error_logger.log_error(error_msg)
        QMessageBox.critical(self, "Error", error_msg)

    def setup_refresh_timers(self):
        """Set up refresh timers"""
        # App list refresh timer
        self.app_refresh_timer = QTimer()
        self.app_refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.app_refresh_timer.start(5000)  # Every 5 seconds
        
        # Memory refresh timer
        self.memory_refresh_timer = QTimer()
        self.memory_refresh_timer.timeout.connect(self._refresh_memory)
        self.memory_refresh_timer.start(2000)  # Every 2 seconds
        
    def refresh_app_list(self, silent=False):
        """Refresh the app list"""
        worker = AppTabWorker(self.adb_utils, self.debug_logger, self.error_logger)
        worker.signals.apps_ready.connect(self._handle_apps_ready)
        worker.signals.error.connect(self._handle_error)
        worker.signals.progress.connect(self._handle_progress)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)
        
    def _handle_apps_ready(self, apps: dict):
        """Handle apps fetched from worker thread"""
        try:
            self.app_list.clear()
            
            # Add user apps
            if 'user' in apps:
                user_apps = apps['user']
                self._add_apps_to_list("User Apps", user_apps)
                
            # Add system apps
            if 'system' in apps:
                system_apps = apps['system']
                self._add_apps_to_list("System Apps", system_apps)
                
            self.debug_logger.log_debug(
                f"Updated app list with {len(apps.get('user', []))} user apps and {len(apps.get('system', []))} system apps",
                "ui",
                "info"
            )
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to update app list: {str(e)}",
                ErrorCode.UI_UPDATE_FAILED
            )
            
    def _handle_error(self, message: str):
        """Handle error from worker thread"""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: red")
        
    def _handle_progress(self, message: str):
        """Handle progress update from worker thread"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("")
        
    def _add_apps_to_list(self, title: str, apps: list):
        """Add apps to list widget"""
        for app in apps:
            item = QListWidgetItem()
            item.setText(f"{app['name']} ({app['package']})")
            item.setData(Qt.UserRole, app['package'])
            
            if app.get('system', False):
                item.setForeground(QBrush(QColor('gray')))
                
            self.app_list.addItem(item)
            
    def _refresh_memory(self):
        """Refresh memory info for selected app"""
        if not self.adb_utils:
            QMessageBox.warning(self, "Warning", "ADBUtils not initialized")
            return
            
        try:
            item = self.app_list.currentItem()
            if item:
                self._on_selection_changed()
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to refresh memory: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to refresh memory: {str(e)}")
            
    def _update_memory_info(self):
        """Update memory information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                memory_info = self.adb_utils.get_memory_info(package)
                if memory_info:
                    self.memory_info_label.setText(f"Memory Usage: {memory_info['total_mb']:.1f} MB")
        except Exception as e:
            self.error_logger.log_error(f"Failed to update memory info: {str(e)}")
            
    def _update_analytics(self):
        """Update analytics information safely"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                # Use ThreadPoolExecutor for analytics updates
                self.executor.submit(self._fetch_analytics, package)
        except Exception as e:
            self.error_logger.log_error(f"Failed to update analytics: {str(e)}")
    
    def _fetch_analytics(self, package: str):
        """Fetch analytics data in background"""
        try:
            # Get analytics data
            analytics = self.adb_utils.get_app_analytics(package)
            if not analytics:
                return
                
            # Update UI in main thread using signals
            self.cpu_label.setText(f"CPU Usage: {analytics.get('cpu_usage', 0):.1f}%")
            self.battery_label.setText(f"Battery Drain: {analytics.get('battery_drain', 0):.1f}%/hr")
            
            # Network usage
            rx_bytes = analytics.get('network', {}).get('rx_bytes', 0)
            tx_bytes = analytics.get('network', {}).get('tx_bytes', 0)
            rx_mb = rx_bytes / (1024 * 1024)
            tx_mb = tx_bytes / (1024 * 1024)
            
            self.rx_label.setText(f"Received: {rx_mb:.1f} MB")
            self.tx_label.setText(f"Transmitted: {tx_mb:.1f} MB")
            
            # Storage usage
            storage = analytics.get('storage', {})
            app_mb = storage.get('app_size', 0) / (1024 * 1024)
            data_mb = storage.get('data_size', 0) / (1024 * 1024)
            
            self.app_size_label.setText(f"App Size: {app_mb:.1f} MB")
            self.data_size_label.setText(f"Data Size: {data_mb:.1f} MB")
            self.total_size_label.setText(f"Total Size: {app_mb + data_mb:.1f} MB")
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to fetch analytics: {str(e)}")
            
    def _on_selection_changed(self):
        """Handle app selection"""
        try:
            items = self.app_list.selectedItems()
            if not items:
                self.memory_label.setText("Memory Usage: N/A")
                self.analytics_text.clear()
                return
                
            # Get selected package
            package = items[0].data(Qt.UserRole)
            if not package:
                return
                
            # Update status
            self.status_label.setText(f"Loading details for {package}...")
            self.status_label.setStyleSheet("color: blue")
            
            # Get memory info
            memory = self.adb_utils.get_memory_info(package)
            if memory:
                total = humanize.naturalsize(memory.get('total_memory', 0))
                self.memory_label.setText(f"Memory Usage: {total}")
            else:
                self.memory_label.setText("Memory Usage: N/A")
                
            # Get analytics
            analytics = self.adb_utils.get_app_analytics(package)
            if analytics:
                # Format analytics text
                lines = []
                
                # CPU
                cpu = analytics.get('cpu', 0)
                lines.append(f"CPU Usage: {cpu:.1f}%")
                
                # Memory breakdown
                if 'memory' in analytics:
                    mem = analytics['memory']
                    lines.extend([
                        "\nMemory Breakdown:",
                        f"  Java Heap: {humanize.naturalsize(mem.get('java', 0))}",
                        f"  Native Heap: {humanize.naturalsize(mem.get('native', 0))}",
                        f"  Code: {humanize.naturalsize(mem.get('code', 0))}",
                        f"  Stack: {humanize.naturalsize(mem.get('stack', 0))}",
                        f"  Graphics: {humanize.naturalsize(mem.get('graphics', 0))}"
                    ])
                
                # Battery
                battery = analytics.get('battery', 0)
                lines.append(f"\nBattery Usage: {battery:.1f}%")
                
                # Network
                rx = humanize.naturalsize(analytics.get('rx_bytes', 0))
                tx = humanize.naturalsize(analytics.get('tx_bytes', 0))
                lines.append(f"\nNetwork Traffic:")
                lines.append(f"  Received: {rx}")
                lines.append(f"  Sent: {tx}")
                
                # Update text
                self.analytics_text.setText('\n'.join(lines))
                
                # Update status
                self.status_label.setText("Details loaded")
                self.status_label.setStyleSheet("color: green")
            else:
                self.analytics_text.setText("No analytics available")
                self.status_label.setText("Could not load details")
                self.status_label.setStyleSheet("color: orange")
                
        except Exception as e:
            error_msg = f"Failed to update app details: {str(e)}"
            self.error_logger.log_error(error_msg)
            self.debug_logger.log_debug(error_msg, "app_select", "error")
            
            self.status_label.setText("Error: Failed to load details")
            self.status_label.setStyleSheet("color: red")
            
    def _check_adb_status(self):
        """Check ADB status and update UI accordingly"""
        if not self.adb_utils:
            return
            
        def check_worker():
            try:
                if self.adb_utils.check_adb_status():
                    # ADB is ready, try to refresh app list
                    self._refresh_app_list()
                else:
                    # Update UI in main thread
                    self.update_ui_signal.emit(lambda: self._update_no_device_ui())
            except Exception as e:
                self.error_logger.log_error(f"Error checking device status: {str(e)}")
                
        # Run in worker thread
        self.executor.submit(check_worker)
        
    def _update_no_device_ui(self):
        """Update UI when no device is connected"""
        self.app_list.clear()
        self.app_list.addItem("No device connected")
        self.status_label.setText("No device connected")
        self.status_label.setStyleSheet("color: red")
        self.refresh_btn.setEnabled(False)
        self.auto_refresh.setEnabled(False)
        self.show_system_apps.setEnabled(False)
        
    def _refresh_app_list(self):
        """Refresh app list silently"""
        if not self.adb_utils or not self.adb_utils.adb_ready:
            return
            
        # Use a worker thread for app list refresh
        def refresh_worker():
            try:
                apps = self.adb_utils.get_installed_apps()
                # Update UI in main thread
                if apps:
                    self.app_list.clear()
                    for app in apps:
                        name = app.get('name', app['package'])
                        package = app['package']
                        
                        # If name is same as package, try to make it more readable
                        if name == package:
                            name = package.split('.')[-1].replace('_', ' ').title()
                        
                        item = AppListItem(name, package)
                        if app.get('system', False):
                            item.setForeground(Qt.gray)
                        self.app_list.addItem(item)
            except Exception as e:
                self.error_logger.log_error(f"Failed to refresh app list: {str(e)}")
        
        # Run in worker thread
        self.executor.submit(refresh_worker)
    
    def _on_auto_refresh_changed(self, state: int):
        """Handle auto refresh checkbox state change"""
        if state == Qt.Checked:
            self.setup_refresh_timers()
        else:
            self.stop_refresh_timers()
            
    def setup_refresh_timers(self):
        """Setup refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(lambda: self.refresh_app_list(silent=True))
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def stop_refresh_timers(self):
        """Stop refresh timers"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
            
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.executor.shutdown(wait=False)
        for worker in self.workers:
            worker.quit()
            worker.wait()
        super().closeEvent(event)
        
>>>>>>> parent of 5c1894b (all current bugs fixed)
    def _on_show_system_apps_changed(self, state: int):
        """Handle show system apps checkbox state change"""
        if self.adb_utils:
            self.adb_utils.include_system_apps = (state == Qt.Checked)
            self.refresh_app_list()
            
    def _on_app_selected(self):
        """Handle app selection change"""
        selected_items = self.app_list.selectedItems()
        if not selected_items:
            self.details_text.clear()
            return
            
        item = selected_items[0]
        package = item.package_name
        
        # Start worker thread to get app details
        worker = AppTabWorker(self.adb_utils, self.debug_logger, self.error_logger)
        worker.signals.apps_ready.connect(self._on_app_details_received)
        worker.signals.error.connect(self._on_error)
        worker.fetch_apps(user_only=False, system_only=False)
        self.threadpool = QThreadPool()
        self.threadpool.start(worker)
        
    def _on_app_details_received(self, apps: dict):
        """Handle app details received"""
        if not apps:
            self.details_text.clear()
            return
            
        # Format details
        text = f"Package: {apps.get('package_name', 'Unknown')}\n"
        text += f"Version: {apps.get('version', 'Unknown')}\n"
        text += f"Install time: {apps.get('install_time', 'Unknown')}\n"
        text += f"Last updated: {apps.get('last_updated', 'Unknown')}\n"
        text += f"Size: {humanize.naturalsize(apps.get('size', 0))}\n\n"
        
        # Add permissions
        text += "Permissions:\n"
        for perm in apps.get('permissions', []):
            text += f"- {perm}\n"
            
        self.details_text.setText(text)
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
