from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QTabWidget, QLabel, QPushButton, QProgressBar,
                             QCheckBox, QMessageBox, QScrollArea, QListWidgetItem,
                             QGroupBox, QComboBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
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
    finished = Signal(object)
    error = Signal(str)
    
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
    def __init__(self):
        """Initialize AppTab"""
        super().__init__()
        
        # Initialize loggers first
        self.error_logger = ErrorLogger()
        self.debug_logger = DebugLogger()
        
        # Initialize AppUtils after loggers
        try:
            self.app_utils = AppUtils()
            
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
        self.setup_ui()
        
        # Setup refresh timers
        self.setup_refresh_timers()
        
        # Initial refresh if device connected
        if self.app_utils and self.app_utils.adb_ready:
            self.refresh_app_list(silent=True)
            
    def _on_device_state_changed(self, connected):
        """Handle device connection state changes"""
        try:
            if connected:
                # Device connected - refresh everything
                self.debug_logger.log_debug("Device connected - refreshing", "device_state", "info")
                self.refresh_app_list(silent=True)
                self._refresh_memory()
                
                # Show status
                self.status_label.setText("Device Connected")
                self.status_label.setStyleSheet("color: green")
                
                # Enable controls
                self.refresh_btn.setEnabled(True)
                self.auto_refresh.setEnabled(True)
                self.show_system_apps.setEnabled(True)
            else:
                # Device disconnected - clear data
                self.debug_logger.log_debug("Device disconnected", "device_state", "warning")
                self.app_list.clear()
                self.memory_label.setText("Memory Usage: N/A")
                self.analytics_text.clear()
                
                # Show status
                self.status_label.setText("No Device Connected")
                self.status_label.setStyleSheet("color: orange")
                
                # Disable controls
                self.refresh_btn.setEnabled(False)
                self.auto_refresh.setEnabled(False)
                self.show_system_apps.setEnabled(False)
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to handle device state change: {str(e)}")
            
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Checking Device...")
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)
        
        # App list group
        app_group = QGroupBox("Installed Apps")
        app_layout = QVBoxLayout(app_group)
        
        # Controls
        controls = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(lambda: self.refresh_app_list(silent=False))
        controls.addWidget(self.refresh_btn)
        
        # Auto refresh checkbox
        self.auto_refresh = QCheckBox("Auto Refresh")
        self.auto_refresh.setChecked(True)
        controls.addWidget(self.auto_refresh)
        
        app_layout.addLayout(controls)
        
        # App list
        self.app_list = QListWidget()
        self.app_list.itemClicked.connect(self._on_app_selected)
        app_layout.addWidget(self.app_list)
        
        layout.addWidget(app_group)
        
        # App details group
        details_group = QGroupBox("App Details")
        details_layout = QVBoxLayout(details_group)
        
        # Memory info
        memory_layout = QHBoxLayout()
        self.memory_label = QLabel("Memory Usage: N/A")
        memory_layout.addWidget(self.memory_label)
        
        # Refresh memory button
        self.refresh_memory_btn = QPushButton("Refresh Memory")
        self.refresh_memory_btn.clicked.connect(self._refresh_memory)
        memory_layout.addWidget(self.refresh_memory_btn)
        
        details_layout.addLayout(memory_layout)
        
        # Analytics
        analytics_layout = QVBoxLayout()
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        analytics_layout.addWidget(self.analytics_text)
        
        details_layout.addLayout(analytics_layout)
        
        layout.addWidget(details_group)
        
        # Debug group
        debug_group = QGroupBox("Debug Log")
        debug_layout = QVBoxLayout(debug_group)
        
        # Debug text
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        debug_layout.addWidget(self.debug_text)
        
        # Clear debug button
        clear_debug_btn = QPushButton("Clear Log")
        clear_debug_btn.clicked.connect(self.clear_debug_log)
        debug_layout.addWidget(clear_debug_btn)
        
        layout.addWidget(debug_group)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        self.show_system_apps = QCheckBox("Show System Apps")
        self.show_system_apps.stateChanged.connect(lambda: self.refresh_app_list())
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(lambda: self.refresh_app_list())
        
        controls_layout.addWidget(self.show_system_apps)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()
        
        # Loading label
        self.loading_label = QLabel("Loading apps...")
        self.loading_label.hide()
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.hide()
        
        # Details area
        self.details_tabs = QTabWidget()
        
        # Basic info tab
        basic_info = QWidget()
        basic_layout = QVBoxLayout(basic_info)
        self.app_info_label = QLabel()
        basic_layout.addWidget(self.app_info_label)
        self.details_tabs.addTab(basic_info, "Basic Info")
        
        # Memory usage tab
        memory_widget = QWidget()
        memory_layout = QVBoxLayout(memory_widget)
        self.memory_info_label = QLabel()
        memory_layout.addWidget(self.memory_info_label)
        self.details_tabs.addTab(memory_widget, "Memory Usage")
        
        # Analytics tab
        analytics_widget = QWidget()
        analytics_layout = QVBoxLayout(analytics_widget)
        
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.battery_label = QLabel("Battery Drain: 0%/hr")
        self.rx_label = QLabel("Received: 0 KB")
        self.tx_label = QLabel("Transmitted: 0 KB")
        self.app_size_label = QLabel("App Size: 0 MB")
        self.data_size_label = QLabel("Data Size: 0 MB")
        self.total_size_label = QLabel("Total Size: 0 MB")
        
        analytics_layout.addWidget(self.cpu_label)
        analytics_layout.addWidget(self.battery_label)
        analytics_layout.addWidget(self.rx_label)
        analytics_layout.addWidget(self.tx_label)
        analytics_layout.addWidget(self.app_size_label)
        analytics_layout.addWidget(self.data_size_label)
        analytics_layout.addWidget(self.total_size_label)
        analytics_layout.addStretch()
        
        self.details_tabs.addTab(analytics_widget, "Analytics")
        
        # Debug tab
        debug_widget = QWidget()
        debug_layout = QVBoxLayout(debug_widget)
        
        self.auto_refresh = QCheckBox("Auto Refresh")
        self.auto_refresh.setChecked(True)
        
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        
        self.clear_log = QPushButton("Clear Log")
        self.clear_log.clicked.connect(self.clear_debug_log)
        
        debug_layout.addWidget(self.auto_refresh)
        debug_layout.addWidget(self.debug_text)
        debug_layout.addWidget(self.clear_log)
        
        self.details_tabs.addTab(debug_widget, "Debug")
        
        # Add widgets to main layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.error_label)
        layout.addWidget(self.app_list, stretch=1)
        layout.addWidget(self.details_tabs, stretch=1)
        
        # Thread pool for background tasks
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
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
        
    def show_error(self, message: str):
        """Show error message in the UI"""
        self.error_label.setText(message)
        self.error_label.show()
        
    def update_refresh_status(self, status: str):
        """Update the refresh status indicator"""
        self.refresh_status.setText(status)
        QTimer.singleShot(2000, lambda: self.refresh_status.clear())
    
    def refresh_app_list(self, silent=False):
        """Refresh the list of installed apps"""
        if not self.app_utils:
            if not silent:
                QMessageBox.warning(self, "Warning", "AppUtils not initialized")
            return
            
        try:
            if not silent:
                self.refresh_btn.setEnabled(False)
                self.refresh_btn.setText("Refreshing...")
                
            # Get app list
            apps = self.app_utils.get_installed_apps(
                system_apps=self.show_system_apps.isChecked(),
                force_refresh=not silent
            )
            
            # Update list widget
            self.app_list.clear()
            
            # Sort apps by name
            apps = sorted(apps, key=lambda x: x['name'].lower())
            
            for app in apps:
                name = app['name']
                package = app['package']
                
                # Create list item
                item = QListWidgetItem()
                item.setText(f"{name}\n{package}")
                item.setData(Qt.UserRole, package)
                
                # Style system apps differently
                if app.get('system', False):
                    item.setForeground(Qt.gray)
                
                self.app_list.addItem(item)
                
            # Update status
            if apps:
                self.status_label.setText(f"Found {len(apps)} apps")
            else:
                self.status_label.setText("No apps found")
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to refresh app list: {str(e)}")
            if not silent:
                QMessageBox.warning(self, "Error", f"Failed to refresh app list: {str(e)}")
                
        finally:
            if not silent:
                self.refresh_btn.setEnabled(True)
                self.refresh_btn.setText("Refresh")
                
    def _on_app_selected(self, item):
        """Handle app selection"""
        if not self.app_utils or not item:
            return
            
        try:
            # Get package name
            package = item.data(Qt.UserRole)
            if not package:
                return
                
            # Get app info
            self.debug_logger.log_debug(f"Getting info for {package}", "app_select", "info")
            
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
                        "Memory Breakdown:",
                        f"  Java Heap: {humanize.naturalsize(mem.get('java', 0))}",
                        f"  Native Heap: {humanize.naturalsize(mem.get('native', 0))}",
                        f"  Code: {humanize.naturalsize(mem.get('code', 0))}",
                        f"  Stack: {humanize.naturalsize(mem.get('stack', 0))}",
                        f"  Graphics: {humanize.naturalsize(mem.get('graphics', 0))}"
                    ])
                
                # Battery
                battery = analytics.get('battery', 0)
                lines.append(f"Battery Usage: {battery:.1f}%")
                
                # Network
                rx = humanize.naturalsize(analytics.get('rx_bytes', 0))
                tx = humanize.naturalsize(analytics.get('tx_bytes', 0))
                lines.append(f"Network: ↓{rx} ↑{tx}")
                
                # Update text
                self.analytics_text.setText('\n'.join(lines))
            else:
                self.analytics_text.setText("No analytics available")
                
        except Exception as e:
            self.error_logger.log_error(f"Failed to get app details: {str(e)}")
            self.debug_logger.log_debug(f"Failed to get app details: {str(e)}", "app_select", "error")
            
    def _refresh_memory(self):
        """Refresh memory info for selected app"""
        if not self.app_utils:
            QMessageBox.warning(self, "Warning", "AppUtils not initialized")
            return
            
        try:
            item = self.app_list.currentItem()
            if item:
                self._on_app_selected(item)
                
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
            
    def _on_debug_entry(self, entry):
        """Handle debug log entry"""
        if not self.auto_refresh.isChecked():
            return
            
        try:
            # Format entry
            timestamp = entry.get('timestamp', '')
            operation = entry.get('operation', '')
            status = entry.get('status', '')
            message = entry.get('message', '')
            
            # Create formatted message
            formatted_entry = f"{timestamp} [{status.upper()}] {operation}: {message}"
            
            # Add to debug text
            if hasattr(self, 'debug_text'):
                self.debug_text.append(formatted_entry)
                
        except Exception as e:
            if hasattr(self, 'error_logger'):
                self.error_logger.log_error(f"Failed to handle debug entry: {str(e)}")
    
    def clear_debug_log(self):
        """Clear the debug log"""
        try:
            self.debug_text.clear()
        except Exception as e:
            self.error_logger.log_error(f"Failed to clear debug log: {str(e)}")
    
    def _check_adb_status(self):
        """Check ADB status and update UI accordingly"""
        if self.app_utils:
            if self.app_utils.check_adb_status():
                # ADB is ready, try to refresh app list
                self._refresh_app_list()
            else:
                # Clear app list if ADB is not ready
                self.app_list.clear()
                self.app_list.addItem("No device connected")
                
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
    
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.executor.shutdown(wait=False)
        for worker in self.workers:
            worker.quit()
            worker.wait()
        super().closeEvent(event)
