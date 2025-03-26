from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTabWidget, QLabel, QPushButton, QProgressBar,
                             QCheckBox, QMessageBox, QScrollArea, QListWidgetItem,
                             QGroupBox, QComboBox, QTextEdit)
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import humanize
from datetime import datetime
import concurrent.futures
import threading

from ..utils.app_utils import AppUtils
from ..utils.error_utils import ErrorLogger
from ..utils.debug_utils import DebugLogger

class AppListItem(QListWidgetItem):
    """Custom list item for app list"""
    def __init__(self, name: str, package: str):
        super().__init__(name)
        self.package_name = package
        self.setData(Qt.UserRole, package)

class AdbWorker(QThread):
    """Worker thread for ADB operations"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.operation(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

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
        
        # Initialize AppUtils with loggers
        try:
            self.app_utils = AppUtils(debug_logger, error_logger)
            
            # Connect signals
            if self.app_utils:
                # Debug logging
                if self.app_utils.debug_logger:
                    self.app_utils.debug_logger.add_listener(self._on_debug_entry)
                    
                # Device state changes
                self.app_utils.device_state_changed.connect(self._on_device_state_changed)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to initialize AppUtils: {str(e)}")
            self.app_utils = None
            
        # Initialize UI
        self._init_ui()
        
        # Setup refresh timers
        self.setup_refresh_timers()
        
        # Initial refresh if device connected
        if self.app_utils and self.app_utils.adb_ready:
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
        try:
            if not silent:
                self.status_label.setText("Refreshing app list...")
                self.status_label.setStyleSheet("color: blue")
                
            # Clear current list
            self.app_list.clear()
            
            # Get apps
            apps = self.app_utils.get_installed_apps(force_refresh=True)
            
            # Add to list
            for app in apps:
                item = QListWidgetItem()
                item.setText(f"{app['name']} ({app['package']})")
                item.setData(Qt.UserRole, app['package'])
                
                if app.get('system', False):
                    item.setForeground(QBrush(QColor('gray')))
                    
                self.app_list.addItem(item)
                
            # Update status
            count = len(apps)
            if not silent:
                self.status_label.setText(f"Found {count} apps")
                self.status_label.setStyleSheet("color: green")
                
            self.debug_logger.log_debug(f"Refreshed app list - {count} apps", "refresh", "info")
            
        except Exception as e:
            error_msg = f"Failed to refresh app list: {str(e)}"
            self.error_logger.log_error(error_msg)
            self.debug_logger.log_debug(error_msg, "refresh", "error")
            
            if not silent:
                self.status_label.setText("Error: Failed to refresh apps")
                self.status_label.setStyleSheet("color: red")
                
    def _refresh_memory(self):
        """Refresh memory info for selected app"""
        if not self.app_utils:
            QMessageBox.warning(self, "Warning", "AppUtils not initialized")
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
        if not self.app_utils or not self.app_utils.adb_ready:
            return
            
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        try:
            package = current_item.data(Qt.UserRole)
            if package:
                memory_info = self.app_utils.get_memory_info(package)
                if memory_info:
                    self.memory_info_label.setText(f"Memory Usage: {memory_info['total_mb']:.1f} MB")
        except Exception as e:
            self.error_logger.log_error(f"Failed to update memory info: {str(e)}")
            
    def _update_analytics(self):
        """Update analytics information safely"""
        if not self.app_utils or not self.app_utils.adb_ready:
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
            analytics = self.app_utils.get_app_analytics(package)
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
            memory = self.app_utils.get_memory_info(package)
            if memory:
                total = humanize.naturalsize(memory.get('total_memory', 0))
                self.memory_label.setText(f"Memory Usage: {total}")
            else:
                self.memory_label.setText("Memory Usage: N/A")
                
            # Get analytics
            analytics = self.app_utils.get_app_analytics(package)
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
        if not self.app_utils:
            return
            
        def check_worker():
            try:
                if self.app_utils.check_adb_status():
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
        if not self.app_utils or not self.app_utils.adb_ready:
            return
            
        # Use a worker thread for app list refresh
        def refresh_worker():
            try:
                apps = self.app_utils.get_installed_apps()
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
        
    def _on_show_system_apps_changed(self, state: int):
        """Handle show system apps checkbox state change"""
        if self.app_utils:
            self.app_utils.include_system_apps = (state == Qt.Checked)
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
        worker = AdbWorker(self.app_utils.get_app_details, package)
        worker.finished.connect(self._on_app_details_received)
        worker.error.connect(self._on_error)
        worker.start()
        
    def _on_app_details_received(self, details):
        """Handle app details received"""
        if not details:
            self.details_text.clear()
            return
            
        # Format details
        text = f"Package: {details.get('package_name', 'Unknown')}\n"
        text += f"Version: {details.get('version', 'Unknown')}\n"
        text += f"Install time: {details.get('install_time', 'Unknown')}\n"
        text += f"Last updated: {details.get('last_updated', 'Unknown')}\n"
        text += f"Size: {humanize.naturalsize(details.get('size', 0))}\n\n"
        
        # Add permissions
        text += "Permissions:\n"
        for perm in details.get('permissions', []):
            text += f"- {perm}\n"
            
        self.details_text.setText(text)
