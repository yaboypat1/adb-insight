import os
import subprocess
import json
import time
from typing import List, Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

from .debug_utils import DebugLogger
from .error_utils import ErrorLogger, ErrorCode

class ADBUtils(QObject):
    """Utility class for ADB operations"""
    
    device_state_changed = pyqtSignal(bool)  # True if device connected
    
    def __init__(self, debug_logger: DebugLogger, error_logger: ErrorLogger):
        super().__init__()
        self.debug_logger = debug_logger
        self.error_logger = error_logger
        
        # Get ADB path
        self.adb_path = self._get_adb_path()
        if self.adb_path:
            self.debug_logger.log_debug(f"ADB executable found at: {self.adb_path}")
        else:
            self.error_logger.log_error("ADB executable not found", ErrorCode.ADB_NOT_FOUND)
    
    def _get_adb_path(self) -> Optional[str]:
        """Get path to ADB executable"""
        # First check our local adb_tools directory
        local_adb = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                'adb_tools', 'adb.exe')
        if os.path.exists(local_adb):
            return local_adb
            
        # Then check system PATH
        try:
            result = subprocess.run(['where', 'adb'], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
            
        return None
    
    def check_adb_status(self) -> bool:
        """Check if ADB is ready and a device is connected"""
        if not self.adb_path:
            return False
            
        try:
            devices = self.get_devices()
            return len([d for d in devices if d['state'] == 'device']) > 0
        except Exception as e:
            self.error_logger.log_error(f"Error checking ADB status: {str(e)}")
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
            self.error_logger.log_error(f"Error getting devices: {str(e)}")
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
            self.error_logger.log_error(f"Error getting installed apps: {str(e)}")
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
            self.error_logger.log_error(f"Error getting app name: {str(e)}")
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
                
            # Parse memory info
            total_pss = 0
            for line in result.stdout.split('\n'):
                if 'TOTAL:' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            total_pss = int(parts[1])
                            break
                        except ValueError:
                            pass
                            
            return {'total_pss': total_pss}
            
        except Exception as e:
            self.error_logger.log_error(f"Error getting memory info: {str(e)}")
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
            self.error_logger.log_error(f"Error clearing app data: {str(e)}")
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
            self.error_logger.log_error(f"Error force stopping app: {str(e)}")
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
            self.error_logger.log_error(f"Error uninstalling app: {str(e)}")
            return False
