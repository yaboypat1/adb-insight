import os
import subprocess
import json
import time
import re
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
            
        try:
            devices = self.get_devices()
            return len([d for d in devices if d['state'] == 'device']) > 0
        except Exception as e:
            logging.error(f"Error checking ADB status: {str(e)}")
            return False
    
    def get_devices(self) -> List[Dict[str, str]]:
        """Get list of connected devices"""
        if not self.adb_path:
            return []
            
        try:
            result = subprocess.run([self.adb_path, 'devices', '-l'],
                                 capture_output=True,
                                 text=True)
            
            if result.returncode != 0:
                return []
                
            devices = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip first line
            
            for line in lines:
                if not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    device = {
                        'id': parts[0],
                        'state': parts[1],
                        'model': next((p.split(':')[1] for p in parts[2:] 
                                    if p.startswith('model:')), 'Unknown')
                    }
                    devices.append(device)
            
            return devices
            
        except Exception as e:
            logging.error(f"Error getting devices: {str(e)}")
            return []
    
    def get_installed_apps(self, include_system: bool = False) -> List[str]:
        """Get list of installed packages"""
        if not self.adb_path:
            return []
            
        try:
            cmd = [self.adb_path, 'shell', 'pm', 'list', 'packages']
            if not include_system:
                cmd.append('-3')  # Only third-party apps
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return []
                
            packages = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('package:'):
                    packages.append(line[8:])  # Remove 'package:' prefix
                    
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
                
            # Try to find app name in output
            for line in result.stdout.split('\n'):
                if 'android.intent.action.MAIN:' in line:
                    parts = line.split('/')
                    if len(parts) > 1:
                        return parts[1].strip()
                        
            return None
            
        except Exception as e:
            logging.error(f"Error getting app name: {str(e)}")
            return None
    
    def get_memory_info(self, package: str) -> Optional[Dict]:
        """Get memory info for package"""
        if not self.adb_path:
            return None
            
        try:
            cmd = [self.adb_path, 'shell', 'dumpsys', 'meminfo', package]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
                
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
