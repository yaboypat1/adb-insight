from typing import List, Dict, Optional, NamedTuple
import subprocess
import re
from datetime import datetime
import json
from .error_utils import ErrorLogger, ErrorCode
from .debug_utils import DebugLogger
import concurrent.futures
import time
import socket
from PySide6.QtCore import Signal, QObject

class AppInfo(NamedTuple):
    package_name: str
    app_name: str
    version: str
    install_time: datetime
    last_updated: datetime
    size: int
    activities: List[str]
    services: List[str]
    permissions: List[str]

class AppAnalytics(NamedTuple):
    cpu_usage: float
    memory_usage: Dict[str, int]
    battery_drain: float
    network_usage: Dict[str, int]
    storage_usage: Dict[str, int]

class AppUtils(QObject):
    """Utility class for app management"""
    
    # Signals
    device_state_changed = Signal(bool)  # True if connected, False if disconnected
    
    def __init__(self):
        """Initialize AppUtils"""
        super().__init__()
        
        # Initialize loggers first
        self.error_logger = ErrorLogger()
        self.debug_logger = DebugLogger()
        
        # Initialize state
        self.adb_ready = False
        self.last_check = 0
        self._app_cache = []  # Cache for installed apps
        self._last_app_refresh = 0  # Last time apps were refreshed
        self._memory_cache = {}  # Cache for memory info
        self._last_memory_refresh = {}  # Last refresh time per package
        self._analytics_cache = {}  # Cache for analytics
        self._last_analytics_refresh = {}  # Last refresh time per package
        self._device_cache = None  # Cache for device info
        self._last_device_refresh = 0  # Last time device was checked
        
        # Start ADB server without requiring device
        try:
            subprocess.run(['adb', 'start-server'], 
                         capture_output=True, 
                         text=True,
                         check=True)
            self.debug_logger.log_debug("ADB server started", "init", "success")
        except Exception as e:
            self.debug_logger.log_debug(f"Failed to start ADB server: {str(e)}", "init", "warning")
            
        # Initial device check
        self._verify_adb(raise_on_no_device=False)
            
    def _log_operation(self, operation: str, package_name: str = '') -> callable:
        """Create a log entry for an operation"""
        start_time = datetime.now()
        
        def log_result(status: str, details: str):
            duration = (datetime.now() - start_time).total_seconds()
            self.debug_logger.log_debug(
                message=details,
                operation=operation,
                status=status,
                package=package_name,
                duration=duration
            )
            
        return log_result

    def _should_refresh_cache(self, last_refresh: float, timeout: int = 30) -> bool:
        """Check if cache should be refreshed based on timeout"""
        return time.time() - last_refresh > timeout
        
    def _verify_device(self) -> bool:
        """Verify device connection with caching"""
        current_time = time.time()
        
        # Use cached result if available and recent (5 seconds)
        if self._device_cache is not None and (current_time - self._last_device_refresh) < 5:
            return self._device_cache
            
        try:
            devices = subprocess.run(
                ['adb', 'devices'], 
                check=True, 
                capture_output=True, 
                text=True
            ).stdout.strip().split('\n')[1:]
            
            # Filter out empty lines and unauthorized devices
            devices = [d for d in devices if d and 'unauthorized' not in d]
            
            # Update cache
            self._device_cache = len(devices) > 0
            self._last_device_refresh = current_time
            
            return self._device_cache
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to verify device: {str(e)}")
            return False
            
    def _verify_adb(self, raise_on_no_device=True):
        """Verify ADB is available and check device status"""
        current_time = time.time()
        
        # Only check every 3 seconds
        if current_time - self.last_check < 3:
            if not self.adb_ready and raise_on_no_device:
                self.debug_logger.log_debug("No device connected", "verify_adb", "warning")
                raise Exception("No device connected")
            return self.adb_ready
            
        self.last_check = current_time
        was_ready = self.adb_ready
        
        try:
            # Check for devices
            result = subprocess.run(['adb', 'devices'], 
                                capture_output=True, 
                                text=True,
                                check=True)
            
            # Parse device list (more carefully)
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
            devices = []
            
            for line in lines[1:]:  # Skip first line (header)
                if '\t' in line:
                    serial, state = line.split('\t')
                    if state == 'device':
                        devices.append(serial)
                        
            device_connected = len(devices) > 0
            
            # Update state
            self.adb_ready = device_connected
            
            # Log appropriate message
            if device_connected:
                self.debug_logger.log_debug(f"Device connected: {devices[0]}", "verify_adb", "success")
            else:
                self.debug_logger.log_debug("No device connected", "verify_adb", "warning")
                
            # Emit signal if state changed
            if was_ready != self.adb_ready:
                self.device_state_changed.emit(self.adb_ready)
                
            # Handle no device case
            if not device_connected and raise_on_no_device:
                raise Exception("No device connected")
                
            return device_connected
            
        except subprocess.CalledProcessError as e:
            self.adb_ready = False
            error_msg = f"ADB command failed: {e.stderr}"
            self.debug_logger.log_debug(error_msg, "verify_adb", "warning")
            
            # Emit signal if state changed
            if was_ready:
                self.device_state_changed.emit(False)
                
            if raise_on_no_device:
                raise Exception(error_msg)
            return False
            
        except Exception as e:
            self.adb_ready = False
            error_msg = str(e)
            self.debug_logger.log_debug(error_msg, "verify_adb", "warning")
            
            # Emit signal if state changed
            if was_ready:
                self.device_state_changed.emit(False)
                
            if raise_on_no_device:
                raise
            return False
                
    def _run_adb_command(self, command: List[str]) -> str:
        """Run an ADB command and return its output"""
        log_result = self._log_operation("adb_command", None)
        try:
            if not self.adb_ready and not self._verify_device():
                raise Exception("No device connected")
            result = subprocess.run(['adb'] + command, check=True, capture_output=True, text=True)
            log_result("success", f"Command: adb {' '.join(command)}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"ADB command failed: {' '.join(['adb'] + command)}\nError: {str(e)}"
            log_result("error", error_msg)
            self.error_logger.log_error(error_msg)
            raise Exception(error_msg)

    def get_installed_apps(self, system_apps: bool = False, force_refresh: bool = False) -> List[Dict[str, str]]:
        """Get list of installed apps with their names"""
        current_time = time.time()
        
        # Return cached results if available and not forced to refresh
        if not force_refresh and self._app_cache and (current_time - self._last_app_refresh) < 30:
            return self._app_cache
            
        # If no device and we have cache, return cache
        if not self.adb_ready and self._app_cache:
            self.debug_logger.log_debug("No device - using cached app list", "get_apps", "warning")
            return self._app_cache
            
        log_result = self._log_operation("get_installed_apps")
        try:
            # Get package names
            cmd = ['shell', 'pm', 'list', 'packages', '-f']
            if not system_apps:
                cmd.append('-3')  # Only third-party apps
                
            output = self._run_adb_command(cmd)
            
            apps = []
            for line in output.splitlines():
                if not line:
                    continue
                    
                # Parse package path and name
                match = re.match(r'package:(.+?)=(.+)', line)
                if not match:
                    continue
                    
                path, package = match.groups()
                
                # Get app label using aapt
                try:
                    name = package  # Default to package name
                    dump_cmd = ['shell', 'dumpsys', 'package', package]
                    dump_output = self._run_adb_command(dump_cmd)
                    
                    # Try to find the app name
                    label_match = re.search(r'applicationInfo.*?labelRes=\d+\s+label="([^"]+)"', dump_output, re.DOTALL)
                    if label_match:
                        name = label_match.group(1)
                    else:
                        # Try alternate format
                        alt_match = re.search(r'Application Label:\s*(.+)', dump_output)
                        if alt_match:
                            name = alt_match.group(1).strip()
                            
                    apps.append({
                        'package': package,
                        'name': name,
                        'path': path,
                        'system': system_apps
                    })
                    
                except Exception as e:
                    self.debug_logger.log_debug(f"Failed to get name for {package}: {str(e)}", "get_apps", "warning")
                    # Still add the app, just with package name
                    apps.append({
                        'package': package,
                        'name': package,
                        'path': path,
                        'system': system_apps
                    })
                    
            # Update cache
            self._app_cache = apps
            self._last_app_refresh = current_time
            
            log_result("success", f"Found {len(apps)} apps")
            return apps
            
        except Exception as e:
            error_msg = f"Failed to get installed apps: {str(e)}"
            self.debug_logger.log_debug(error_msg, "get_apps", "error")
            
            # Return cache if available
            if self._app_cache:
                return self._app_cache
                
            # Otherwise return empty list
            return []

    def get_memory_info(self, package: str) -> Optional[Dict]:
        """Get memory info with caching"""
        current_time = time.time()
        last_refresh = self._last_memory_refresh.get(package, 0)
        
        # Return cached data if recent (5 seconds)
        if package in self._memory_cache and not self._should_refresh_cache(last_refresh, 5):
            return self._memory_cache[package]
            
        try:
            cmd = ['shell', 'dumpsys', 'meminfo', package]
            output = self._run_adb_command(cmd)
            
            # Parse memory info
            memory = {}
            total_pss = re.search(r'TOTAL PSS:\s+(\d+)', output)
            if total_pss:
                memory['total_mb'] = int(total_pss.group(1)) / 1024  # Convert to MB
                
            # Update cache
            self._memory_cache[package] = memory
            self._last_memory_refresh[package] = current_time
            
            return memory
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to get memory info: {str(e)}")
            return None
            
    def get_app_analytics(self, package: str) -> Optional[Dict]:
        """Get app analytics with caching"""
        current_time = time.time()
        
        # Check cache
        if (package in self._analytics_cache and 
            (current_time - self._last_analytics_refresh.get(package, 0)) < 5):
            return self._analytics_cache[package]
            
        try:
            if not self.adb_ready:
                return None
                
            analytics = {}
            
            # Get CPU usage
            cpu_cmd = ['shell', 'top', '-n', '1', '|', 'grep', package]
            try:
                cpu_output = self._run_adb_command(cpu_cmd)
                if cpu_output:
                    # Parse CPU usage from top output
                    parts = cpu_output.split()
                    for i, part in enumerate(parts):
                        if part.endswith('%'):
                            analytics['cpu'] = float(part.rstrip('%'))
                            break
                    if 'cpu' not in analytics:
                        analytics['cpu'] = 0.0
            except Exception as e:
                self.debug_logger.log_debug(f"Failed to get CPU usage: {str(e)}", "analytics", "warning")
                analytics['cpu'] = 0.0
                
            # Get memory usage
            mem_cmd = ['shell', 'dumpsys', 'meminfo', package]
            try:
                mem_output = self._run_adb_command(mem_cmd)
                if mem_output:
                    # Parse memory info
                    total = re.search(r'TOTAL\s+(\d+)', mem_output)
                    if total:
                        analytics['total_memory'] = int(total.group(1)) * 1024  # Convert to bytes
                    
                    # Get detailed memory breakdown
                    analytics['memory'] = {
                        'java': re.search(r'Java Heap:\s+(\d+)', mem_output),
                        'native': re.search(r'Native Heap:\s+(\d+)', mem_output),
                        'code': re.search(r'Code:\s+(\d+)', mem_output),
                        'stack': re.search(r'Stack:\s+(\d+)', mem_output),
                        'graphics': re.search(r'Graphics:\s+(\d+)', mem_output)
                    }
                    analytics['memory'] = {k: int(v.group(1)) * 1024 if v else 0 
                                        for k, v in analytics['memory'].items()}
            except Exception as e:
                self.debug_logger.log_debug(f"Failed to get memory info: {str(e)}", "analytics", "warning")
                analytics['total_memory'] = 0
                analytics['memory'] = {'java': 0, 'native': 0, 'code': 0, 'stack': 0, 'graphics': 0}
                
            # Get battery usage
            bat_cmd = ['shell', 'dumpsys', 'batterystats', package]
            try:
                bat_output = self._run_adb_command(bat_cmd)
                if bat_output:
                    # Parse battery usage
                    battery = re.search(r'Computed drain:\s+([\d.]+)', bat_output)
                    analytics['battery'] = float(battery.group(1)) if battery else 0.0
            except Exception as e:
                self.debug_logger.log_debug(f"Failed to get battery info: {str(e)}", "analytics", "warning")
                analytics['battery'] = 0.0
                
            # Get network usage
            net_cmd = ['shell', 'cat', f'/proc/uid_stat/{package}/tcp_rcv']
            try:
                rx_output = self._run_adb_command(net_cmd)
                analytics['rx_bytes'] = int(rx_output.strip()) if rx_output else 0
                
                net_cmd = ['shell', 'cat', f'/proc/uid_stat/{package}/tcp_snd']
                tx_output = self._run_adb_command(net_cmd)
                analytics['tx_bytes'] = int(tx_output.strip()) if tx_output else 0
            except Exception as e:
                self.debug_logger.log_debug(f"Failed to get network info: {str(e)}", "analytics", "warning")
                analytics['rx_bytes'] = 0
                analytics['tx_bytes'] = 0
                
            # Update cache
            self._analytics_cache[package] = analytics
            self._last_analytics_refresh[package] = current_time
            
            return analytics
            
        except Exception as e:
            self.debug_logger.log_debug(f"Failed to get analytics: {str(e)}", "analytics", "error")
            return None
            
    def get_app_details(self, package_name: str) -> Optional[AppInfo]:
        """Get detailed information about an app"""
        log_result = self._log_operation("get_app_details", package_name)
        try:
            # Get basic package info
            output = self._run_adb_command(['shell', f"dumpsys package {package_name}"])
            
            # Extract app name
            app_name = package_name
            name_match = re.search(r'label="([^"]+)"', output)
            if name_match:
                app_name = name_match.group(1)
            
            # Extract version
            version = "Unknown"
            version_match = re.search(r'versionName=([^\s]+)', output)
            if version_match:
                version = version_match.group(1)
            
            # Extract timestamps
            install_time = datetime.now()
            update_time = datetime.now()
            time_match = re.search(r'firstInstallTime=([0-9]+).*lastUpdateTime=([0-9]+)', output)
            if time_match:
                install_time = datetime.fromtimestamp(int(time_match.group(1)) / 1000)
                update_time = datetime.fromtimestamp(int(time_match.group(2)) / 1000)
            
            # Get app size
            size = 0
            try:
                size_output = self._run_adb_command(['shell', f"du -b $(pm path {package_name} | cut -d: -f2)"])
                size = sum(int(line.split()[0]) for line in size_output.splitlines() if line.strip())
            except:
                pass
            
            # Extract activities
            activities = []
            activity_section = re.search(r'Activity Resolver Table:.*?(?=Receiver Resolver Table|\Z)', output, re.DOTALL)
            if activity_section:
                activities = [
                    act.strip()
                    for act in re.findall(r'\s+([a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', activity_section.group())
                    if act.strip() and package_name in act
                ]
            
            # Extract services
            services = []
            service_section = re.search(r'Service Resolver Table:.*?(?=Provider Resolver Table|\Z)', output, re.DOTALL)
            if service_section:
                services = [
                    svc.strip()
                    for svc in re.findall(r'\s+([a-zA-Z0-9_.]+/[a-zA-Z0-9_.]+)', service_section.group())
                    if svc.strip() and package_name in svc
                ]
            
            # Extract permissions
            permissions = re.findall(r'runtime permission:(.*?)(?=\n|$)', output)
            
            log_result("success", f"Retrieved app details: Name={app_name}, Version={version}")
            return AppInfo(
                package_name=package_name,
                app_name=app_name,
                version=version,
                install_time=install_time,
                last_updated=update_time,
                size=size,
                activities=activities,
                services=services,
                permissions=permissions
            )
            
        except Exception as e:
            log_result("error", f"Failed to get app details for {package_name}: {str(e)}")
            self.error_logger.log_error(f"Failed to get app details for {package_name}: {str(e)}")
            raise

    def check_adb_status(self) -> bool:
        """Check ADB status and update adb_ready flag"""
        # Only check every 2 seconds to avoid too frequent checks
        current_time = time.time()
        if current_time - self.last_check < 2:
            return self.adb_ready
            
        self.last_check = current_time
        was_ready = self.adb_ready
        self.adb_ready = self._verify_adb(raise_on_no_device=False)
        
        # Log status change
        if was_ready != self.adb_ready:
            if self.adb_ready:
                self.debug_logger.log_operation("adb_status", "success", "ADB connection established")
            else:
                self.debug_logger.log_operation("adb_status", "warning", "ADB connection lost")
        
        return self.adb_ready
