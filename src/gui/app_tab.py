from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QCursor

from ..utils.adb_utils import ADBUtils
from ..utils.debug_utils import DebugLogger
from ..utils.error_utils import ErrorLogger, ErrorCode

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
                    
                    # Get memory info
                    memory = self.adb_utils.get_memory_info(package)
                    total_memory = memory.get('total_pss', 0) if memory else 0
                    
                    apps.append({
                        'name': name,
                        'package': package,
                        'memory': total_memory
                    })
                    
                    # Update progress
                    progress = int((i + 1) / total * 100)
                    self.progress.emit(progress)
                    
                except Exception as e:
                    continue  # Skip failed app
                    
            self.finished.emit(apps)
            
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
        
        # Initialize worker
        self.worker = None
        
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
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Package", "Memory Usage"])
        
        # Set table properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Add context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
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
            # App name
            name_item = QTableWidgetItem(app['name'])
            self.table.setItem(i, 0, name_item)
            
            # Package name
            package_item = QTableWidgetItem(app['package'])
            self.table.setItem(i, 1, package_item)
            
            # Memory usage (format as MB)
            memory_mb = app['memory'] / 1024  # Convert KB to MB
            memory_item = QTableWidgetItem(f"{memory_mb:.1f} MB")
            memory_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, memory_item)
            
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
            
        # Create menu
        menu = QMenu()
        
        # Add actions
        clear_data = QAction("Clear App Data", self)
        clear_data.triggered.connect(lambda: self.clear_app_data(row))
        menu.addAction(clear_data)
        
        force_stop = QAction("Force Stop", self)
        force_stop.triggered.connect(lambda: self.force_stop_app(row))
        menu.addAction(force_stop)
        
        uninstall = QAction("Uninstall", self)
        uninstall.triggered.connect(lambda: self.uninstall_app(row))
        menu.addAction(uninstall)
        
        # Show menu
        menu.exec_(QCursor.pos())

    def clear_app_data(self, row: int):
        """Clear data for selected app"""
        package = self.table.item(row, 1).text()
        # TODO: Implement clear data functionality
        QMessageBox.information(self, "Not Implemented", "Clear data not implemented yet")

    def force_stop_app(self, row: int):
        """Force stop selected app"""
        package = self.table.item(row, 1).text()
        # TODO: Implement force stop functionality
        QMessageBox.information(self, "Not Implemented", "Force stop not implemented yet")

    def uninstall_app(self, row: int):
        """Uninstall selected app"""
        package = self.table.item(row, 1).text()
        # TODO: Implement uninstall functionality
        QMessageBox.information(self, "Not Implemented", "Uninstall not implemented yet")

    def handle_device_state_changed(self, connected: bool):
        """Handle device connection state changes"""
        self.refresh_button.setEnabled(connected)
        self.system_apps_button.setEnabled(connected)
        
        if not connected:
            self.table.setRowCount(0)
