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
