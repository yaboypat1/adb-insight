# Known Issues and Error Log

## Critical Issues

### 1. ADB Command Execution Issues
- **Description**: Problems with ADB command execution
  - Shell commands with pipes failing with "too many values to unpack (expected 3)" error
  - Device state checking errors in `get_device_state()`
  - Command execution failing when using grep or other shell operators
- **Components Affected**: 
  - `src/utils/adb_utils.py:_run_adb()` - Line ~97-131
  - `src/utils/adb_utils.py:get_device_state()` - Line ~162-216
  - `src/utils/app_utils.py:_verify_device()` - Line ~522-541
  - `src/gui/app_tab.py:_check_adb_status()` - Line ~383-392
- **Root Causes**:
  - Shell command parsing issues in `_run_adb()` when using pipe operators (|, >, <)
  - Improper handling of subprocess.run() with shell=True
  - Device state synchronization problems between ADBUtils and AppUtils
  - Error code: DEVICE_NOT_CONNECTED when device state check fails
  - Error code: ADB_SERVER_NOT_RUNNING when ADB server fails to start
- **Impact**:
  - Unreliable device detection (Error logs in debug_logger with category="device")
  - Failed app list refreshes (Error code: APP_LIST_REFRESH_FAILED)
  - Inconsistent device status display in UI
  - Command timeouts after 10 seconds
- **Current Status**: Active
  - Working on fixing shell command execution in `src/utils/adb_utils.py`
  - Error logs can be found in `logs/adb_error.log`
  - Stack traces show issues in subprocess.run() calls

### 2. Device Connection Status Issues
- **Description**: Device connection state not properly tracked
  - Connection status updates unreliable with error "Error checking device status"
  - Multiple device handling issues when more than one device is connected
  - State changes not properly propagated through signal system
- **Components Affected**:
  - `src/utils/app_utils.py:_verify_device()` - Line ~522-541
  - `src/utils/adb_utils.py:get_connected_devices()` - Line ~443-483
  - `src/gui/app_tab.py:_on_device_state_changed()` - Line ~130-169
- **Root Causes**:
  - Asynchronous state updates not coordinated between threads
  - Device state caching issues (cache timeout: 5 seconds)
  - Error handling gaps in device state transitions
  - Error code: MULTIPLE_DEVICES when multiple devices detected
  - Error code: DEVICE_STATE_MISMATCH when state is inconsistent
- **Impact**:
  - Inconsistent UI state in AppTab
  - Failed operations due to device state mismatch
  - Poor user experience with delayed updates
  - Errors logged in `logs/device_state.log`
- **Current Status**: Active
  - Implementing improved state management in ADBUtils
  - Adding comprehensive error logging
  - Error tracking system records in `logs/error_tracking.db`

### 3. Dependency and Import Conflicts
- **Description**: Conflicts between ADB libraries and Qt framework dependencies
  - PyQt6/PySide6 mismatch in requirements.txt
  - Conflicting imports between pure-python-adb and adb-shell libraries
  - Module import errors during application startup
- **Components Affected**: 
  - `requirements.txt` - Line ~1
  - `src/utils/adb_utils.py` - Line ~8-11
  - `src/gui/main_window.py` - Line ~9
- **Root Causes**:
  - Requirements file specified PySide6 but codebase uses PyQt6
  - Mixed usage of incompatible ADB libraries:
    - `from adb.adb_commands import AdbCommands` (pure-python-adb)
    - `from adb_shell.adb_device import AdbDeviceUsb, AdbDeviceTcp` (adb-shell)
  - Error code: SYSTEM_RESOURCE_ERROR when dependencies conflict
  - Error code: UNKNOWN_ERROR during import failures
- **Impact**:
  - Application fails to start
  - ModuleNotFoundError: No module named 'adb'
  - Inconsistent ADB command execution
  - Potential stability issues if both libraries are used
- **Current Status**: Active
  - Requirements.txt updated to use PyQt6
  - Need to standardize on single ADB library
  - Error logs show import failures in startup sequence
  - Stack traces indicate module import conflicts

### Log Analysis (2025-03-26)

#### Error Log Samples
From `logs/errors.log`:
```
2025-03-26 18:32:57 - ERROR - [UNKNOWN_ERROR] Error checking device status: too many values to unpack (expected 3)
Context: None
Stack: None
```

#### Application Logs
1. **ADB Insight Daily Logs**:
   - `logs/adb_insight_20250326.log` (171.8 KB)
   - `logs/adb_insight_20250325.log` (88.3 MB)
   - Contains detailed application activity and debugging information
   
2. **Error Logs**:
   - `logs/errors.log` (140.0 KB)
   - Tracks critical errors and exceptions
   - Shows patterns of:
     - Device connection failures
     - Import errors during startup
     - ADB command execution issues

3. **Log Analysis Summary**:
   - High volume of device status check errors
   - Frequent import-related crashes during startup
   - Multiple instances of command parsing failures
   - Large log file (88.3 MB) from March 25 indicates potential issue with log rotation

4. **Debug Information**:
   - Application startup attempts: Multiple
   - Common error patterns:
     - ModuleNotFoundError: No module named 'adb'
     - Device status check failures
     - Command parsing errors
   - Error frequency: High during startup phase

## Bug Report Template

When reporting bugs, please include:

1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. ADB version being used
5. Full error messages and logs from:
   - `logs/adb_error.log`
   - `logs/device_state.log`
   - `logs/app_debug.log`
6. Screenshots if applicable
7. Recent device connection history from `logs/connection_history.db`
8. System Information:
   - Python version
   - Operating System
   - ADB version (`adb version`)
   - Device information (`adb devices -l`)
