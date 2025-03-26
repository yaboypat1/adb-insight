import os
import sys
import subprocess
import time
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from adb_shell.adb_device import AdbDeviceUsb, AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb.adb_commands import AdbCommands
from retry import retry
import psutil
import humanize
from .error_utils import ErrorLogger, ErrorCode, ADBError
from .debug_utils import DebugLogger
import logging
import shutil

class ADBUtils:
    """Enhanced utility class for ADB operations"""
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        self.signer = None
        self.adb_path = 'adb'  # Default to 'adb' in PATH
        self._verify_adb_path()
        self.device_cache = {}
        self.app_cache = {}
        self.last_device_check = 0
        self.last_app_refresh = 0
        self.cache_timeout = 5  # seconds
        
        # Initialize ADB client
        self._init_adb_client()
        
    def _init_adb_client(self):
        """Initialize ADB client with authentication"""
        try:
            # Set up authentication
            key_path = os.path.expanduser('~/.android/adbkey')
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    private_key = f.read()
                with open(key_path + '.pub', 'rb') as f:
                    public_key = f.read()
                self.signer = PythonRSASigner(public_key, private_key)
                
            # Initialize ADB commands
            self.adb = AdbCommands()
            
            self.debug_logger.log_debug("ADB client initialized", "adb", "info")
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to initialize ADB client: {str(e)}", 
                                    ErrorCode.ADB_SERVER_NOT_RUNNING)
            
    def _verify_adb_path(self) -> None:
        """Verify ADB executable exists in PATH"""
        if shutil.which(self.adb_path):
            self.debug_logger.log_debug(
                f"ADB executable found at: {shutil.which(self.adb_path)}", 
                "adb", 
                "info"
            )
            return
            
        # Try common environment variables
        for env_var in ['ANDROID_HOME', 'ANDROID_SDK_ROOT']:
            if env_var in os.environ:
                platform_tools = os.path.join(os.environ[env_var], 'platform-tools', 'adb')
                if os.path.exists(platform_tools):
                    self.adb_path = platform_tools
                    self.debug_logger.log_debug(
                        f"ADB executable found at: {platform_tools}", 
                        "adb", 
                        "info"
                    )
                    return
                    
        error_msg = (
            "ADB executable not found in PATH or Android SDK. "
            "Please ensure Android SDK Platform Tools are installed "
            "and the directory containing adb.exe is added to your PATH."
        )
        self.error_logger.log_error(error_msg)
        raise FileNotFoundError(error_msg)
        
    @retry(tries=3, delay=1, backoff=2)
    def _run_adb(self, args: List[str], timeout: int = 15) -> Tuple[bool, str]:
        """Run an ADB command with retry logic and enhanced error handling"""
        command = [self.adb_path] + args
        cmd_str = ' '.join(command)
        
        try:
            self.debug_logger.log_debug(f"Running ADB command: {cmd_str}", "adb", "debug")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout
            )
            
            if result.returncode != 0:
                error_msg = f"ADB command failed (code {result.returncode}): {result.stderr.strip()}"
                self.error_logger.log_error(error_msg)
                return False, error_msg
                
            self.debug_logger.log_debug(
                f"ADB command successful: {result.stdout.strip()[:100]}...", 
                "adb", 
                "debug"
            )
            return True, result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            error_msg = f"ADB command timed out after {timeout}s: {cmd_str}"
            self.error_logger.log_error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"ADB command failed unexpectedly: {str(e)}"
            self.error_logger.log_error(error_msg)
            return False, error_msg
            
    def _run_shell_command(self, args: List[str], timeout: int = 15) -> Tuple[bool, str]:
        """Run an ADB shell command safely handling pipes and redirects"""
        # For shell commands that need pipe operations
        if any(x in ' '.join(args) for x in ['|', '>', '<', '&']):
            shell_cmd = f"{self.adb_path} shell " + ' '.join(args)
            try:
                self.debug_logger.log_debug(f"Running shell command: {shell_cmd}", "adb", "debug")
                
                result = subprocess.run(
                    shell_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode != 0:
                    error_msg = f"Shell command failed: {result.stderr.strip()}"
                    self.error_logger.log_error(error_msg)
                    return False, error_msg
                    
                return True, result.stdout.strip()
                
            except Exception as e:
                error_msg = f"Shell command failed: {str(e)}"
                self.error_logger.log_error(error_msg)
                return False, error_msg
                
        # For regular shell commands
        return self._run_adb(['shell'] + args, timeout)
        
    def _get_device(self) -> Optional[AdbDeviceUsb]:
        """Get connected ADB device"""
        try:
            # Try USB devices first
            device = AdbDeviceUsb()
            if self.signer:
                device.connect(rsa_keys=[self.signer], auth_timeout_s=5)
            else:
                device.connect(auth_timeout_s=5)
            return device
            
        except Exception:
            try:
                # Try TCP devices
                success, state = self.get_device_state()
                if success and ':' in state:
                    host, port = state.split(':')
                    device = AdbDeviceTcp(host, int(port))
                    if self.signer:
                        device.connect(rsa_keys=[self.signer], auth_timeout_s=5)
                    else:
                        device.connect(auth_timeout_s=5)
                    return device
                    
            except Exception as e:
                self.error_logger.log_error(f"Failed to connect to device: {str(e)}")
                
        return None
        
    def get_device_state(self) -> Tuple[bool, str]:
        """Get current device state with caching"""
        try:
            # Check cache
            now = time.time()
            if now - self.last_device_check < self.cache_timeout:
                cached = self.device_cache.get('state')
                if cached:
                    return cached
                    
            # Get devices
            devices = self.get_connected_devices()
            
            # Determine result
            if not devices:
                result = (False, "No devices connected")
            elif len(devices) > 1:
                result = (False, "Multiple devices connected")
            else:
                device = devices[0]
                if device['state'] == 'device':
                    result = (True, device['id'])
                else:
                    result = (False, f"Device {device['id']} is {device['state']}")
                    
            # Update cache
            self.device_cache['state'] = result
            self.last_device_check = now
            
            return result
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to get device state: {str(e)}")
            return False, str(e)
        
    def get_installed_apps(self, system_apps: bool = False, force_refresh: bool = False) -> List[Dict]:
        """Get list of installed apps with enhanced info"""
        # Check cache
        now = time.time()
        if not force_refresh and now - self.last_app_refresh < self.cache_timeout:
            cached = self.app_cache.get('apps')
            if cached is not None:
                return cached
                
        # Verify device
        device_ok, msg = self.get_device_state()
        if not device_ok:
            self.error_logger.log_error(f"Cannot get apps: {msg}")
            return []
            
        # Get package list
        success, output = self._run_adb(['shell', 'pm', 'list', 'packages', '-f', '-3'])
        if not success:
            return []
            
        apps = []
        for line in output.split('\n'):
            if not line.strip():
                continue
                
            try:
                # Parse package path and name
                match = re.match(r'package:(.+?)=(.+)$', line.strip())
                if not match:
                    continue
                    
                path, package = match.groups()
                
                # Get app info using separate commands to avoid pipe issues
                app_info = {
                    'name': package,
                    'package': package,
                    'path': path,
                    'system': '/system/' in path,
                    'sdk': None,
                    'cpu_abi': None,
                    'install_time': None
                }
                
                # Get SDK version
                success, sdk_info = self._run_adb(['shell', 'dumpsys', 'package', package, '|', 'grep', 'targetSdk'])
                if success:
                    sdk_match = re.search(r'targetSdk=(\d+)', sdk_info)
                    if sdk_match:
                        app_info['sdk'] = int(sdk_match.group(1))
                        
                # Get CPU ABI
                success, abi_info = self._run_adb(['shell', 'dumpsys', 'package', package, '|', 'grep', 'primaryCpuAbi'])
                if success:
                    abi_match = re.search(r'primaryCpuAbi=(.+)$', abi_info)
                    if abi_match:
                        app_info['cpu_abi'] = abi_match.group(1)
                        
                # Get install time
                success, time_info = self._run_adb(['shell', 'dumpsys', 'package', package, '|', 'grep', 'firstInstallTime'])
                if success:
                    time_match = re.search(r'firstInstallTime=(.+)$', time_info)
                    if time_match:
                        app_info['install_time'] = time_match.group(1)
                        
                # Get app label
                success, label_info = self._run_adb(['shell', 'dumpsys', 'package', package, '|', 'grep', 'android.app.Application'])
                if success:
                    name_match = re.search(r'label="([^"]+)"', label_info)
                    if name_match:
                        app_info['name'] = name_match.group(1)
                        
                # Skip system apps if not requested
                if not system_apps and app_info['system']:
                    continue
                    
                apps.append(app_info)
                
            except Exception as e:
                self.error_logger.log_error(f"Failed to get info for {package}: {str(e)}")
                continue
                
        # Update cache
        self.app_cache['apps'] = apps
        self.last_app_refresh = now
        
        return apps
        
    def get_memory_info(self, package: str) -> Optional[Dict]:
        """Get detailed memory info for an app"""
        device_ok, msg = self.get_device_state()
        if not device_ok:
            return None
            
        success, output = self._run_adb(['shell', 'dumpsys', 'meminfo', package])
        if not success:
            return None
            
        try:
            memory_info = {
                'total': 0,
                'java_heap': 0,
                'native_heap': 0,
                'code': 0,
                'stack': 0,
                'graphics': 0,
                'private_other': 0,
                'system': 0,
                'total_swap': 0
            }
            
            # Parse memory values
            for line in output.split('\n'):
                if 'TOTAL' in line:
                    match = re.search(r'TOTAL\s+(\d+)', line)
                    if match:
                        memory_info['total'] = int(match.group(1)) * 1024
                        
                elif 'Java Heap:' in line:
                    match = re.search(r'Java Heap:\s+(\d+)', line)
                    if match:
                        memory_info['java_heap'] = int(match.group(1)) * 1024
                        
                elif 'Native Heap:' in line:
                    match = re.search(r'Native Heap:\s+(\d+)', line)
                    if match:
                        memory_info['native_heap'] = int(match.group(1)) * 1024
                        
                elif 'Code:' in line:
                    match = re.search(r'Code:\s+(\d+)', line)
                    if match:
                        memory_info['code'] = int(match.group(1)) * 1024
                        
                elif 'Stack:' in line:
                    match = re.search(r'Stack:\s+(\d+)', line)
                    if match:
                        memory_info['stack'] = int(match.group(1)) * 1024
                        
                elif 'Graphics:' in line:
                    match = re.search(r'Graphics:\s+(\d+)', line)
                    if match:
                        memory_info['graphics'] = int(match.group(1)) * 1024
                        
                elif 'Private Other:' in line:
                    match = re.search(r'Private Other:\s+(\d+)', line)
                    if match:
                        memory_info['private_other'] = int(match.group(1)) * 1024
                        
                elif 'System:' in line:
                    match = re.search(r'System:\s+(\d+)', line)
                    if match:
                        memory_info['system'] = int(match.group(1)) * 1024
                        
                elif 'TOTAL SWAP PSS' in line:
                    match = re.search(r'TOTAL SWAP PSS\s+(\d+)', line)
                    if match:
                        memory_info['total_swap'] = int(match.group(1)) * 1024
                        
            return memory_info
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to parse memory info: {str(e)}")
            return None
            
    def get_app_analytics(self, package: str) -> Optional[Dict]:
        """Get comprehensive app analytics"""
        device_ok, msg = self.get_device_state()
        if not device_ok:
            return None
            
        analytics = {}
        
        try:
            # Get CPU usage
            success, output = self._run_adb(['shell', 'top', '-n', '1', '-b'], use_shell=True)
            if success:
                for line in output.split('\n'):
                    if package in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            try:
                                cpu = float(parts[8].replace('%', ''))
                                analytics['cpu'] = cpu
                            except ValueError:
                                pass
                                
            # Get memory usage
            memory = self.get_memory_info(package)
            if memory:
                analytics['memory'] = memory
                
            # Get battery info
            success, output = self._run_adb(['shell', 'dumpsys', 'batterystats', package])
            if success:
                battery_match = re.search(r'Computed drain:\s+(\d+(?:\.\d+)?)', output)
                if battery_match:
                    analytics['battery'] = float(battery_match.group(1))
                    
            # Get network stats
            success, output = self._run_adb(['shell', 'dumpsys', 'netstats', '|', 'grep', package])
            if success:
                rx_match = re.search(r'rx=(\d+)', output)
                tx_match = re.search(r'tx=(\d+)', output)
                if rx_match:
                    analytics['rx_bytes'] = int(rx_match.group(1))
                if tx_match:
                    analytics['tx_bytes'] = int(tx_match.group(1))
                    
            # Get disk usage
            success, output = self._run_adb([
                'shell', 'du', '-b', f'/data/data/{package}', '2>/dev/null'
            ], use_shell=True)
            if success:
                size_match = re.search(r'(\d+)', output)
                if size_match:
                    analytics['disk_usage'] = int(size_match.group(1))
                    
            return analytics
            
        except Exception as e:
            self.error_logger.log_error(f"Failed to get app analytics: {str(e)}")
            return None

    def get_connected_devices(self) -> List[Dict[str, str]]:
        """Get list of connected devices with enhanced error handling"""
        devices = []
        try:
            success, output = self._run_adb(['devices', '-l'])
            if not success:
                self.error_logger.log_error(
                    f"Failed to get device list: {output}",
                    ErrorCode.DEVICE_NOT_CONNECTED
                )
                return []
                
            lines = output.strip().splitlines()
            
            # Verify header line
            if not lines or not lines[0].startswith("List of devices attached"):
                self.error_logger.log_error(
                    "Invalid ADB devices output format",
                    ErrorCode.ADB_COMMAND_FAILED
                )
                return []
                
            # Process device lines
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                # Split on whitespace for extended info
                parts = line.split(None, 2)  # Max 2 splits to handle device info
                
                if len(parts) >= 2:
                    device_id = parts[0]
                    state = parts[1]
                    
                    device_info = {
                        'id': device_id,
                        'state': state
                    }
                    
                    # Parse additional device info if available
                    if len(parts) > 2 and state == 'device':
                        for item in parts[2].split():
                            if ':' in item:
                                key, value = item.split(':', 1)
                                device_info[key] = value
                                
                        self.debug_logger.log_debug(
                            f"Found device: {device_id} ({device_info.get('model', 'Unknown')})",
                            "device",
                            "info"
                        )
                    else:
                        self.debug_logger.log_debug(
                            f"Device in non-ready state: {device_id} ({state})",
                            "device",
                            "warning"
                        )
                        
                    devices.append(device_info)
                else:
                    self.error_logger.log_error(
                        f"Unexpected format in device list: '{line}'",
                        ErrorCode.ADB_COMMAND_FAILED
                    )
                    
        except Exception as e:
            self.error_logger.log_error(
                f"Failed to get device list: {str(e)}",
                ErrorCode.ADB_COMMAND_FAILED
            )
            return []
            
        self.debug_logger.log_debug(
            f"Found {len(devices)} device(s)",
            "device",
            "info"
        )
        return devices

    def check_adb_status(self) -> bool:
        """Check if ADB server is running and device is connected"""
        try:
            # First check if ADB server is running
            success, output = self._run_adb(['start-server'])
            if not success:
                self.error_logger.log_error("Failed to start ADB server")
                return False
                
            # Get device state
            devices = self.get_connected_devices()
            if not devices:
                self.debug_logger.log_debug("No devices connected", "device", "warning")
                return False
                
            # Check for exactly one device in proper state
            connected_devices = [d for d in devices if d['state'] == 'device']
            if not connected_devices:
                self.debug_logger.log_debug("No device in ready state", "device", "warning")
                return False
            elif len(connected_devices) > 1:
                self.debug_logger.log_debug("Multiple devices connected", "device", "warning")
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
            self.error_logger.log_error(f"Error checking device status: {str(e)}")
            return False
            
    @property
    def adb_ready(self) -> bool:
        """Check if ADB is ready for commands"""
        return self.check_adb_status()
