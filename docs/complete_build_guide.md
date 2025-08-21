# Complete Drone Build Guide

## 🛠️ Phase 1: Frame Assembly

### 1.1 Motor Installation
- Mount 2207 motors to frame arms using M3 screws
- Ensure proper motor direction (clockwise/counter-clockwise)
- Use threadlocker on motor screws
- Route motor wires through frame arms

### 1.2 ESC Installation
- Mount ESCs on frame arms near motors
- Use double-sided tape or zip ties for mounting
- Route ESC signal wires to flight controller
- Ensure proper ESC orientation for cooling

### 1.3 Flight Controller Mounting
- Install vibration dampening grommets
- Mount F7 FC to center plate
- Ensure level mounting for proper sensor calibration
- Route all wires through center hole

### 1.4 GPS Module Installation
- Mount GPS on top plate for clear sky view
- Use M3 standoffs for proper height
- Route GPS cable to FC UART port
- Ensure GPS antenna faces upward

### 1.5 Raspberry Pi Mounting
- Install Pi on top plate with cooling system
- Use M3 standoffs for proper ventilation
- Mount camera securely to Pi
- Ensure all Pi connections are accessible

## 🔌 Phase 2: Electrical Wiring

### 2.1 Power Distribution
```
Battery → XT60 → PDB → ESCs (4S)
                ↓
            UBEC → Raspberry Pi (5V)
```

### 2.2 ESC Connections
- Connect ESC power leads to PDB
- Route ESC signal wires to FC motor outputs
- Ensure proper motor numbering (1-4)
- Test motor direction before final assembly

### 2.3 Flight Controller Power
- Connect FC to PDB for main power
- Install 5V BEC for FC logic power
- Connect GPS to FC UART port
- Install telemetry radio to FC

### 2.4 Raspberry Pi Power
- Connect 5V UBEC to Pi power pins
- Ensure stable 5V supply (3-5A capacity)
- Connect Pi to FC via USB or UART
- Install camera to Pi CSI port

### 2.5 Receiver Installation
- Connect FlySky receiver to FC
- Configure iBus protocol in FC
- Test all control channels
- Set up failsafe configuration

## 💻 Phase 3: Software Configuration

### 3.1 Flight Controller Setup
1. **Flash ArduPilot Firmware**
   - Download ArduPilot firmware for your F7 FC
   - Use Mission Planner or QGroundControl
   - Select "ArduCopter" as vehicle type

2. **Basic Configuration**
   - Set frame type to "Quad"
   - Configure motor numbering
   - Set ESC protocol (DShot600 recommended)
   - Calibrate accelerometer and compass

3. **Flight Modes**
   - Manual: Direct control
   - Loiter: GPS position hold
   - RTL: Return to launch
   - Guided: Computer control

### 3.2 Raspberry Pi Setup
1. **Install Ubuntu Server 22.04**
   - Download Ubuntu Server image
   - Flash to microSD card
   - Enable SSH and WiFi during setup

2. **Install Dependencies**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3-pip python3-opencv
   sudo apt install -y git cmake build-essential
   sudo apt install -y libatlas-base-dev libjasper-dev
   ```

3. **Install MAVSDK**
   ```bash
   pip3 install mavsdk
   pip3 install mavsdk-python
   ```

4. **Install YOLOv8**
   ```bash
   pip3 install ultralytics
   pip3 install torch torchvision
   ```

### 3.3 Camera Configuration
1. **Enable Camera Interface**
   ```bash
   sudo raspi-config
   # Enable Camera Interface
   # Enable I2C Interface
   ```

2. **Test Camera**
   ```bash
   raspistill -o test.jpg
   ```

3. **Install PiCamera2**
   ```bash
   pip3 install picamera2
   ```

## 🧠 Phase 4: Computer Vision Setup

### 4.1 YOLOv8 Person Detection
1. **Download Pre-trained Model**
   ```python
   from ultralytics import YOLO
   model = YOLO('yolov8n.pt')  # nano model for speed
   ```

2. **Test Person Detection**
   ```python
   results = model('test_image.jpg')
   for result in results:
       boxes = result.boxes
       for box in boxes:
           if box.cls == 0:  # person class
               print("Person detected!")
   ```

### 4.2 Real-time Detection
1. **Camera Stream Processing**
   - Capture frames from Pi camera
   - Process with YOLOv8
   - Extract person coordinates
   - Calculate tracking commands

2. **Performance Optimization**
   - Use YOLOv8n (nano) for speed
   - Process every 3rd frame
   - Resize images to 320x320
   - Use GPU acceleration if available

## 🚁 Phase 5: Autonomous Flight Logic

### 5.1 Person Tracking Algorithm
1. **Coordinate System**
   - Convert image coordinates to drone commands
   - Calculate relative position and distance
   - Generate velocity commands

2. **Safety Limits**
   - Maximum following distance: 10m
   - Minimum safe distance: 2m
   - Maximum altitude: 30m
   - Speed limits: 3m/s forward, 2m/s lateral

### 5.2 Flight Control Integration
1. **MAVSDK Communication**
   - Connect to FC via telemetry or USB
   - Send velocity commands
   - Monitor flight status
   - Handle emergency situations

2. **Autonomous Modes**
   - Person following mode
   - Return to home
   - Emergency landing
   - Manual override

## 🧪 Phase 6: Testing and Calibration

### 6.1 Ground Testing
1. **Motor Test**
   - Test each motor individually
   - Verify rotation direction
   - Check ESC calibration

2. **Sensor Calibration**
   - Calibrate accelerometer
   - Calibrate compass
   - Test GPS lock

3. **Communication Test**
   - Test radio control
   - Verify telemetry link
   - Test Pi-FC communication

### 6.2 Flight Testing
1. **Manual Flight Test**
   - Test basic flight characteristics
   - Verify control response
   - Test failsafe systems

2. **Autonomous Test**
   - Test GPS hold mode
   - Test return to home
   - Test person detection (on ground)

3. **Following Test**
   - Start with low altitude
   - Test person detection in flight
   - Gradually increase complexity

## 🔧 Phase 7: Fine-tuning

### 7.1 PID Tuning
- Tune roll and pitch PIDs for stability
- Adjust yaw PIDs for smooth rotation
- Fine-tune altitude hold parameters

### 7.2 Tracking Parameters
- Adjust following distance
- Tune tracking speed
- Optimize detection sensitivity

### 7.3 Safety Parameters
- Set maximum distances
- Configure emergency procedures
- Test failsafe systems

## 📸 Phase 8: Photography Features

### 8.1 Automatic Photo Capture
- Capture photos when person detected
- Save with timestamp and location
- Implement burst mode for action shots

### 8.2 Photo Quality
- Adjust camera settings for best quality
- Implement HDR for varying lighting
- Add GPS coordinates to photos

## 🚨 Safety Protocols

### 8.3 Pre-flight Checklist
- [ ] Battery fully charged
- [ ] Props securely attached
- [ ] GPS lock acquired
- [ ] All systems tested
- [ ] Emergency procedures reviewed

### 8.4 Emergency Procedures
- Kill switch activation
- Return to home
- Emergency landing
- Signal loss procedures

## 🎯 Next Steps

After completing this build:
1. Practice manual flight extensively
2. Test autonomous modes in safe areas
3. Gradually increase complexity
4. Document any issues and solutions
5. Share your experience with the community

---

**Remember: Safety first! Always test in open areas away from people and property.**
