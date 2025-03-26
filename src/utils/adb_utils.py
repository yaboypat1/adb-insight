import subprocess
import re
from typing import List, Tuple, Optional, Dict
import qrcode
from PIL import Image
import tempfile
import os
from PySide6.QtCore import QProcess
import socket
import json
import time
import netifaces
import threading
import ipaddress
from queue import Queue
from .error_utils import ErrorLogger, ErrorCode, ADBError

class ADBUtils:
    """Utility class for ADB operations"""
    
    MIN_ADB_VERSION = "1.0.41"  # Minimum ADB version required
    ADB_DEFAULT_PORT = "5555"
    error_logger = ErrorLogger()
    
    @staticmethod
    def check_adb_installed() -> Tuple[bool, str]:
        """Check if ADB is installed and accessible"""
        try:
            # Try to run adb version
            result = subprocess.run(['adb', 'version'], 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            return True, result.stdout.strip()
            
        except FileNotFoundError:
            msg = "ADB not found in system PATH"
            ADBUtils.error_logger.log_error(msg, ErrorCode.ADB_SERVER_NOT_RUNNING)
            return False, msg
            
        except subprocess.CalledProcessError as e:
            msg = f"ADB command failed: {e.stderr}"
            ADBUtils.error_logger.log_error(msg, ErrorCode.ADB_COMMAND_FAILED)
            return False, msg
            
        except Exception as e:
            msg = f"Unexpected error checking ADB: {str(e)}"
            ADBUtils.error_logger.log_error(msg)
            return False, msg
            
    @staticmethod
    def start_adb_server() -> Tuple[bool, str]:
        """Start the ADB server"""
        try:
            result = subprocess.run(['adb', 'start-server'], 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            return True, "ADB server started successfully"
            
        except subprocess.CalledProcessError as e:
            msg = f"Failed to start ADB server: {e.stderr}"
            ADBUtils.error_logger.log_error(msg, ErrorCode.ADB_SERVER_START_FAILED)
            return False, msg
            
        except Exception as e:
            msg = f"Unexpected error starting ADB server: {str(e)}"
            ADBUtils.error_logger.log_error(msg)
            return False, msg
            
    @staticmethod
    def kill_adb_server() -> Tuple[bool, str]:
        """Kill the ADB server"""
        try:
            result = subprocess.run(['adb', 'kill-server'], 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            return True, "ADB server killed successfully"
            
        except subprocess.CalledProcessError as e:
            msg = f"Failed to kill ADB server: {e.stderr}"
            ADBUtils.error_logger.log_error(msg, ErrorCode.ADB_SERVER_KILL_FAILED)
            return False, msg
            
        except Exception as e:
            msg = f"Unexpected error killing ADB server: {str(e)}"
            ADBUtils.error_logger.log_error(msg)
            return False, msg
            
    @staticmethod
    def _run_adb_command(cmd: List[str], timeout: int = 10) -> Tuple[bool, str, Optional[str]]:
        """Run an ADB command and handle errors"""
        print(f"Running ADB command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return True, result.stdout, None
            else:
                error = result.stderr or "Command failed with no error message"
                print(f"ADB command failed: {error}")
                return False, "", error
        except subprocess.TimeoutExpired:
            error = f"Command timed out after {timeout} seconds"
            print(f"ADB command timeout: {error}")
            return False, "", error
        except Exception as e:
            print(f"ADB command error: {str(e)}")
            return False, "", str(e)

    @staticmethod
    def get_connected_devices() -> List[Tuple[str, str, Optional[str]]]:
        """Get list of connected devices with their states and names"""
        print("Getting connected devices...")
        try:
            # First ensure ADB server is running
            subprocess.run(['adb', 'start-server'], capture_output=True, text=True, timeout=5)
            
            # Get device list
            result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, timeout=5)
            
            devices = []
            lines = result.stdout.strip().split('\n')
            
            # Skip first line (header)
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        device_id = parts[0]
                        state = parts[1]
                        
                        # Try to get device model name
                        model = None
                        model_match = re.search(r'model:(\S+)', line)
                        if model_match:
                            model = model_match.group(1)
                        
                        devices.append((device_id, state, model))
            
            print(f"Found {len(devices)} devices")
            return devices
            
        except Exception as e:
            print(f"Error getting devices: {str(e)}")
            ADBUtils.error_logger.log_error(f"Failed to get connected devices: {str(e)}")
            return []

    @staticmethod
    def get_network_info() -> Tuple[bool, List[Dict[str, str]]]:
        """Get all network interfaces and their IP addresses"""
        print("Getting network information...")
        try:
            networks = []
            interfaces = netifaces.interfaces()
            
            for iface in interfaces:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:  # If interface has IPv4
                    for addr in addrs[netifaces.AF_INET]:
                        if 'addr' in addr and 'netmask' in addr:
                            networks.append({
                                'interface': iface,
                                'ip': addr['addr'],
                                'netmask': addr['netmask']
                            })
            print(f"Found {len(networks)} network interfaces")
            return True, networks
        except Exception as e:
            print(f"Error getting network info: {str(e)}")
            return False, []

    @staticmethod
    def discover_android_devices(progress_callback=None) -> List[Dict[str, str]]:
        """Scan network for Android devices with ADB enabled"""
        print("Discovering Android devices...")
        devices = []
        success, networks = ADBUtils.get_network_info()
        
        if not success:
            return devices
        
        def scan_ip(ip: str, port: str, results: Queue):
            try:
                # Try to connect to the ADB port
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)  # Quick timeout for faster scanning
                result = sock.connect_ex((ip, int(port)))
                sock.close()
                
                if result == 0:  # Port is open
                    # Try ADB connection
                    cmd = ['adb', 'connect', f"{ip}:{port}"]
                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    
                    if "connected" in process.stdout.lower():
                        # Try to get device info
                        info_cmd = ['adb', '-s', f"{ip}:{port}", 'shell', 'getprop']
                        info_process = subprocess.run(info_cmd, capture_output=True, text=True, timeout=2)
                        
                        device_info = {
                            'ip': ip,
                            'port': port,
                            'status': 'available'
                        }
                        
                        # Parse device properties
                        for line in info_process.stdout.split('\n'):
                            if '[ro.product.model]' in line:
                                device_info['model'] = line.split('[')[2].split(']')[0]
                            elif '[ro.product.manufacturer]' in line:
                                device_info['manufacturer'] = line.split('[')[2].split(']')[0]
                        
                        results.put(device_info)
                        
                        # Disconnect after scanning
                        subprocess.run(['adb', 'disconnect', f"{ip}:{port}"], 
                                    capture_output=True, timeout=1)
            except:
                pass

        def scan_network(network: Dict[str, str], results: Queue, progress_callback):
            try:
                ip_network = ipaddress.IPv4Network(
                    f"{network['ip']}/{network['netmask']}", strict=False
                )
                total_ips = sum(1 for _ in ip_network.hosts())
                scanned = 0
                
                threads = []
                for ip in ip_network.hosts():
                    ip_str = str(ip)
                    thread = threading.Thread(
                        target=scan_ip,
                        args=(ip_str, ADBUtils.ADB_DEFAULT_PORT, results)
                    )
                    thread.daemon = True
                    threads.append(thread)
                    thread.start()
                    
                    # Limit concurrent threads
                    while sum(t.is_alive() for t in threads) >= 50:
                        time.sleep(0.1)
                    
                    scanned += 1
                    if progress_callback:
                        progress = (scanned / total_ips) * 100
                        progress_callback(network['interface'], progress)
                
                # Wait for remaining threads
                for thread in threads:
                    thread.join(timeout=0.5)
                
            except Exception as e:
                print(f"Error scanning network {network['interface']}: {str(e)}")

        # Start network scanning
        results = Queue()
        scan_threads = []
        
        for network in networks:
            if network['ip'].startswith('192.168.') or network['ip'].startswith('10.') or network['ip'].startswith('172.'):
                thread = threading.Thread(
                    target=scan_network,
                    args=(network, results, progress_callback)
                )
                thread.daemon = True
                scan_threads.append(thread)
                thread.start()
        
        # Wait for all network scans to complete
        for thread in scan_threads:
            thread.join()
        
        # Collect results
        while not results.empty():
            devices.append(results.get())
        
        print(f"Found {len(devices)} devices")
        return devices

    @staticmethod
    def get_pairing_port() -> Tuple[bool, str, str]:
        """Get the current pairing port from the device"""
        print("Getting pairing port...")
        try:
            # Run adb pair without arguments to see available ports
            result = subprocess.run(
                ['adb', 'pair'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Look for port in the output
            for line in result.stdout.split('\n'):
                if 'port:' in line.lower():
                    # Extract the pairing code from the output
                    port = line.split(':')[1].strip()
                    print(f"Found pairing port: {port}")
                    return True, port, ""
            
            print("Could not find pairing port")
            return False, "", "Could not find pairing port"
        except Exception as e:
            print(f"Error getting pairing port: {str(e)}")
            return False, "", str(e)

    @staticmethod
    def connect_wireless(ip: str, port: str = "5555") -> Tuple[bool, str]:
        """Connect to a device wirelessly using its IP address"""
        print(f"Connecting to {ip}:{port}...")
        try:
            # Validate IP address format
            try:
                socket.inet_aton(ip)
            except socket.error:
                print("Invalid IP address format")
                return False, "Invalid IP address format"
            
            # First try to disconnect any existing connection
            subprocess.run(['adb', 'disconnect', f"{ip}:{port}"], 
                         capture_output=True, text=True, timeout=5)
            
            # Try direct connection
            result = subprocess.run(['adb', 'connect', f"{ip}:{port}"],
                                 capture_output=True, text=True, timeout=10)
            
            # Check for specific connection messages
            output = result.stdout.lower()
            if "connected" in output and "failed" not in output:
                print("Connected successfully")
                return True, "Successfully connected"
            elif "already connected" in output:
                print("Already connected")
                return True, "Device already connected"
            elif "failed" in output:
                if "cannot connect" in output:
                    print("Device refused connection")
                    return False, "Device refused connection. Check if wireless debugging is enabled and the port is correct."
                else:
                    print("Failed to connect")
                    return False, result.stdout.strip()
            else:
                error_msg = result.stdout.strip() or result.stderr.strip() or "Failed to connect"
                print(f"Connection failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            print("Connection attempt timed out")
            return False, "Connection attempt timed out"
        except Exception as e:
            print(f"Error connecting: {str(e)}")
            return False, str(e)

    @staticmethod
    def start_pairing_with_code() -> Tuple[bool, str, str, str]:
        """Start pairing server and return pairing code"""
        print("Starting pairing server...")
        try:
            # Get network information
            success, networks = ADBUtils.get_network_info()
            if not success or not networks:
                print("Could not get network information")
                return False, "Could not get network information", "", ""
            
            # Find the most likely network interface
            local_ip = None
            for network in networks:
                ip = network['ip']
                if (ip.startswith('192.168.') or 
                    ip.startswith('10.') or 
                    ip.startswith('172.')):
                    local_ip = ip
                    break
            
            if not local_ip:
                print("Could not find a suitable network interface")
                return False, "Could not find a suitable network interface", "", ""

            # Get the current pairing port
            port_success, port, port_error = ADBUtils.get_pairing_port()
            if not port_success:
                print(f"Could not get pairing port: {port_error}")
                return False, f"Could not get pairing port: {port_error}", "", ""

            # Start pairing server
            result = subprocess.run(
                ['adb', 'pair', f"{local_ip}:{port}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Parse the output to get the pairing code
            if "Enter pairing code:" in result.stdout:
                # Extract the pairing code from the output
                lines = result.stdout.split('\n')
                code_line = next((line for line in lines if 'Enter pairing code:' in line), None)
                if code_line:
                    pairing_code = code_line.split(':')[1].strip()
                    print(f"Pairing code: {pairing_code}")
                    return True, f"{local_ip}:{port}", pairing_code, local_ip
            
            print("Failed to start pairing server")
            return False, "Failed to start pairing server", "", ""
            
        except Exception as e:
            print(f"Error starting pairing server: {str(e)}")
            return False, str(e), "", ""

    @staticmethod
    def verify_pairing(pairing_code: str, address: str) -> Tuple[bool, str]:
        """Verify the pairing code and attempt connection"""
        print(f"Verifying pairing code for {address}...")
        try:
            # Send pairing code
            process = subprocess.Popen(
                ['adb', 'pair', address],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=f"{pairing_code}\n", timeout=10)
            
            if "Successfully paired" in stdout:
                # Get the device's actual port for connection
                ip = address.split(':')[0]
                
                # Try to get the device's connection port (usually shown in wireless debugging settings)
                port_result = subprocess.run(
                    ['adb', 'devices', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Look for the device's port in the output
                device_port = "5555"  # default
                for line in port_result.stdout.split('\n'):
                    if ip in line:
                        parts = line.split()
                        if len(parts) > 0 and ':' in parts[0]:
                            device_port = parts[0].split(':')[1]
                            break
                
                # Try to connect to the device
                connect_result = subprocess.run(
                    ['adb', 'connect', f"{ip}:{device_port}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "connected" in connect_result.stdout.lower() and "failed" not in connect_result.stdout.lower():
                    print("Paired and connected successfully")
                    return True, "Successfully paired and connected"
                else:
                    print(f"Paired but failed to connect: {connect_result.stdout}")
                    return False, f"Paired but failed to connect: {connect_result.stdout}"
            else:
                error = stderr.strip() or stdout.strip() or "Pairing failed"
                print(f"Pairing failed: {error}")
                return False, error
                
        except subprocess.TimeoutExpired:
            print("Pairing timed out")
            return False, "Pairing timed out"
        except Exception as e:
            print(f"Error pairing: {str(e)}")
            return False, str(e)

    @staticmethod
    def enable_wireless_debugging(device_id: Optional[str] = None) -> Tuple[bool, str]:
        """Enable wireless debugging on a connected device"""
        print("Enabling wireless debugging...")
        try:
            # First check if device is connected via USB
            devices = ADBUtils.get_connected_devices()
            if not devices:
                print("No devices connected via USB")
                return False, "No devices connected via USB. Please connect your device with a USB cable first and ensure USB debugging is enabled."
            
            # Check device state
            device_to_use = None
            for d_id, state, name in devices:
                if device_id and d_id == device_id:
                    device_to_use = d_id
                    if state != "device":
                        print(f"Device {d_id} is not ready (state: {state})")
                        return False, f"Device {d_id} is not ready (state: {state}). Please check USB debugging is enabled."
                    break
                elif not device_id and state == "device":
                    device_to_use = d_id
                    break
            
            if not device_to_use:
                if device_id:
                    print(f"Device {device_id} not found or not authorized")
                    return False, f"Device {device_id} not found or not authorized"
                else:
                    print("No authorized devices found")
                    return False, "No authorized devices found. Please check USB debugging is enabled."
            
            # Get device IP address
            cmd = ['adb']
            if device_to_use:
                cmd.extend(['-s', device_to_use])
            
            # Try both wlan0 and eth0
            ip = None
            for interface in ['wlan0', 'eth0']:
                try:
                    result = subprocess.run(
                        cmd + ['shell', 'ip', 'addr', 'show', interface],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'inet ' in line and not 'inet6' in line:
                                ip = line.split('inet ')[1].split('/')[0].strip()
                                break
                    
                    if ip:
                        break
                except:
                    continue
            
            if not ip:
                print("Could not find device IP address")
                return False, "Could not find device IP address. Please ensure Wi-Fi is enabled on your device."
            
            # Enable TCP/IP mode
            tcp_cmd = ['adb']
            if device_to_use:
                tcp_cmd.extend(['-s', device_to_use])
            tcp_cmd.extend(['tcpip', '5555'])
            
            result = subprocess.run(tcp_cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                print(f"Failed to enable TCP/IP mode: {error_msg}")
                return False, f"Failed to enable TCP/IP mode: {error_msg}"
            
            # Wait for the mode to change
            time.sleep(2)
            
            # Try to connect to the device
            connect_result = subprocess.run(
                ['adb', 'connect', f"{ip}:5555"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "connected" in connect_result.stdout.lower() and "failed" not in connect_result.stdout.lower():
                print("Connected successfully")
                return True, ip
            else:
                error_msg = connect_result.stdout.strip() or connect_result.stderr.strip()
                print(f"Failed to connect: {error_msg}")
                return False, f"Failed to connect: {error_msg}"
            
        except subprocess.TimeoutExpired:
            print("Command timed out")
            return False, "Command timed out. Please try again."
        except Exception as e:
            print(f"Error: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def disconnect_wireless(ip: str, port: str = "5555") -> Tuple[bool, str]:
        """Disconnect from a wireless device"""
        print(f"Disconnecting from {ip}:{port}...")
        try:
            result = subprocess.run(
                ['adb', 'disconnect', f"{ip}:{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "disconnected" in result.stdout.lower():
                print("Disconnected successfully")
                return True, "Successfully disconnected"
            else:
                print(f"Failed to disconnect: {result.stdout}")
                return False, result.stdout.strip() or "Failed to disconnect"
                
        except subprocess.TimeoutExpired:
            print("Disconnect attempt timed out")
            return False, "Disconnect attempt timed out"
        except Exception as e:
            print(f"Error disconnecting: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_local_ip() -> Tuple[bool, str]:
        """Get local IP address"""
        print("Getting local IP address...")
        try:
            # Try all interfaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.'):  # Skip localhost
                            print(f"Found local IP: {ip}")
                            return True, ip
            
            print("No suitable network interface found")
            return False, "No suitable network interface found"
            
        except Exception as e:
            print(f"Error getting local IP: {str(e)}")
            return False, str(e)

    @staticmethod
    def start_pairing(port: str = "5555") -> Tuple[bool, str, Optional[str]]:
        """Start pairing server and generate QR code for wireless debugging"""
        print("Starting pairing server...")
        try:
            # Get network information
            success, networks = ADBUtils.get_network_info()
            if not success or not networks:
                print("Could not get network information")
                return False, "Could not get network information", None
            
            # Find the most likely network interface
            local_ip = None
            for network in networks:
                ip = network['ip']
                if (ip.startswith('192.168.') or 
                    ip.startswith('10.') or 
                    ip.startswith('172.')):
                    local_ip = ip
                    break
            
            if not local_ip:
                print("Could not find a suitable network interface")
                return False, "Could not find a suitable network interface", None
            
            # Format QR code data
            qr_data = f"adb connect {local_ip}:{port}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to temporary file
            temp_dir = tempfile.gettempdir()
            qr_path = os.path.join(temp_dir, "adb_pair_qr.png")
            qr_img.save(qr_path)
            
            print(f"Pairing server started on {local_ip}:{port}")
            return True, f"{local_ip}:{port}", qr_path
            
        except Exception as e:
            print(f"Error starting pairing server: {str(e)}")
            return False, str(e), None

    @staticmethod
    def create_pairing_process(port: str = "5555") -> QProcess:
        """Create a QProcess for handling the pairing server"""
        print("Creating pairing process...")
        process = QProcess()
        process.setProgram("adb")
        process.setArguments(["pair", f":{port}"])
        return process

    @staticmethod
    def restart_adb_server() -> Tuple[bool, str]:
        """Restart the ADB server"""
        kill_success, kill_msg = ADBUtils.kill_adb_server()
        if not kill_success:
            print(f"Failed to kill ADB server: {kill_msg}")
            return False, f"Failed to kill ADB server: {kill_msg}"
        
        time.sleep(1)  # Wait a bit for the server to fully stop
        
        start_success, start_msg = ADBUtils.start_adb_server()
        if not start_success:
            print(f"Failed to start ADB server: {start_msg}")
            return False, f"Failed to start ADB server: {start_msg}"
        
        print("ADB server restarted successfully")
        return True, "ADB server restarted successfully"
