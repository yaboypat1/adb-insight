from setuptools import setup, find_packages

setup(
    name="adb-insight",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.8.0',
        'adb>=1.3.0',
        'adb-shell>=0.4.3',
        'psutil>=5.9.0',
        'humanize>=4.6.0',
        'python-dateutil>=2.8.2',
        'pyusb>=1.2.1',
        'packaging>=23.1',
        'colorama>=0.4.6',
        'tqdm>=4.65.0',
        'retry>=0.9.2',
        'qrcode>=7.4.2',
        'pillow>=10.0.0',
        'netifaces>=0.11.0'
    ],
    python_requires='>=3.7',
)
