#!/bin/bash
# Raspberry Pi Setup Script for Person-Following Drone
# This script installs all necessary dependencies and configures the system

set -e  # Exit on any error

echo "🚁 Setting up Raspberry Pi for Person-Following Drone Project"
echo "================================================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    cmake \
    build-essential \
    libatlas-base-dev \
    libjasper-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libgtk-3-dev \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    unzip \
    htop \
    vim \
    screen \
    tmux

# Enable camera interface
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C interface
echo "🔌 Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Enable SPI interface
echo "🔌 Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# Enable serial interface (disable login shell)
echo "🔌 Configuring serial interface..."
sudo raspi-config nonint do_serial 1

# Set GPU memory split (for OpenCV)
echo "🎮 Setting GPU memory split..."
sudo raspi-config nonint do_memory_split 128

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/drone_project
cd ~/drone_project

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv drone_env
source drone_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."

# Core dependencies
pip install \
    numpy \
    opencv-python \
    opencv-contrib-python \
    pillow \
    matplotlib \
    scipy

# Machine learning dependencies
pip install \
    torch \
    torchvision \
    torchaudio \
    ultralytics \
    onnx \
    onnxruntime

# Drone control dependencies
pip install \
    mavsdk \
    pymavlink \
    pyserial \
    pynmea2

# Camera dependencies
pip install \
    picamera2 \
    picamera

# Utility dependencies
pip install \
    requests \
    websockets \
    asyncio-mqtt \
    paho-mqtt \
    psutil \
    pyyaml \
    click \
    rich

# Install specific versions for compatibility
echo "📦 Installing specific package versions..."
pip install \
    "opencv-python==4.8.1.78" \
    "numpy==1.24.3" \
    "torch==2.0.1" \
    "torchvision==0.15.2"

# Download YOLOv8 model
echo "🧠 Downloading YOLOv8 model..."
mkdir -p models
cd models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
cd ..

# Create configuration files
echo "⚙️  Creating configuration files..."
cat > config.yaml << 'EOF'
# Drone Configuration File
drone:
  name: "PersonFollowingDrone"
  model: "ZMR250"
  
# Camera Configuration
camera:
  type: "PiCamera2"  # or "USB"
  resolution: [640, 480]
  fps: 30
  rotation: 0
  
# Person Detection Configuration
detection:
  model: "models/yolov8n.pt"
  confidence_threshold: 0.5
  nms_threshold: 0.4
  target_size: 200  # pixels
  
# Flight Control Configuration
flight:
  max_velocity: 3.0  # m/s
  max_yaw_rate: 45.0  # degrees/s
  safe_altitude: 5.0  # meters
  max_following_distance: 10.0  # meters
  min_safe_distance: 2.0  # meters
  
# Safety Configuration
safety:
  max_flight_time: 600  # seconds
  low_battery_threshold: 20  # percent
  max_altitude: 30.0  # meters
  min_altitude: 2.0  # meters
  emergency_landing_altitude: 1.0  # meters
  
# Communication Configuration
communication:
  flight_controller: "udp://:14540"
  telemetry_rate: 10  # Hz
  offboard_rate: 20  # Hz
  
# Logging Configuration
logging:
  level: "INFO"
  file: "drone_following.log"
  max_size: "10MB"
  backup_count: 5
EOF

# Create systemd service file
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/drone-following.service > /dev/null << 'EOF'
[Unit]
Description=Person Following Drone Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/drone_project
Environment=PATH=/home/pi/drone_project/drone_env/bin
ExecStart=/home/pi/drone_project/drone_env/bin/python main_integration.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable drone-following.service

# Create startup script
echo "📜 Creating startup script..."
cat > start_drone.sh << 'EOF'
#!/bin/bash
# Startup script for Person-Following Drone

cd ~/drone_project
source drone_env/bin/activate

echo "🚁 Starting Person-Following Drone System..."
echo "Press Ctrl+C to stop"

# Check if flight controller is connected
echo "🔌 Checking flight controller connection..."
if ! ping -c 1 192.168.1.1 > /dev/null 2>&1; then
    echo "⚠️  Warning: Flight controller not reachable"
    echo "Make sure telemetry is connected and configured"
fi

# Start the main system
python main_integration.py
EOF

chmod +x start_drone.sh

# Create test script
echo "🧪 Creating test script..."
cat > test_system.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Person-Following Drone System
Tests individual components without flying
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_camera():
    """Test camera functionality"""
    print("📷 Testing camera...")
    try:
        from computer_vision.person_detector import PersonDetector
        detector = PersonDetector()
        print("✅ Camera test passed")
        detector.cleanup()
        return True
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_yolo():
    """Test YOLOv8 model"""
    print("🧠 Testing YOLOv8 model...")
    try:
        from ultralytics import YOLO
        model = YOLO('models/yolov8n.pt')
        print("✅ YOLOv8 test passed")
        return True
    except Exception as e:
        print(f"❌ YOLOv8 test failed: {e}")
        return False

