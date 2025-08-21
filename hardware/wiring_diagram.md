# Drone Wiring Diagram

## 🔌 Complete Electrical Schematic

### Power Distribution
```
4S LiPo Battery (14.8V)
    ↓
XT60 Connector
    ↓
Power Distribution Board (PDB)
    ├── ESC 1 (Motor 1) - 14.8V
    ├── ESC 2 (Motor 2) - 14.8V
    ├── ESC 3 (Motor 3) - 14.8V
    ├── ESC 4 (Motor 4) - 14.8V
    ├── Flight Controller - 14.8V
    └── 5V UBEC - 14.8V Input
            ↓
        5V Output
            ↓
    Raspberry Pi 4B
```

### Flight Controller Connections
```
F7 Flight Controller
    ├── Power
    │   ├── Main Power: PDB → FC (14.8V)
    │   └── Logic Power: 5V BEC → FC (5V)
    │
    ├── Motors (ESC Signal Wires)
    │   ├── Motor 1: ESC1 Signal → FC Motor 1
    │   ├── Motor 2: ESC2 Signal → FC Motor 2
    │   ├── Motor 3: ESC3 Signal → FC Motor 3
    │   └── Motor 4: ESC4 Signal → FC Motor 4
    │
    ├── GPS Module
    │   ├── GPS VCC → FC 5V
    │   ├── GPS GND → FC GND
    │   ├── GPS TX → FC UART1 RX
    │   └── GPS RX → FC UART1 TX
    │
    ├── Telemetry Radio
    │   ├── Radio VCC → FC 5V
    │   ├── Radio GND → FC GND
    │   ├── Radio TX → FC UART2 RX
    │   └── Radio RX → FC UART2 TX
    │
    └── FlySky Receiver
        ├── Receiver VCC → FC 5V
        ├── Receiver GND → FC GND
        └── Receiver Signal → FC iBus Port
```

### Raspberry Pi Connections
```
Raspberry Pi 4B
    ├── Power
    │   ├── 5V → 5V UBEC Output
    │   └── GND → 5V UBEC GND
    │
    ├── Camera
    │   ├── CSI Cable → Pi Camera Port
    │   └── Camera Power → Pi 5V
    │
    ├── Flight Controller Communication
    │   ├── USB Cable → FC USB Port
    │   └── Alternative: UART Connection
    │       ├── Pi TX → FC UART3 RX
    │       ├── Pi RX → FC UART3 TX
    │       └── Pi GND → FC GND
    │
    └── Optional: WiFi/Bluetooth
        ├── WiFi Dongle → Pi USB
        └── Bluetooth → Pi Built-in
```

## 📍 Pin Assignments

### Flight Controller Pinout (Typical F7)
```
Power Pins:
- VCC: 14.8V from PDB
- 5V: 5V from BEC
- GND: Common ground

Motor Outputs:
- Motor 1: Output 1
- Motor 2: Output 2
- Motor 3: Output 3
- Motor 4: Output 4

UART Ports:
- UART1: GPS Module
- UART2: Telemetry Radio
- UART3: Raspberry Pi (if using UART)
- USB: Raspberry Pi (recommended)

Receiver:
- iBus: FlySky receiver signal
```

### Raspberry Pi Pinout
```
Power:
- Pin 2: 5V (from UBEC)
- Pin 6: GND (from UBEC)

Camera:
- CSI Port: Camera ribbon cable

Communication:
- USB Ports: Flight Controller, WiFi dongle
- GPIO: Optional for additional sensors
```

## 🔧 Component Specifications

### Power System
- **LiPo Battery**: 4S 1500-2200mAh, 70C+ discharge
- **PDB**: 4S input, 4 ESC outputs, 5V BEC output
- **5V UBEC**: 5V output, 3-5A capacity, 4S input
- **5V BEC**: 5V output, 1A capacity, for FC logic

### ESCs
- **Type**: 30A BLHeli_32 or similar
- **Protocol**: DShot600 recommended
- **Power**: 14.8V (4S)
- **Signal**: 5V logic level

### Flight Controller
- **Type**: F7 processor
- **Firmware**: ArduPilot
- **Power**: 14.8V main, 5V logic
- **Communication**: USB, UART, iBus

### GPS Module
- **Type**: BN-880 or Matek M8Q-5883
- **Power**: 5V
- **Protocol**: UART
- **Features**: GPS + Compass

### Telemetry Radio
- **Type**: SiK radio (433MHz or 915MHz)
- **Power**: 5V
- **Protocol**: UART
- **Range**: 1-2km line of sight

### Raspberry Pi
- **Model**: 4B (4GB or 8GB)
- **Power**: 5V, 3A minimum
- **OS**: Ubuntu Server 22.04
- **Camera**: Pi Camera V3 or USB webcam

## ⚠️ Wiring Safety Notes

### Power Distribution
1. **Always use smoke stopper** for first power-up
2. **Check polarity** before connecting
3. **Secure all connections** with heat shrink or tape
4. **Route wires** to avoid prop interference

### Signal Wires
1. **Keep signal wires** away from power wires
2. **Use twisted pairs** for differential signals
3. **Minimize wire length** to reduce interference
4. **Secure loose wires** to prevent vibration damage

### Ground Connections
1. **Single ground point** for all components
2. **Avoid ground loops** in signal circuits
3. **Use star grounding** for power distribution
4. **Check continuity** of all ground connections

## 🧪 Testing Procedure

### Pre-Power Test
1. **Continuity test** all connections
2. **Check polarity** of all components
3. **Verify wire routing** won't interfere with props
4. **Secure all connections** with proper strain relief

### First Power-Up
1. **Use smoke stopper** in series with battery
2. **Check voltage** at all power points
3. **Test each system** individually
4. **Monitor temperature** of all components

### System Integration Test
1. **Test motor response** to FC commands
2. **Verify GPS lock** and compass calibration
3. **Test telemetry** communication
4. **Verify Pi-FC** communication

## 🔍 Troubleshooting Common Issues

### Power Issues
- **No power**: Check battery voltage and connections
- **Voltage drop**: Verify wire gauge and connections
- **ESC issues**: Check power and signal connections

### Communication Issues
- **GPS no lock**: Check antenna orientation and connections
- **Telemetry failure**: Verify UART settings and connections
- **Pi-FC disconnect**: Check USB cable and FC settings

### Motor Issues
- **Motor not spinning**: Check ESC power and signal
- **Wrong direction**: Swap motor wires or change FC settings
- **Vibration**: Check prop balance and motor mounting
