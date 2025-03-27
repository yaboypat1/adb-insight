# Known Issues and Error Log

## Critical Issues

### 1. Merge Conflicts in AppTab Implementation
- **Description**: Multiple merge conflicts in app_tab.py causing syntax errors and application failure
  - Multiple instances of merge conflict markers (<<<<<<< HEAD, =======, >>>>>>>)
  - Duplicate class definitions and imports
  - Code structure inconsistencies
  - Invalid decimal literal error in line 1426
- **Components Affected**: 
  - `src/gui/app_tab.py`:
    - Lines 0-19: Multiple import conflicts
    - Lines 20-268: First instance of AppTab class
    - Lines 394-845: Second instance of AppTab class
    - Lines 972-1423: Third instance of AppTab class
    - Lines 1551-2002: Fourth instance of AppTab class
    - Line 1426: Invalid decimal literal error
  - `src/gui/main_window.py`:
    - Line 12: Import error from app_tab.py
    - Lines 0-14: PyQt import inconsistencies
- **Root Causes**:
  - Unresolved merge conflicts from previous commits
  - Multiple versions of the same code
  - Improper merge conflict resolution
  - Git merge markers not properly handled
- **Impact**:
  - Application fails to start due to syntax errors
  - Invalid decimal literal error in app_tab.py
  - Broken imports in main_window.py
  - Multiple class definitions causing confusion
- **Current Status**: Active
  - Need to resolve merge conflicts
  - Clean up duplicate code
  - Restore proper class structure
  - Fix import statements

### 2. PyQt Version Compatibility Issues
- **Description**: Inconsistent PyQt imports and usage across the codebase
  - Mixed usage of PyQt5 and PyQt6 imports
  - Incompatible signal/slot connections
  - UI component initialization issues
- **Components Affected**:
  - `src/workers/thread_worker.py`:
    - Line 1: Using PyQt5.QtCore
    - Lines 3-20: Worker class using PyQt5 signals
  - `src/utils/app_utils.py`:
    - Line 11: Using PyQt6.QtCore
    - Lines 100-150: Signal implementations
  - `src/gui/app_tab.py`:
    - Multiple PyQt version imports throughout file
  - `src/gui/main_window.py`:
    - Lines 2-8: PyQt5 imports
    - Lines 9-15: UI components using PyQt5
- **Root Causes**:
  - Migration between PyQt versions not completed
  - Inconsistent import statements
  - Error code: IMPORT_ERROR when PyQt modules conflict
  - Mixed usage of PyQt5 and PyQt6 signals
- **Impact**:
  - UI components may fail to initialize
  - Signal/slot connections may not work
  - Application stability issues
  - Runtime errors due to version mismatch
- **Current Status**: Active
  - Need to standardize on single PyQt version (preferably PyQt6)
  - Update all imports and class implementations
  - Fix signal/slot connections
  - Test UI component initialization

### 3. Error Handling and Logging System
- **Description**: Improved error handling system implemented but needs integration
  - Comprehensive error codes defined in `error_codes.py`
  - Worker thread error handling in place
  - Logging system for different error types
- **Components Affected**:
  - `src/utils/error_codes.py`:
    - Lines 1-50: Error code definitions
    - Lines 51-100: Error message mappings
  - `src/workers/thread_worker.py`:
    - Lines 10-30: Worker error handling
    - Lines 31-40: Error signals
  - `src/utils/app_utils.py`:
    - Lines 200-250: Error handling implementation
    - Lines 251-300: Logging integration
- **Status**: Implemented but needs testing
  - Error codes and messages defined
  - Worker thread error handling working
  - Logging system functional
  - Need to verify error propagation

## Recent Updates (2025-03-27)
1. Identified exact locations of merge conflicts in app_tab.py
2. Found PyQt version inconsistencies across multiple files
3. Mapped error handling system implementation
4. Added detailed file and line references for all issues
5. Updated error message translations

## Next Steps
1. Resolve merge conflicts in app_tab.py:
   - Remove all merge conflict markers
   - Keep only one instance of AppTab class
   - Fix imports and dependencies
2. Standardize PyQt version:
   - Convert all PyQt5 imports to PyQt6
   - Update signal/slot syntax
   - Test UI components
3. Clean up duplicate code:
   - Remove redundant class definitions
   - Consolidate utility functions
4. Test error handling system:
   - Verify error propagation
   - Check logging functionality
5. Update documentation:
   - Add code comments
   - Update API documentation
   - Document error codes

## Bug Report Template

When reporting bugs, please include:

1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Error messages and stack traces
5. System Information:
   - Python version
   - Operating System
   - PyQt version (specify 5 or 6)
   - Device information (if applicable)
6. File locations and line numbers where the error occurs
7. Recent changes that might have caused the issue
