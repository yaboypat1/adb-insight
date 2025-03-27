import os
import sys
import subprocess
import time
import re
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from typing import List, Dict, Optional, Tuple
import logging

class ADBUtils:
    """Utility class for ADB operations"""
    
    device_state_changed = logging.getLogger('device_state_changed')  # True if device connected
    
    def __init__(self):
        """Initialize ADB utils"""
        self.adb_path = self.find_adb()
        
    def find_adb(self) -> Optional[str]:
        """Find ADB executable path"""
        # First check in adb_tools directory
        adb_tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'adb_tools', 'adb.exe')
        if os.path.exists(adb_tools_path):
            logging.debug(f"ADB executable found at: {adb_tools_path}")
            return adb_tools_path
            
        # Then check in PATH
        try:
            result = subprocess.run(['where', 'adb'], capture_output=True, text=True)
            if result.returncode == 0:
                adb_path = result.stdout.strip().split('\n')[0]
                logging.debug(f"ADB executable found at: {adb_path}")
                return adb_path
        except Exception as e:
            logging.error(f"Error finding ADB in PATH: {str(e)}")
            
        return None
        
    def check_adb_status(self) -> bool:
        """Check if ADB is ready and a device is connected"""
        if not self.adb_path:
            return False
=======
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
>>>>>>> parent of 5c1894b (all current bugs fixed)
            
        except Exception as e:
<<<<<<< HEAD
            logging.error(f"Error checking ADB status: {str(e)}")
            return False
    
    def get_devices(self) -> List[Dict[str, str]]:
        """Get list of connected devices"""
        if not self.adb_path:
            return []
=======
            self.error_logger.log_error(f"Failed to initialize ADB client: {str(e)}", 
                                    ErrorCode.ADB_SERVER_NOT_RUNNING)
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
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
>>>>>>> parent of 5c1894b (all current bugs fixed)
            
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
=======
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
>>>>>>> parent of 5c1894b (all current bugs fixed)
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
            
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            return devices
            
        except Exception as e:
            logging.error(f"Error getting devices: {str(e)}")
            return []
    
    def get_installed_apps(self, include_system: bool = False) -> List[str]:
        """Get list of installed packages"""
        if not self.adb_path:
            return []
=======
        success, output = self._run_adb(['shell', 'dumpsys', 'meminfo', package])
        if not success:
            return None
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
        success, output = self._run_adb(['shell', 'dumpsys', 'meminfo', package])
        if not success:
            return None
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
        success, output = self._run_adb(['shell', 'dumpsys', 'meminfo', package])
        if not success:
            return None