def test_mavsdk():
    """Test MAVSDK installation"""
    print("🔌 Testing MAVSDK...")
    try:
        from mavsdk import System
        print("✅ MAVSDK test passed")
        return True
    except Exception as e:
        print(f"❌ MAVSDK test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running system tests...")
    print("=" * 40)
    
    tests = [
        test_camera,
        test_yolo,
        test_mavsdk
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test_system.py

# Create requirements.txt
echo "📋 Creating requirements.txt..."
pip freeze > requirements.txt

# Set up environment variables
echo "🌍 Setting up environment variables..."
cat >> ~/.bashrc << 'EOF'

# Drone Project Environment Variables
export DRONE_PROJECT_DIR="$HOME/drone_project"
export DRONE_VENV="$HOME/drone_project/drone_env"
export PYTHONPATH="$DRONE_PROJECT_DIR:$PYTHONPATH"

# Add drone scripts to PATH
export PATH="$DRONE_PROJECT_DIR:$PATH"

# Activate virtual environment automatically
alias activate_drone="source $DRONE_VENV/bin/activate"
alias start_drone="cd $DRONE_PROJECT_DIR && ./start_drone.sh"
alias test_drone="cd $DRONE_PROJECT_DIR && python test_system.py"
EOF

# Create desktop shortcut
echo "🖥️  Creating desktop shortcut..."
cat > ~/Desktop/Start\ Drone.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Start Person Following Drone
Comment=Start the autonomous person following drone system
Exec=/home/pi/drone_project/start_drone.sh
Icon=applications-engineering
Terminal=true
Categories=Development;Engineering;
EOF

chmod +x ~/Desktop/Start\ Drone.desktop

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/drone-following > /dev/null << 'EOF'
/home/pi/drone_project/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 pi pi
    postrotate
        systemctl reload drone-following.service
    endscript
}
EOF

# Create backup script
echo "💾 Creating backup script..."
cat > backup_drone.sh << 'EOF'
#!/bin/bash
# Backup script for drone project

BACKUP_DIR="$HOME/drone_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="drone_backup_$DATE.tar.gz"

echo "💾 Creating backup: $BACKUP_NAME"

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude='drone_env' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_NAME"

# Clean up old backups (keep last 5)
cd "$BACKUP_DIR"
ls -t drone_backup_*.tar.gz | tail -n +6 | xargs -r rm

echo "🧹 Cleaned up old backups"
EOF

chmod +x backup_drone.sh

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > monitor_drone.py << 'EOF'
#!/usr/bin/env python3
"""
Drone System Monitor
Monitors system resources and drone status
"""

import psutil
import time
import os
import subprocess
from datetime import datetime

def get_system_info():
    """Get system resource information"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used': memory.used / (1024**3),  # GB
        'disk_percent': disk.percent,
        'disk_free': disk.free / (1024**3)  # GB
    }

def get_drone_status():
    """Get drone service status"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'drone-following.service'], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "unknown"

def get_temperature():
    """Get Raspberry Pi temperature"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read()) / 1000.0
        return temp
    except:
        return None

def main():
    """Main monitoring loop"""
    print("📊 Drone System Monitor")
    print("=" * 30)
    
    try:
        while True:
            # Clear screen
            os.system('clear')
            
            # Get system info
            sys_info = get_system_info()
            drone_status = get_drone_status()
            temp = get_temperature()
            
            # Display information
            print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🚁 Drone Service: {drone_status}")
            print()
            print("💻 System Resources:")
            print(f"   CPU Usage: {sys_info['cpu']:.1f}%")
            print(f"   Memory: {sys_info['memory_percent']:.1f}% ({sys_info['memory_used']:.1f} GB)")
            print(f"   Disk: {sys_info['disk_percent']:.1f}% ({sys_info['disk_free']:.1f} GB free)")
            
            if temp:
                print(f"🌡️  Temperature: {temp:.1f}°C")
            
            print()
            print("Press Ctrl+C to exit")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    main()
EOF

chmod +x monitor_drone.py

# Final setup
echo "🎯 Final setup..."
source ~/.bashrc

# Test the setup
echo "🧪 Testing setup..."
cd ~/drone_project
source drone_env/bin/activate
python test_system.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your flight controller via USB or telemetry"
echo "2. Test the system: python test_system.py"
echo "3. Start the drone: ./start_drone.sh"
echo "4. Monitor system: python monitor_drone.py"
echo ""
echo "📁 Project directory: ~/drone_project"
echo "🐍 Virtual environment: ~/drone_project/drone_env"
echo "📝 Logs: ~/drone_project/drone_following.log"
echo ""
echo "🔧 Useful commands:"
echo "  activate_drone  - Activate virtual environment"
echo "  start_drone     - Start the drone system"
echo "  test_drone      - Run system tests"
echo "  backup_drone    - Create backup"
echo ""
echo "⚠️  Remember to:"
echo "- Test in safe, open areas"
echo "- Follow local drone regulations"
echo "- Keep kill switch accessible"
echo "- Monitor battery levels"
echo ""
echo "Happy flying! 🚁✈️"
