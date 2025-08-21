# Autonomous Person-Following Drone

A complete guide to building a drone that can autonomously follow people around for photography using computer vision and machine learning.

## 🚁 Project Overview

This drone uses your existing ZMR250 frame with 2207 motors, 30A ESCs, and F7 flight controller, enhanced with a Raspberry Pi 4B for computer vision capabilities. The system can detect people using YOLOv8 and autonomously track them while maintaining safe distances.

## 📋 Components List

### What You Already Have ✅
- ZMR250 carbon fiber frame
- 2207 brushless motors (4x)
- 30A ESCs (4x)
- F7 flight controller
- FlySky receiver
- 5" propellers

### What You Need to Add 🔧
- **Power System:**
  - 4S 1500-2200mAh LiPo battery (70C+ discharge)
  - 5V 5A UBEC for Raspberry Pi power
  - LiPo charger with balance charging
  
- **Companion Computer:**
  - Raspberry Pi 4B (4GB or 8GB)
  - MicroSD card (32GB+)
  - Heatsink and fan for cooling
  
- **Vision System:**
  - Raspberry Pi Camera V3 (wide-angle) or USB webcam
  - Camera mount for frame
  
- **Navigation:**
  - GPS module with compass (BN-880 or Matek M8Q-5883)
  - Optional: TFmini-S lidar for precise altitude
  
- **Communication:**
  - SiK telemetry radios (433MHz/915MHz) or USB-UART cable
  - Optional: FPV system for manual control
  
- **Build Accessories:**
  - XT60 connectors
  - Battery straps
  - M3 standoffs and screws
  - Prop guards (recommended for testing)
  - Smoke stopper for safe testing

## 🏗️ Build Instructions

### 1. Frame Assembly
1. Mount motors to frame arms
2. Install ESCs on frame arms or central plate
3. Mount flight controller with vibration dampening
4. Install GPS module on top plate
5. Mount Raspberry Pi with cooling system

### 2. Electrical Wiring
1. Connect ESCs to flight controller
2. Wire UBEC for 5V power to Pi
3. Connect GPS to FC UART
4. Install telemetry radios
5. Connect camera to Pi

### 3. Software Setup
1. Flash flight controller with ArduPilot
2. Configure Pi with Ubuntu Server
3. Install MAVSDK and OpenCV
4. Set up YOLOv8 person detection
5. Configure autonomous flight modes

## 🚀 Usage

### Manual Flight
- Use your FlySky transmitter for manual control
- Test basic flight characteristics before autonomous modes

### Autonomous Following
- Run the person detection script
- Drone will automatically detect and follow people
- Maintains safe distance and altitude
- Can take photos automatically

### Safety Features
- Kill switch on transmitter
- Return-to-home on signal loss
- Maximum distance and altitude limits
- Emergency landing procedures

## 📁 Project Structure

```
drone-following-system/
├── flight_controller/     # ArduPilot configuration
├── raspberry_pi/         # Pi setup and scripts
├── computer_vision/      # YOLOv8 and tracking code
├── flight_control/       # Autonomous flight logic
├── hardware/             # Wiring diagrams and specs
├── docs/                 # Detailed build guides
└── safety/               # Safety protocols and testing
```

## ⚠️ Safety Warnings

- **NEVER test indoors** without prop guards
- Always test in open areas away from people
- Use smoke stopper for first power-up
- Keep kill switch easily accessible
- Follow local drone regulations
- Test autonomous modes at low altitude first

## 🔧 Troubleshooting

Common issues and solutions are documented in the troubleshooting guide. Always check wiring connections and software configurations before flight.

## 📚 Additional Resources

- ArduPilot documentation
- MAVSDK Python examples
- YOLOv8 training guides
- Local drone regulations

---

**⚠️ Disclaimer: This is an advanced project requiring significant technical knowledge. Always prioritize safety and follow local regulations.**