>>>>>>> parent of 5c1894b (all current bugs fixed)
            
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
                    
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            return packages
            
        except Exception as e:
            logging.error(f"Error getting installed apps: {str(e)}")
            return []
    
    def get_app_name(self, package: str) -> Optional[str]:
        """Get app name for package"""
        if not self.adb_path:
            return None
            
        try:
            cmd = [self.adb_path, 'shell', 'dumpsys', 'package', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
=======
                # Split on whitespace for extended info
                parts = line.split(None, 2)  # Max 2 splits to handle device info
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
                # Split on whitespace for extended info
                parts = line.split(None, 2)  # Max 2 splits to handle device info
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
                # Split on whitespace for extended info
                parts = line.split(None, 2)  # Max 2 splits to handle device info
>>>>>>> parent of 5c1894b (all current bugs fixed)
                
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            logging.error(f"Error getting app name: {str(e)}")
            return None
    
    def get_memory_info(self, package: str) -> Optional[Dict]:
        """Get memory info for package"""
        if not self.adb_path:
            return None
=======
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
            self.error_logger.log_error(
                f"Failed to get device list: {str(e)}",
                ErrorCode.ADB_COMMAND_FAILED
            )
            return []
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
            
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
                
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            memory_info = {
                'total_pss': 0,
                'java_heap': 0,
                'native_heap': 0,
                'code': 0,
                'stack': 0,
                'graphics': 0,
                'private_other': 0,
                'system': 0
            }
            
            # Parse memory info
            in_app_summary = False
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # Look for App Summary section
                if 'App Summary' in line:
                    in_app_summary = True
                    continue
                    
                if in_app_summary:
                    # Parse key memory metrics
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip().lower()
                            try:
                                # Extract the first number from the value part
                                value = int(''.join(c for c in parts[1].split()[0] if c.isdigit()))
                                
                                # Map the keys to our dictionary
                                if 'java heap' in key:
                                    memory_info['java_heap'] = value
                                elif 'native heap' in key:
                                    memory_info['native_heap'] = value
                                elif 'code' in key:
                                    memory_info['code'] = value
                                elif 'stack' in key:
                                    memory_info['stack'] = value
                                elif 'graphics' in key:
                                    memory_info['graphics'] = value
                                elif 'private other' in key:
                                    memory_info['private_other'] = value
                                elif 'system' in key:
                                    memory_info['system'] = value
                            except (ValueError, IndexError):
                                continue
                
                # Look for total PSS
                elif 'TOTAL PSS:' in line or 'TOTAL:' in line:
                    try:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit():
                                memory_info['total_pss'] = int(part)
                                break
                    except (ValueError, IndexError):
                        continue
            
            return memory_info
            
        except Exception as e:
            logging.error(f"Error getting memory info: {str(e)}")
            return None
    
    def clear_app_data(self, package: str) -> bool:
        """Clear app data"""
        if not self.adb_path:
            return False
            
        try:
            cmd = [self.adb_path, 'shell', 'pm', 'clear', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error clearing app data: {str(e)}")
            return False
    
    def force_stop_app(self, package: str) -> bool:
        """Force stop app"""
        if not self.adb_path:
            return False
            
        try:
            cmd = [self.adb_path, 'shell', 'am', 'force-stop', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error force stopping app: {str(e)}")
            return False
    
    def uninstall_app(self, package: str) -> bool:
        """Uninstall app"""
        if not self.adb_path:
            return False
            
        try:
            cmd = [self.adb_path, 'uninstall', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error uninstalling app: {str(e)}")
            return False
    
    def get_package_details(self, package: str) -> Optional[Dict]:
        """Get detailed information about a package"""
        if not self.adb_path:
            return None
            
        try:
            # Get package info
            cmd = [self.adb_path, 'shell', 'dumpsys', 'package', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
                
            details = {
                'is_stopped': False,
                'is_disabled': False,
                'is_suspended': False,
                'last_updated': None,
                'version': None,
                'target_sdk': None
            }
            
            output = result.stdout
            
            # Check package flags
            flags_match = re.search(r'pkgFlags=\[\s*(.*?)\s*\]', output)
            if flags_match:
                flags = flags_match.group(1).split()
                details['is_stopped'] = any('STOPPED' in flag for flag in flags)
                details['is_suspended'] = any('SUSPENDED' in flag for flag in flags)
            
            # Check enabled state
            state_match = re.search(r'enabled=(\d+)\s+suspended=(\d+)', output)
            if state_match:
                enabled = state_match.group(1) == '1'
                suspended = state_match.group(2) == '1'
                details['is_disabled'] = not enabled
                details['is_suspended'] = suspended
            else:
                # Try alternate format
                state_match = re.search(r'enabledState=(\d+)', output)
                if state_match:
                    # Android component states:
                    # 0 = DEFAULT (enabled)
                    # 1 = ENABLED
                    # 2 = DISABLED
                    # 3 = DISABLED_USER
                    # 4 = DISABLED_UNTIL_USED
                    state = int(state_match.group(1))
                    details['is_disabled'] = state in [2, 3]  # Only consider explicitly disabled states
                    details['is_suspended'] = state == 4  # DISABLED_UNTIL_USED is more like suspended
            
            # Get version info
            version_match = re.search(r'versionName=([^\s]+)', output)
            if version_match:
                details['version'] = version_match.group(1)
                
            # Get target SDK
            sdk_match = re.search(r'targetSdk=(\d+)', output)
            if sdk_match:
                details['target_sdk'] = int(sdk_match.group(1))
                
            # Get last updated time
            time_match = re.search(r'lastUpdateTime=(\d+)', output)
            if time_match:
                details['last_updated'] = int(time_match.group(1))
            
            return details
            
        except Exception as e:
            logging.error(f"Error getting package details for {package}: {str(e)}")
            return None
    
    def get_app_crashes(self, package: str) -> Dict:
        """Get recent crash information for a package"""
        if not self.adb_path:
            return {}
            
        try:
            # Try exit-info first (Android 11+)
            cmd = [self.adb_path, 'shell', 'dumpsys', 'activity', 'exit-info', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            crashes = {
                'recent_crashes': [],
                'recent_anrs': []
            }
            
            if result.returncode == 0 and 'Exit info for' in result.stdout:
                # Parse exit-info output
                for line in result.stdout.split('\n'):
                    if 'timestamp=' in line:
                        timestamp_match = re.search(r'timestamp=(\d+)', line)
                        reason_match = re.search(r'reason=(\w+)', line)
                        
                        if timestamp_match and reason_match:
                            timestamp = int(timestamp_match.group(1))
                            reason = reason_match.group(1)
                            
                            if reason == 'crash':
                                crashes['recent_crashes'].append({
                                    'timestamp': timestamp,
                                    'type': 'crash'
                                })
                            elif reason == 'anr':
                                crashes['recent_anrs'].append({
                                    'timestamp': timestamp,
                                    'type': 'anr'
                                })
            else:
                # Fallback to logcat for older versions
                cmd = [self.adb_path, 'logcat', '-d', '-b', 'crash', '-T', '100']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if package in line:
                            if 'FATAL EXCEPTION' in line:
                                crashes['recent_crashes'].append({
                                    'timestamp': None,
                                    'type': 'crash'
                                })
                            elif 'ANR in' in line:
                                crashes['recent_anrs'].append({
                                    'timestamp': None,
                                    'type': 'anr'
                                })
            
            return crashes
            
        except Exception as e:
            logging.error(f"Error getting crash info: {str(e)}")
            return {}
    
    def get_resource_usage(self, package: str) -> Dict:
        """Get current resource usage for a package"""
        if not self.adb_path:
            return {}
            
        try:
            # Get process ID first
            cmd = [self.adb_path, 'shell', 'pidof', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
                
            pid = result.stdout.strip()
            if not pid:
                return {}
                
            # Get resource usage with top
            cmd = [self.adb_path, 'shell', 'top', '-n', '1', '-b', '-p', pid]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {}
                
            usage = {
                'cpu_percent': 0.0,
                'rss_kb': 0,
                'vsz_kb': 0
            }
            
            # Parse top output
            for line in result.stdout.split('\n'):
                if pid in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        try:
                            usage['cpu_percent'] = float(parts[8])
                            usage['rss_kb'] = int(parts[5])
                            usage['vsz_kb'] = int(parts[4])
                        except (ValueError, IndexError):
                            pass
                            
            return usage
            
        except Exception as e:
            logging.error(f"Error getting resource usage: {str(e)}")
            return {}
    
    def set_app_enabled_state(self, package: str, enabled: bool) -> bool:
        """Enable or disable an app"""
        if not self.adb_path:
            return False
            
        try:
            cmd = [self.adb_path, 'shell', 'pm', 'disable' if not enabled else 'enable', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error {'enabling' if enabled else 'disabling'} app: {str(e)}")
            return False
    
    def set_app_suspended_state(self, package: str, resume: bool) -> bool:
        """Suspend or resume an app"""
        if not self.adb_path:
            return False
            
        try:
            cmd = [self.adb_path, 'shell', 'am', 'suspend' if not resume else 'resume', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error {'resuming' if resume else 'suspending'} app: {str(e)}")
            return False
    
    def start_wireless_pairing(self) -> Optional[str]:
        """Start wireless pairing and return the pairing code"""
        if not self.adb_path:
            return None
            
        try:
            # Start pairing
            cmd = [self.adb_path, 'pair', '0.0.0.0:37275']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Extract pairing code from output
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Enter' in line and 'pairing code' in line:
                        # Extract the code (usually 6 digits)
                        code = ''.join(c for c in line if c.isdigit())
                        if len(code) == 6:
                            return code
            return None
            
        except Exception as e:
            logging.error(f"Error starting wireless pairing: {str(e)}")
            return None
            
    def pair_wireless_device(self, code: str, ip: str = None, port: int = 37275) -> bool:
        """Complete wireless pairing with the given code"""
        if not self.adb_path:
            return False
            
        try:
            # If IP is provided, use it for pairing
            pair_address = f"{ip}:{port}" if ip else "0.0.0.0:37275"
            
            # Send pairing code
            cmd = [self.adb_path, 'pair', pair_address, code]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and 'Successfully paired' in result.stdout
            
        except Exception as e:
            logging.error(f"Error pairing device: {str(e)}")
            return False
            
    def connect_wireless_device(self, ip: str, port: int = 5555) -> bool:
        """Connect to a wireless device"""
        if not self.adb_path:
            return False
            
        try:
            # Connect to device
            cmd = [self.adb_path, 'connect', f'{ip}:{port}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and 'connected' in result.stdout.lower()
            
        except Exception as e:
            logging.error(f"Error connecting to device: {str(e)}")
            return False
            
    def disconnect_wireless_device(self, ip: str = None, port: int = 5555) -> bool:
        """Disconnect from a wireless device. If no IP is provided, disconnect all."""
        if not self.adb_path:
            return False
            
        try:
            # Disconnect device(s)
            cmd = [self.adb_path, 'disconnect']
            if ip:
                cmd.append(f'{ip}:{port}')
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error disconnecting device: {str(e)}")
            return False

    def run_adb_command(self, args: List[str], timeout: int = 30) -> str:
        """Run an ADB command with the given arguments"""
        if not self.adb_path:
            raise FileNotFoundError("ADB executable not found")
            
        try:
            cmd = [self.adb_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
                
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired as e:
            logging.error(f"ADB command timed out after {timeout}s: {' '.join(cmd)}")
            raise
        except Exception as e:
            logging.error(f"Error running ADB command: {str(e)}")
            raise

    def enable_tcpip(self, device_id: str, port: int = 5555) -> bool:
        """Sets the specified device to listen on a TCP/IP port."""
        logging.info(f"Attempting to enable TCP/IP mode on port {port} for device {device_id}...")
        try:
            # Use -s <device_id> to target the specific USB device
            output = self.run_adb_command(['-s', device_id, 'tcpip', str(port)], timeout=10)
            # Check output for success indication
            if output and "restarting in TCP mode port" in output:
                logging.info(f"Successfully enabled TCP/IP on {device_id}:{port}.")
                return True
            else:
                # May succeed even without specific output on some devices
                logging.warning(f"Enable TCP/IP command ran for {device_id}, output unclear but assuming success: {output}")
                return True # Be optimistic, but user might need to check device
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logging.error(f"Failed to enable TCP/IP mode for {device_id}: {e}")
            return False
        except Exception as e:
            logging.exception(f"Unexpected error enabling TCP/IP for {device_id}: {e}")
            return False

    def get_device_ip(self, device_id: str) -> Optional[str]:
        """Attempts to get the IP address of the device's wlan0 interface via USB."""
        logging.info(f"Attempting to get IP address for device {device_id} via USB...")
        ip_address = None
        try:
            # Use -s <device_id> to target the specific USB device
            # Ensure device has wifi enabled when running this
            output = self.run_adb_command(['-s', device_id, 'shell', 'ip', 'addr', 'show', 'wlan0'], timeout=10)
            if output:
                # Parse output like: "inet 192.168.1.100/24 brd ..."
                match = re.search(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/', output)
                if match:
                    ip_address = match.group(1)
                    logging.info(f"Found IP address {ip_address} for device {device_id}.")
                else:
                    logging.warning(f"Could not parse IP address from 'ip addr show wlan0' output for {device_id}. Is Wi-Fi connected?")
            else:
                logging.warning(f"Command 'ip addr show wlan0' returned no output for {device_id}.")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logging.error(f"Failed to get IP address for {device_id}: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error getting IP for {device_id}: {e}")
        return ip_address

    def connect_wireless(self, ip_address: str, port: int = 5555) -> bool:
        """Connects ADB to a device wirelessly."""
        target = f"{ip_address}:{port}"
        logging.info(f"Attempting to connect wirelessly to {target}...")
        try:
            # Longer timeout for network operations
            output = self.run_adb_command(['connect', target], timeout=25)
            # Check output for success variations
            if output and (f"connected to {target}" in output or f"already connected to {target}" in output):
                logging.info(f"Successfully connected or already connected to {target}.")
                return True
            else:
                # If run_adb_command doesn't raise error but output is not success
                logging.warning(f"Connect command to {target} ran, but output suggests failure: {output}")
                return False
        except subprocess.CalledProcessError as e:
            # Explicit failure from ADB (e.g., connection refused, timeout from ADB side)
            logging.error(f"Failed to connect to {target}. Error: {e.stderr or e.stdout or e}")
            return False
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout waiting for connect command to {target} to finish.")
            return False
        except FileNotFoundError as e:
            logging.error(f"Failed to connect: ADB command not found: {e}")
            return False
        except Exception as e:
            logging.exception(f"Unexpected error connecting to {target}: {e}")
            return False

    def disconnect_wireless(self, ip_address: str, port: int = 5555) -> bool:
        """Disconnects ADB from a specific wireless device."""
        target = f"{ip_address}:{port}"
        logging.info(f"Attempting to disconnect from {target}...")
        try:
            output = self.run_adb_command(['disconnect', target], timeout=10)
            # Check output
            if output and f"disconnected {target}" in output:
                logging.info(f"Successfully disconnected from {target}.")
                return True
            else:
                # Might return nothing or error if not connected - treat absence of error as success?
                logging.warning(f"Disconnect command for {target} output unclear, assuming success if no error raised: {output}")
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logging.error(f"Failed to disconnect from {target}: {e}")
            return False
        except Exception as e:
            logging.exception(f"Unexpected error disconnecting from {target}: {e}")
            return False

    def is_server_running(self) -> bool:
        """Check if ADB server is running"""
        try:
            result = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error checking ADB server status: {str(e)}")
            return False

    def get_installed_packages(self, device_id: str) -> List[Dict[str, str]]:
        """Get list of installed packages on device with details"""
        packages = []
        
        try:
            # Get package list
            _, stdout, _ = self._run_command(['-s', device_id, 'shell', 'pm', 'list', 'packages', '-f', '-3'])
            
            for line in stdout.split('\n'):
                if not line.strip():
                    continue
                    
                # Parse package line
                # Format: package:/data/app/com.example.app-hash/base.apk=com.example.app
                match = re.match(r'package:(.+)=(.+)', line.strip())
                if match:
                    apk_path, package_name = match.groups()
                    
                    # Get detailed package info using dumpsys
                    _, dump_out, _ = self._run_command(['-s', device_id, 'shell', 'dumpsys', 'package', package_name])
                    
                    package_info = {
                        'name': package_name,
                        'path': apk_path,
                        'version': 'Unknown',
                        'size': '0 B',
                        'status': 'Unknown'
                    }
                    
                    # Get version
                    version_match = re.search(r'versionName=([^\s]+)', dump_out)
                    if version_match:
                        package_info['version'] = version_match.group(1)
                    
                    # Get package size using ls -l
                    _, size_out, _ = self._run_command(['-s', device_id, 'shell', f'ls -l "{apk_path}"'])
                    if size_out:
                        # Parse ls output format: -rw-r--r-- 1 system system 1234567 2024-01-01 12:00 /path/to/file
                        parts = size_out.split()
                        if len(parts) >= 5:
                            try:
                                size_bytes = int(parts[4])  # Size is usually the 5th field
                                package_info['size'] = self._format_size(size_bytes)
                            except (ValueError, IndexError):
                                pass
                    
                    # Determine package status
                    if 'SYSTEM' in dump_out:
                        package_info['status'] = 'System'
                    elif 'DISABLED' in dump_out or 'disabled=1' in dump_out:
                        package_info['status'] = 'Disabled'
                    else:
                        package_info['status'] = 'User'
                    
                    packages.append(package_info)
            
            return packages
            
        except Exception as e:
            logging.error(f"Error getting installed packages: {str(e)}")
            return []
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes into human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def launch_app(self, device_id: str, package_name: str) -> bool:
        """Launch an app on the device"""
        try:
            # Get the main activity
            _, stdout, _ = self._run_command(['-s', device_id, 'shell', 'cmd', 'package', 'resolve-activity', '--brief', package_name])
            activity = stdout.strip()
            
            if not activity:
                # Try dumpsys to find launcher activity
                _, stdout, _ = self._run_command(['-s', device_id, 'shell', 'dumpsys', 'package', package_name, '|', 'grep', '-A', '1', 'android.intent.category.LAUNCHER'])
                match = re.search(r'([^\s]+)/[^\s]+', stdout)
                if match:
                    activity = match.group(1)
            
            if activity:
                returncode, _, stderr = self._run_command(['-s', device_id, 'shell', 'am', 'start', '-n', activity])
                return returncode == 0 and not stderr
            else:
                logging.error(f"Could not find main activity for {package_name}")
                return False
                
        except Exception as e:
            logging.error(f"Error launching app {package_name}: {str(e)}")
            return False

    def uninstall_package(self, device_id: str, package_name: str) -> bool:
        """Uninstall an app from the device"""
        try:
            returncode, stdout, stderr = self._run_command(['-s', device_id, 'uninstall', package_name])
            return returncode == 0 and 'Success' in stdout
        except Exception as e:
            logging.error(f"Error uninstalling package {package_name}: {str(e)}")
            return False

    def disable_app(self, device_id: str, package_name: str) -> bool:
        """Disable an app on the device"""
        try:
            returncode, _, stderr = self._run_command(['-s', device_id, 'shell', 'pm', 'disable-user', '--user', '0', package_name])
            return returncode == 0 and not stderr
        except Exception as e:
            logging.error(f"Error disabling app {package_name}: {str(e)}")
            return False

    def _run_command(self, command: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Run an ADB command and return exit code, stdout, and stderr"""
        try:
            # Create full command with ADB path
            full_command = [self.adb_path] + command
            
            # Run command and capture output
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for process to complete
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout.strip(), stderr.strip()
            
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def get_package_details_with_size(self, package: str, device_id: str) -> Optional[Dict]:
        """Get detailed information about a package with size"""
        if not self.adb_path:
            return None
            
        try:
            # Get package info
            _, stdout, _ = self._run_command(['-s', device_id, 'shell', 'dumpsys', 'package', package])
            
            if not stdout:
                return None
                
            details = {
                'is_stopped': False,
                'is_disabled': False,
                'is_suspended': False,
                'last_updated': None,
                'version': None,
                'target_sdk': None,
                'size': None
            }
            
            output = stdout
            
            # Check package flags
            flags_match = re.search(r'pkgFlags=\[\s*(.*?)\s*\]', output)
            if flags_match:
                flags = flags_match.group(1).split()
                details['is_stopped'] = any('STOPPED' in flag for flag in flags)
                details['is_suspended'] = any('SUSPENDED' in flag for flag in flags)
            
            # Check enabled state
            state_match = re.search(r'enabled=(\d+)\s+suspended=(\d+)', output)
            if state_match:
                enabled = state_match.group(1) == '1'
                suspended = state_match.group(2) == '1'
                details['is_disabled'] = not enabled
                details['is_suspended'] = suspended
            else:
                # Try alternate format
                state_match = re.search(r'enabledState=(\d+)', output)
                if state_match:
                    # Android component states:
                    # 0 = DEFAULT (enabled)
                    # 1 = ENABLED
                    # 2 = DISABLED
                    # 3 = DISABLED_USER
                    # 4 = DISABLED_UNTIL_USED
                    state = int(state_match.group(1))
                    details['is_disabled'] = state in [2, 3]  # Only consider explicitly disabled states
                    details['is_suspended'] = state == 4  # DISABLED_UNTIL_USED is more like suspended
            
            # Get version info
            version_match = re.search(r'versionName=([^\s]+)', output)
            if version_match:
                details['version'] = version_match.group(1)
                
            # Get target SDK
            sdk_match = re.search(r'targetSdk=(\d+)', output)
            if sdk_match:
                details['target_sdk'] = int(sdk_match.group(1))
                
            # Get last updated time
            time_match = re.search(r'lastUpdateTime=(\d+)', output)
            if time_match:
                details['last_updated'] = int(time_match.group(1))
            
            # Get package size
            _, size_out, _ = self._run_command(['-s', device_id, 'shell', 'du', '-k', '/data/app/' + package])
            if size_out:
                try:
                    size_kb = int(size_out.split()[0])
                    details['size'] = size_kb * 1024  # Convert KB to bytes
                except (ValueError, IndexError):
                    details['size'] = 'Unknown'
            else:
                details['size'] = 'Unknown'
            
            return details
            
        except Exception as e:
            logging.error(f"Error getting package details for {package}: {str(e)}")
            return None
=======
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
            
=======
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
            
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
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
            
>>>>>>> parent of 5c1894b (all current bugs fixed)
    @property
    def adb_ready(self) -> bool:
        """Check if ADB is ready for commands"""
        return self.check_adb_status()
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
=======
>>>>>>> parent of 5c1894b (all current bugs fixed)
