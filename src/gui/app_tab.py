from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QMenu, QAction, QGroupBox,
    QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QCursor, QColor, QFont

from src.utils.adb_utils import ADBUtils
from src.utils.debug_utils import DebugLogger
from src.utils.error_utils import ErrorLogger, ErrorCode

class AppTabWorker(QThread):
    """Worker thread for fetching app data"""
    
    finished = pyqtSignal(list)  # Emits list of app info
    error = pyqtSignal(str)  # Emits error message
    progress = pyqtSignal(int)  # Emits progress value
    
    def __init__(self, adb_utils: ADBUtils):
        super().__init__()
        self.adb_utils = adb_utils
        self.include_system = False

    def run(self):
        """Fetch installed apps in background"""
        try:
            if not self.adb_utils.check_adb_status():
                self.error.emit("No device connected")
                return
                
            # Get list of packages
            packages = self.adb_utils.get_installed_apps(self.include_system)
            if not packages:
                self.error.emit("No apps found")
                return
                
            # Process each package
            apps = []
            total = len(packages)
            
            for i, package in enumerate(packages):
                try:
                    # Get app name
                    name = self.adb_utils.get_app_name(package) or package
                    
                    # Get app details
                    details = self.adb_utils.get_package_details(package)
                    
                    # Get memory info
                    memory = self.adb_utils.get_memory_info(package)
                    total_memory = memory.get('total_pss', 0) if memory else 0
                    
                    apps.append({
                        'name': name,
                        'package': package,
                        'memory': total_memory,
                        'is_stopped': details.get('is_stopped', False),
                        'is_disabled': details.get('is_disabled', False),
                        'is_suspended': details.get('is_suspended', False),
                        'version': details.get('version', 'Unknown'),
                        'target_sdk': details.get('target_sdk', 'Unknown')
                    })
                    
                    # Update progress
                    progress = int((i + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    continue  # Skip failed app
                    
            self.finished.emit(apps)
            
        except Exception as e:
            self.error.emit(str(e))

class AppDetailsWorker(QThread):
    """Worker thread for fetching app details"""
    
    finished = pyqtSignal(dict)  # Emits app details
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, adb_utils: ADBUtils, package: str):
        super().__init__()
        self.adb_utils = adb_utils
        self.package = package
        
    def run(self):
        """Fetch app details in background"""
        try:
            if not self.adb_utils.check_adb_status():
                self.error.emit("No device connected")
                return
                
            # Get all details
            details = self.adb_utils.get_package_details(self.package)
            crashes = self.adb_utils.get_app_crashes(self.package)
            resources = self.adb_utils.get_resource_usage(self.package)
            memory = self.adb_utils.get_memory_info(self.package)
            
            # Combine all info
            info = {
                'details': details,
                'crashes': crashes,
                'resources': resources,
                'memory': memory
            }
            
            self.finished.emit(info)
            
        except Exception as e:
            self.error.emit(str(e))

class AppTab(QWidget):
    """Tab for managing installed applications"""
    
    def __init__(self, adb_utils: ADBUtils, debug_logger: DebugLogger, error_logger: ErrorLogger):
        super().__init__()
        
        # Store utils
        self.adb_utils = adb_utils
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Initialize workers
        self.worker = None
        self.details_worker = None
        self.selected_package = None
        
        # Create update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_app_details)
        self.update_timer.setInterval(2000)  # Update every 2 seconds
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_apps)
        controls_layout.addWidget(self.refresh_button)
        
        self.system_apps_button = QPushButton("Show System Apps")
        self.system_apps_button.setCheckable(True)
        self.system_apps_button.clicked.connect(self.toggle_system_apps)
        controls_layout.addWidget(self.system_apps_button)
        
        controls_layout.addStretch()
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        controls_layout.addWidget(self.progress_bar)
        
        layout.addLayout(controls_layout)
        
        # Create split layout
        split_layout = QHBoxLayout()
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Package", "Version", "Status", "Memory"])
        
        # Set table properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Add context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect selection change
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        split_layout.addWidget(self.table, stretch=2)
        
        # Create details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Status group
        status_group = QGroupBox("Status")
        status_layout = QGridLayout()
        
        self.status_label = QLabel("Select an app to view details")
        status_layout.addWidget(self.status_label, 0, 0, 1, 2)
        
        self.stopped_label = QLabel("Force Stopped:")
        self.stopped_value = QLabel("N/A")
        status_layout.addWidget(self.stopped_label, 1, 0)
        status_layout.addWidget(self.stopped_value, 1, 1)
        
        self.disabled_label = QLabel("Disabled:")
        self.disabled_value = QLabel("N/A")
        status_layout.addWidget(self.disabled_label, 2, 0)
        status_layout.addWidget(self.disabled_value, 2, 1)
        
        self.suspended_label = QLabel("Suspended:")
        self.suspended_value = QLabel("N/A")
        status_layout.addWidget(self.suspended_label, 3, 0)
        status_layout.addWidget(self.suspended_value, 3, 1)
        
        status_group.setLayout(status_layout)
        details_layout.addWidget(status_group)
        
        # Resource group
        resource_group = QGroupBox("Resource Usage")
        resource_layout = QGridLayout()
        
        self.cpu_label = QLabel("CPU Usage:")
        self.cpu_value = QLabel("N/A")
        resource_layout.addWidget(self.cpu_label, 0, 0)
        resource_layout.addWidget(self.cpu_value, 0, 1)
        
        self.memory_label = QLabel("Memory Usage:")
        self.memory_value = QLabel("N/A")
        resource_layout.addWidget(self.memory_label, 1, 0)
        resource_layout.addWidget(self.memory_value, 1, 1)
        
        self.virtual_label = QLabel("Virtual Memory:")
        self.virtual_value = QLabel("N/A")
        resource_layout.addWidget(self.virtual_label, 2, 0)
        resource_layout.addWidget(self.virtual_value, 2, 1)
        
        resource_group.setLayout(resource_layout)
        details_layout.addWidget(resource_group)
        
        # Issues group
        issues_group = QGroupBox("Recent Issues")
        issues_layout = QGridLayout()
        
        self.crashes_label = QLabel("Recent Crashes:")
        self.crashes_value = QLabel("N/A")
        issues_layout.addWidget(self.crashes_label, 0, 0)
        issues_layout.addWidget(self.crashes_value, 0, 1)
        
        self.anrs_label = QLabel("Recent ANRs:")
        self.anrs_value = QLabel("N/A")
        issues_layout.addWidget(self.anrs_label, 1, 0)
        issues_layout.addWidget(self.anrs_value, 1, 1)
        
        issues_group.setLayout(issues_layout)
        details_layout.addWidget(issues_group)
        
        details_layout.addStretch()
        split_layout.addWidget(details_widget, stretch=1)
        
        layout.addLayout(split_layout)
        
        # Initial state
        self.handle_device_state_changed(False)

    def refresh_apps(self):
        """Refresh the list of installed apps"""
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Disable controls
        self.refresh_button.setEnabled(False)
        self.system_apps_button.setEnabled(False)
        
        # Clear table
        self.table.setRowCount(0)
        
        # Create and start worker
        if self.worker:
            self.worker.quit()
            
        self.worker = AppTabWorker(self.adb_utils)
        self.worker.include_system = self.system_apps_button.isChecked()
        
        # Connect signals
        self.worker.finished.connect(self.handle_apps_loaded)
        self.worker.error.connect(self.handle_error)
        self.worker.progress.connect(self.progress_bar.setValue)
        
        # Start worker
        self.worker.start()

    def handle_apps_loaded(self, apps: List[Dict]):
        """Handle loaded app data"""
        # Update table
        self.table.setRowCount(len(apps))
        
        for i, app in enumerate(apps):
            try:
                # App name
                name_item = QTableWidgetItem(app.get('name', 'Unknown'))
                if app.get('is_disabled', False):
                    name_item.setForeground(QColor('gray'))
                elif app.get('is_suspended', False):
                    name_item.setForeground(QColor('darkgray'))
                self.table.setItem(i, 0, name_item)
                
                # Package name
                package_item = QTableWidgetItem(app.get('package', ''))
                self.table.setItem(i, 1, package_item)
                
                # Version
                version_item = QTableWidgetItem(str(app.get('version', 'Unknown')))
                self.table.setItem(i, 2, version_item)
                
                # Status
                status_text = []
                if app.get('is_disabled', False):
                    status_text.append("Disabled")
                elif app.get('is_suspended', False):
                    status_text.append("Suspended")
                else:
                    status_text.append("Enabled")
                    
                if app.get('is_stopped', False):
                    status_text.append("Stopped")
                    
                status_item = QTableWidgetItem(", ".join(status_text))
                if app.get('is_disabled', False):
                    status_item.setForeground(QColor('red'))
                elif app.get('is_suspended', False):
                    status_item.setForeground(QColor('orange'))
                elif app.get('is_stopped', False):
                    status_item.setForeground(QColor('darkred'))
                self.table.setItem(i, 3, status_item)
                
                # Memory usage (format as MB)
                try:
                    memory_mb = float(app.get('memory', 0)) / 1024.0  # Convert KB to MB
                except (TypeError, ValueError):
                    memory_mb = 0.0
                memory_item = QTableWidgetItem(f"{memory_mb:.1f} MB")
                memory_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 4, memory_item)
                
            except Exception as e:
                self.error_logger.log_error(
                    f"Error displaying app info: {str(e)}",
                    ErrorCode.UNKNOWN,
                    {"app": str(app)}
                )
                continue
            
        # Hide progress and enable controls
        self.progress_bar.hide()
        self.refresh_button.setEnabled(True)
        self.system_apps_button.setEnabled(True)
        
        # Log success
        self.debug_logger.log_debug(
            f"Loaded {len(apps)} apps",
            "app",
            "info"
        )

    def handle_error(self, error: str):
        """Handle worker error"""
        # Hide progress and enable controls
        self.progress_bar.hide()
        self.refresh_button.setEnabled(True)
        self.system_apps_button.setEnabled(True)
        
        # Show error
        QMessageBox.warning(self, "Error", error)
        
        # Log error
        self.error_logger.log_error(
            f"Failed to load apps: {error}",
            ErrorCode.PACKAGE_NOT_FOUND
        )

    def toggle_system_apps(self):
        """Toggle system apps visibility"""
        self.refresh_apps()

    def show_context_menu(self, position):
        """Show context menu for selected app"""
        # Get selected row
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        # Get package info
        package = self.table.item(row, 1).text()
        is_disabled = "Disabled" in self.table.item(row, 3).text()
        is_suspended = "Suspended" in self.table.item(row, 3).text()
            
        # Create menu
        menu = QMenu()
        
        # Add actions
        clear_data = QAction("Clear App Data", self)
        clear_data.triggered.connect(lambda: self.clear_app_data(row))
        menu.addAction(clear_data)
        
        force_stop = QAction("Force Stop", self)
        force_stop.triggered.connect(lambda: self.force_stop_app(row))
        menu.addAction(force_stop)
        
        # Add enable/disable action
        toggle_enabled = QAction("Enable" if is_disabled else "Disable", self)
        toggle_enabled.triggered.connect(lambda: self.toggle_app_enabled(row))
        menu.addAction(toggle_enabled)
        
        toggle_suspended = QAction("Resume" if is_suspended else "Suspend", self)
        toggle_suspended.triggered.connect(lambda: self.toggle_app_suspended(row))
        menu.addAction(toggle_suspended)
        
        menu.addSeparator()
        
        uninstall = QAction("Uninstall", self)
        uninstall.triggered.connect(lambda: self.uninstall_app(row))
        menu.addAction(uninstall)
        
        # Show menu
        menu.exec_(QCursor.pos())

    def clear_app_data(self, row: int):
        """Clear data for selected app"""
        package = self.table.item(row, 1).text()
        if self.adb_utils.clear_app_data(package):
            QMessageBox.information(self, "Success", "App data cleared successfully")
            self._update_app_details()
        else:
            QMessageBox.warning(self, "Error", "Failed to clear app data")

    def force_stop_app(self, row: int):
        """Force stop selected app"""
        package = self.table.item(row, 1).text()
        if self.adb_utils.force_stop_app(package):
            QMessageBox.information(self, "Success", "App force stopped successfully")
            self._update_app_details()
        else:
            QMessageBox.warning(self, "Error", "Failed to force stop app")

    def uninstall_app(self, row: int):
        """Uninstall selected app"""
        package = self.table.item(row, 1).text()
        if self.adb_utils.uninstall_app(package):
            QMessageBox.information(self, "Success", "App uninstalled successfully")
            self.refresh_apps()
        else:
            QMessageBox.warning(self, "Error", "Failed to uninstall app")

    def toggle_app_enabled(self, row: int):
        """Toggle app enabled state"""
        package = self.table.item(row, 1).text()
        is_disabled = "Disabled" in self.table.item(row, 3).text()
        
        if self.adb_utils.set_app_enabled_state(package, is_disabled):
            QMessageBox.information(self, "Success", f"App {'enabled' if is_disabled else 'disabled'} successfully")
            self.refresh_apps()
        else:
            QMessageBox.warning(self, "Error", f"Failed to {'enable' if is_disabled else 'disable'} app")

    def toggle_app_suspended(self, row: int):
        """Toggle app suspended state"""
        package = self.table.item(row, 1).text()
        is_suspended = "Suspended" in self.table.item(row, 3).text()
        
        if self.adb_utils.set_app_suspended_state(package, is_suspended):
            QMessageBox.information(self, "Success", f"App {'resumed' if is_suspended else 'suspended'} successfully")
            self.refresh_apps()
        else:
            QMessageBox.warning(self, "Error", f"Failed to {'resume' if is_suspended else 'suspend'} app")

    def handle_device_state_changed(self, connected: bool):
        """Handle device connection state changes"""
        self.refresh_button.setEnabled(connected)
        self.system_apps_button.setEnabled(connected)
        
        if not connected:
            self.table.setRowCount(0)
            if self.worker:
                self.worker.quit()
            if self.details_worker:
                self.details_worker.quit()
            self.update_timer.stop()
            self._clear_details()

    def _on_selection_changed(self):
        """Handle app selection change"""
        selected = self.table.selectedItems()
        if not selected:
            self._clear_details()
            return
            
        # Get package name
        row = selected[0].row()
        package = self.table.item(row, 1).text()
        
        # Update selected package
        self.selected_package = package
        
        # Update details
        self._update_app_details()
        
        # Start update timer
        self.update_timer.start()

    def _update_app_details(self):
        """Update app details"""
        if not self.selected_package:
            return
            
        # Create and start worker
        if self.details_worker:
            self.details_worker.quit()
            
        self.details_worker = AppDetailsWorker(self.adb_utils, self.selected_package)
        self.details_worker.finished.connect(self._handle_details_loaded)
        self.details_worker.error.connect(self.handle_error)
        self.details_worker.start()

    def _handle_details_loaded(self, info: Dict):
        """Handle loaded app details"""
        try:
            if not info:
                self._clear_details()
                return
                
            # Update status
            details = info.get('details', {})
            if not details:
                self._clear_details()
                return
                
            self.stopped_value.setText("Yes" if details.get('is_stopped', False) else "No")
            self.disabled_value.setText("Yes" if details.get('is_disabled', False) else "No")
            self.suspended_value.setText("Yes" if details.get('is_suspended', False) else "No")
            
            # Update resource usage
            resources = info.get('resources', {})
            self.cpu_value.setText(f"{resources.get('cpu_percent', 0):.1f}%")
            
            # Update memory values
            memory = info.get('memory', {})
            if memory:
                try:
                    total_mb = float(memory.get('total_pss', 0)) / 1024.0
                    java_heap_mb = float(memory.get('java_heap', 0)) / 1024.0
                    native_heap_mb = float(memory.get('native_heap', 0)) / 1024.0
                    
                    self.memory_value.setText(f"Total: {total_mb:.1f} MB\nJava: {java_heap_mb:.1f} MB\nNative: {native_heap_mb:.1f} MB")
                    self.virtual_value.setText(f"{resources.get('vsz_kb', 0) / 1024.0:.1f} MB")
                except (TypeError, ValueError):
                    self.memory_value.setText("N/A")
                    self.virtual_value.setText("N/A")
            else:
                self.memory_value.setText("N/A")
                self.virtual_value.setText("N/A")
            
            # Update issues
            crashes = info.get('crashes', {})
            recent_crashes = len(crashes.get('recent_crashes', []))
            recent_anrs = len(crashes.get('recent_anrs', []))
            
            self.crashes_value.setText(str(recent_crashes))
            self.anrs_value.setText(str(recent_anrs))
            
            # Update status text
            if recent_crashes > 0 or recent_anrs > 0:
                self.status_label.setText("Warning: App has recent issues")
                self.status_label.setStyleSheet("color: red")
            elif details.get('is_disabled', False):
                self.status_label.setText("Warning: App is disabled")
                self.status_label.setStyleSheet("color: red")
            elif details.get('is_suspended', False):
                self.status_label.setText("App is suspended (sleeping)")
                self.status_label.setStyleSheet("color: orange")
            elif details.get('is_stopped', False):
                self.status_label.setText("Warning: App is force stopped")
                self.status_label.setStyleSheet("color: darkred")
            else:
                self.status_label.setText("App is running normally")
                self.status_label.setStyleSheet("")
                
        except Exception as e:
            self.error_logger.log_error(
                f"Error handling app details: {str(e)}",
                ErrorCode.UNKNOWN,
                {"info": str(info)}
            )
            self._clear_details()

    def _clear_details(self):
        """Clear app details"""
        self.selected_package = None
        self.update_timer.stop()
        
        # Clear status
        self.status_label.setText("Select an app to view details")
        self.status_label.setStyleSheet("")
        self.stopped_value.setText("N/A")
        self.disabled_value.setText("N/A")
        self.suspended_value.setText("N/A")
        
        # Clear resource usage
        self.cpu_value.setText("N/A")
        self.memory_value.setText("N/A")
        self.virtual_value.setText("N/A")
        
        # Clear issues
        self.crashes_value.setText("N/A")
        self.anrs_value.setText("N/A")
