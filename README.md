# ADB Insight - Advanced Android Debug Bridge Tool

A powerful Python-based GUI application for Android app debugging and analysis using ADB (Android Debug Bridge).

## Features

- Device Connection Management
  - Wireless ADB debugging support
  - Auto-reconnection handling
  - Device state monitoring

- App Management
  - List installed apps (system and user apps)
  - App details and metadata
  - Package information

- Performance Monitoring
  - Real-time CPU usage
  - Memory analysis and leak detection
  - Battery consumption tracking
  - Network usage statistics

- Issue Detection
  - Crash monitoring
  - ANR (Application Not Responding) detection
  - Resource usage warnings

## Requirements

- Python 3.12+
- PySide6
- Android Debug Bridge (ADB) tool
- Android device or emulator

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/adb-insight.git
cd adb-insight
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Connect your Android device via USB or wireless ADB
2. Run the application:
```bash
python main.py
```

3. The main window will show:
   - Connected devices
   - Installed apps
   - Performance metrics
   - Debug information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
