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
from PyQt6.QtCore import pyqtSignal, QObject
import os
import sys
import subprocess
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
from adb_shell.adb_device import AdbDeviceUsb
from adb.adb_commands import AdbCommands
from retry import retry
import psutil
import humanize
from .error_utils import ErrorLogger, ErrorCode, AppError, DeviceError, MemoryError
from .debug_utils import DebugLogger
from .adb_utils import ADBUtils

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
    device_state_changed = pyqtSignal(bool)  # True if connected, False if disconnected
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        """Initialize AppUtils"""
        super().__init__()
        
        # Store loggers
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
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
        self.current_device = None
        self.include_system_apps = False
        
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
        self._verify_device(raise_on_no_device=False)
            
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
        
    def _verify_device(self, raise_on_no_device=True):
        """Verify a device is connected"""
        try:
            devices = subprocess.run(['adb', 'devices'], 
                                capture_output=True, 
                                text=True,
                                check=True).stdout.strip().split('\n')[1:]
            
            # Filter out empty lines and unauthorized devices
            devices = [d for d in devices if d and 'unauthorized' not in d]
            
            if not devices:
                self.debug_logger.log_debug("No devices connected", "verify_device", "warning")
                return False
                
            # Use the first connected device
            device = next((d for d in devices if 'device' in d), None)
            if not device:
                self.debug_logger.log_debug("No device in ready state", "verify_device", "warning")
                return False
                
            self.current_device = device
            self.debug_logger.log_debug(
                f"Using device: {device}", 
                "verify_device", 
                "info"
            )
            return True
            
        except Exception as e:
            self.debug_logger.log_debug(f"Device verification failed: {str(e)}", "verify_device", "error")
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

    def get_installed_apps(self, force_refresh=False) -> List[Dict[str, str]]:
        """Get list of installed apps with caching"""
        try:
            # Check if we should use cache
            current_time = time.time()
            if not force_refresh and self._app_cache and (current_time - self._last_app_refresh) < 30:
                self.debug_logger.log_debug("Using cached app list", "get_apps", "info")
                return self._app_cache
                
            # Verify device
            if not self._verify_device():
                if self._app_cache:
                    self.debug_logger.log_debug("No device, using cached apps", "get_apps", "warning")
                    return self._app_cache
                return []
                
            # Get all packages
            cmd = ['shell', 'pm', 'list', 'packages', '-f', '-3']  # -3 for third-party apps
            output = self._run_adb_command(cmd)
            
            if not output:
                self.debug_logger.log_debug("No packages found", "get_apps", "warning")
                return []
                
            apps = []
            for line in output.splitlines():
                try:
                    if not line.startswith('package:'):
                        continue
                        
                    # Parse package line
                    # Format: package:/data/app/com.example.app-hash/base.apk=com.example.app
                    parts = line[8:].split('=')  # Remove 'package:' prefix
                    if len(parts) != 2:
                        continue
                        
                    path, package = parts
                    path = path.strip()
                    package = package.strip()
                    
                    # Get app name
                    name = self._get_app_name(package)
                    if not name:
                        name = package.split('.')[-1].title()
                    
                    # Get app info
                    info = {
                        'package': package,
                        'name': name,
                        'path': path,
                        'system': False
                    }
                    
                    apps.append(info)
                    
                except Exception as e:
                    self.debug_logger.log_debug(f"Error parsing package: {str(e)}", "get_apps", "warning")
                    continue
                    
            # Get system apps if requested
            if self.include_system_apps:
                cmd = ['shell', 'pm', 'list', 'packages', '-f', '-s']  # -s for system apps
                output = self._run_adb_command(cmd)
                
                if output:
                    for line in output.splitlines():
                        try:
                            if not line.startswith('package:'):
                                continue
                                
                            parts = line[8:].split('=')
                            if len(parts) != 2:
                                continue
                                
                            path, package = parts
                            path = path.strip()
                            package = package.strip()
                            
                            # Skip already added apps
                            if any(a['package'] == package for a in apps):
                                continue
                                
                            name = self._get_app_name(package)
                            if not name:
                                name = package.split('.')[-1].title()
                                
                            info = {
                                'package': package,
                                'name': name,
                                'path': path,
                                'system': True
                            }
                            
                            apps.append(info)
                            
                        except Exception as e:
                            self.debug_logger.log_debug(f"Error parsing system package: {str(e)}", "get_apps", "warning")
                            continue
                            
            # Update cache
            self._app_cache = apps
            self._last_app_refresh = current_time
            
            self.debug_logger.log_debug(f"Found {len(apps)} apps", "get_apps", "info")
            return apps
            
        except Exception as e:
            self.debug_logger.log_debug(f"Failed to get app list: {str(e)}", "get_apps", "error")
            if self._app_cache:
                return self._app_cache
            return []
            
    def _get_app_name(self, package: str) -> Optional[str]:
        """Get app name from package"""
        try:
            cmd = ['shell', 'dumpsys', 'package', package]
            output = self._run_adb_command(cmd)
            
            if output:
                # Try different patterns
                patterns = [
                    r'applicationInfo.*?labelRes=\d+\s+nonLocalizedLabel=([^\s]+)',
                    r'Application Label:\s*([^\n]+)',
                    r'labelRes=\d+\s+label="([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, output)
                    if match:
                        name = match.group(1).strip()
                        if name and name != package:
                            return name
                            
            return None
            
        except Exception as e:
            self.debug_logger.log_debug(f"Failed to get app name: {str(e)}", "app_name", "warning")
            return None
            
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
        self.adb_ready = self._verify_device(raise_on_no_device=False)
        
        # Log status change
        if was_ready != self.adb_ready:
            if self.adb_ready:
                self.debug_logger.log_operation("adb_status", "success", "ADB connection established")
            else:
                self.debug_logger.log_operation("adb_status", "warning", "ADB connection lost")
        
        return self.adb_ready

class EnhancedAppUtils:
    """Enhanced utility class for app operations"""
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.adb_utils = ADBUtils(debug_logger, error_logger)
        self.app_cache = {}
        self.last_refresh = 0
        self.cache_timeout = 5  # seconds
        
    def _verify_device(self) -> bool:
        """Verify device connection with enhanced error handling"""
        try:
            devices = self.adb_utils.get_connected_devices()
            if not devices:
                self.error_logger.log_error(
                    "No devices connected",
                    ErrorCode.DEVICE_NOT_CONNECTED,
                    {'state': 'no_device'}
                )
                return False
                
            # Check for exactly one device in proper state
            connected_devices = [d for d in devices if d['state'] == 'device']
            if not connected_devices:
                self.error_logger.log_error(
                    "No device in ready state",
                    ErrorCode.DEVICE_NOT_CONNECTED,
                    {'state': 'not_ready'}
                )
                return False
            elif len(connected_devices) > 1:
                self.error_logger.log_error(
                    "Multiple devices connected",
                    ErrorCode.MULTIPLE_DEVICES,
                    {'count': len(connected_devices)}
                )
                return False
                
            # Device is ready
            device = connected_devices[0]
            self.debug_logger.log_debug(
                f"Device {device['id']} connected ({device.get('model', 'Unknown')})", 
                "device", 
                "info"
            )
            return True
            
        except Exception as e:
            self.error_logger.log_error(
                f"Device verification error: {str(e)}",
                ErrorCode.DEVICE_NOT_CONNECTED,
                {'error': str(e)}
            )
            return False
            
    def get_installed_apps(self, force_refresh: bool = False) -> List[Dict]:
        """Get installed apps with enhanced info"""
        try:
            return self.adb_utils.get_installed_apps(system_apps=False, force_refresh=force_refresh)
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to get installed apps: {str(e)}",
                ErrorCode.APP_NOT_FOUND,
                {'force_refresh': force_refresh}
            )
            return []
            
    def get_app_info(self, package: str) -> Optional[Dict]:
        """Get detailed app information"""
        try:
            if not self._verify_device():
                return None
                
            # Get basic app info
            apps = self.get_installed_apps()
            app_info = next((app for app in apps if app['package'] == package), None)
            if not app_info:
                raise AppError(f"App {package} not found", ErrorCode.APP_NOT_FOUND)
                
            # Get memory info
            memory = self.adb_utils.get_memory_info(package)
            if memory:
                app_info['memory'] = memory
                
            # Get analytics
            analytics = self.adb_utils.get_app_analytics(package)
            if analytics:
                app_info.update(analytics)
                
            # Add human-readable sizes
            if 'memory' in app_info:
                app_info['memory_human'] = {
                    k: humanize.naturalsize(v)
                    for k, v in app_info['memory'].items()
                }
                
            if 'disk_usage' in app_info:
                app_info['disk_usage_human'] = humanize.naturalsize(app_info['disk_usage'])
                
            return app_info
            
        except AppError as e:
            self.error_logger.log_error(
                str(e),
                e.code,
                {'package': package}
            )
            return None
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to get app info: {str(e)}",
                ErrorCode.APP_NOT_FOUND,
                {'package': package}
            )
            return None
            
    def monitor_app(self, package: str, duration: int = 60, interval: int = 1) -> List[Dict]:
        """Monitor app performance over time"""
        try:
            if not self._verify_device():
                return []
                
            metrics = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    # Get current metrics
                    analytics = self.adb_utils.get_app_analytics(package)
                    if analytics:
                        analytics['timestamp'] = datetime.now().isoformat()
                        metrics.append(analytics)
                        
                except Exception as e:
                    self.error_logger.log_error(
                        f"Failed to get metrics: {str(e)}",
                        ErrorCode.ANALYTICS_CPU_FAILED,
                        {'package': package, 'timestamp': datetime.now().isoformat()}
                    )
                    
                time.sleep(interval)
                
            return metrics
            
        except Exception as e:
            self.error_logger.log_error(
                f"App monitoring failed: {str(e)}",
                ErrorCode.ANALYTICS_CPU_FAILED,
                {'package': package, 'duration': duration}
            )
            return []
            
    def analyze_memory_usage(self, package: str) -> Optional[Dict]:
        """Analyze app memory usage patterns"""
        try:
            if not self._verify_device():
                return None
                
            # Get current memory info
            memory = self.adb_utils.get_memory_info(package)
            if not memory:
                raise MemoryError(f"Failed to get memory info for {package}")
                
            # Get device total memory
            success, output = self.adb_utils._run_adb(['shell', 'cat', '/proc/meminfo'])
            total_memory = None
            if success:
                for line in output.split('\n'):
                    if 'MemTotal' in line:
                        total_memory = int(line.split()[1]) * 1024  # Convert to bytes
                        break
                        
            analysis = {
                'current': memory,
                'total_device_memory': total_memory,
                'percentages': {}
            }
            
            # Calculate percentages if we have total memory
            if total_memory:
                for key, value in memory.items():
                    if isinstance(value, (int, float)):
                        analysis['percentages'][key] = (value / total_memory) * 100
                        
            # Add human-readable values
            analysis['human_readable'] = {
                'current': {k: humanize.naturalsize(v) for k, v in memory.items()},
                'total_device_memory': humanize.naturalsize(total_memory) if total_memory else None
            }
            
            return analysis
            
        except MemoryError as e:
            self.error_logger.log_error(
                str(e),
                e.code,
                {'package': package}
            )
            return None
            
        except Exception as e:
            self.error_logger.log_error(
                f"Memory analysis failed: {str(e)}",
                ErrorCode.MEMORY_READ_FAILED,
                {'package': package}
            )
            return None
            
    def get_app_permissions(self, package: str) -> Optional[Dict]:
        """Get detailed app permissions"""
        try:
            if not self._verify_device():
                return None
                
            success, output = self.adb_utils._run_adb(['shell', 'dumpsys', 'package', package])
            if not success:
                raise AppError(f"Failed to get permissions for {package}")
                
            permissions = {
                'granted': [],
                'denied': [],
                'requested': []
            }
            
            current_section = None
            for line in output.split('\n'):
                if 'granted=true' in line:
                    perm = line.split(':')[1].strip()
                    permissions['granted'].append(perm)
                elif 'granted=false' in line:
                    perm = line.split(':')[1].strip()
                    permissions['denied'].append(perm)
                elif 'requested' in line and 'permission' in line:
                    perm = line.split(':')[1].strip()
                    permissions['requested'].append(perm)
                    
            return permissions
            
        except AppError as e:
            self.error_logger.log_error(
                str(e),
                e.code,
                {'package': package}
            )
            return None
            
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to get app permissions: {str(e)}",
                ErrorCode.APP_NOT_FOUND,
                {'package': package}
            )
            return None
