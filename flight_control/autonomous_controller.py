#!/usr/bin/env python3
"""
Autonomous Flight Controller for Person-Following Drone
Integrates with ArduPilot flight controller using MAVSDK
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed
from mavsdk.mission import MissionError
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomousController:
    """Autonomous flight controller using MAVSDK"""
    
    def __init__(self, connection_string: str = "udp://:14540"):
        """
        Initialize the autonomous controller
        
        Args:
            connection_string: MAVLink connection string
        """
        self.drone = System()
        self.connection_string = connection_string
        self.is_connected = False
        self.is_armed = False
        self.is_flying = False
        
        # Flight parameters
        self.max_velocity = 3.0  # m/s
        self.max_yaw_rate = 45.0  # degrees/s
        self.safe_altitude = 5.0  # meters
        self.max_following_distance = 10.0  # meters
        self.min_safe_distance = 2.0  # meters
        
        # Tracking state
        self.current_target = None
        self.last_target_time = 0
        self.target_lost_timeout = 5.0  # seconds
        
        # Safety parameters
        self.emergency_landing = False
        self.max_flight_time = 600  # 10 minutes
        self.flight_start_time = None
        
        # Movement smoothing
        self.velocity_history = []
        self.max_history = 5
        
    async def connect(self) -> bool:
        """Connect to the flight controller"""
        try:
            logger.info(f"Connecting to drone via {self.connection_string}")
            
            # Connect to the drone
            await self.drone.connect(self.connection_string)
            
            # Wait for connection
            async for state in self.drone.core.connection_state():
                if state.is_connected:
                    logger.info("Connected to drone!")
                    self.is_connected = True
                    break
            
            # Get drone info
            async for info in self.drone.info.system():
                logger.info(f"Drone ID: {info.system_id}")
                break
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def wait_for_gps(self, timeout: int = 60) -> bool:
        """Wait for GPS lock"""
        try:
            logger.info("Waiting for GPS lock...")
            start_time = time.time()
            
            async for gps_info in self.drone.gps.info():
                if gps_info.num_satellites >= 6:
                    logger.info(f"GPS lock acquired with {gps_info.num_satellites} satellites")
                    return True
                
                if time.time() - start_time > timeout:
                    logger.error("GPS lock timeout")
                    return False
                    
        except Exception as e:
            logger.error(f"GPS wait failed: {e}")
            return False
    
    async def arm_and_takeoff(self, target_altitude: float = 5.0) -> bool:
        """Arm the drone and take off to target altitude"""
        try:
            if not self.is_connected:
                logger.error("Not connected to drone")
                return False
            
            # Wait for GPS lock
            if not await self.wait_for_gps():
                return False
            
            # Check if drone is ready to arm
            async for health in self.drone.core.health():
                if health.is_gyrometer_calibration_ok and health.is_accelerometer_calibration_ok:
                    break
            
            # Arm the drone
            logger.info("Arming drone...")
            await self.drone.action.arm()
            self.is_armed = True
            logger.info("Drone armed successfully")
            
            # Take off
            logger.info(f"Taking off to {target_altitude}m...")
            await self.drone.action.takeoff()
            
            # Wait for takeoff to complete
            async for altitude in self.drone.telemetry.position():
                if altitude.relative_altitude_m >= target_altitude * 0.9:
                    logger.info("Takeoff completed")
                    self.is_flying = True
                    self.flight_start_time = time.time()
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"Takeoff failed: {e}")
            return False
    
    async def enable_offboard_mode(self) -> bool:
        """Enable offboard mode for velocity control"""
        try:
            logger.info("Enabling offboard mode...")
            
            # Set initial velocity to zero
            await self.drone.offboard.set_velocity_body(
                VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)
            )
            
            # Start offboard mode
            await self.drone.offboard.start()
            logger.info("Offboard mode enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable offboard mode: {e}")
            return False
    
    async def send_velocity_command(self, velocity: Dict[str, float]) -> bool:
        """
        Send velocity command to the drone
        
        Args:
            velocity: Dictionary with 'forward', 'right', 'up', 'yaw' velocities
        """
        try:
            if not self.is_flying:
                logger.warning("Drone not flying, cannot send velocity command")
                return False
            
            # Extract velocity components
            forward = velocity.get('forward', 0.0)
            right = velocity.get('right', 0.0)
            up = velocity.get('up', 0.0)
            yaw = velocity.get('yaw', 0.0)
            
            # Apply safety limits
            forward = np.clip(forward, -self.max_velocity, self.max_velocity)
            right = np.clip(right, -self.max_velocity, self.max_velocity)
            up = np.clip(up, -self.max_velocity, self.max_velocity)
            yaw = np.clip(yaw, -self.max_yaw_rate, self.max_yaw_rate)
            
            # Convert yaw from degrees/s to rad/s
            yaw_rad = np.radians(yaw)
            
            # Send velocity command
            await self.drone.offboard.set_velocity_body(
                VelocityBodyYawspeed(forward, right, up, yaw_rad)
            )
            
            # Store in history for smoothing
            self.velocity_history.append({
                'timestamp': time.time(),
                'forward': forward,
                'right': right,
                'up': up,
                'yaw': yaw
            })
            
            # Keep only recent history
            if len(self.velocity_history) > self.max_history:
                self.velocity_history.pop(0)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send velocity command: {e}")
            return False
    
    async def follow_person(self, tracking_commands: Dict[str, float]) -> bool:
        """
        Execute person following behavior
        
        Args:
            tracking_commands: Commands from person detector
        """
        try:
            if not self.is_flying:
                return False
            
            # Check safety conditions
            if not await self._check_safety_conditions():
                logger.warning("Safety conditions not met, stopping following")
                return False
            
            # Send velocity commands
            success = await self.send_velocity_command(tracking_commands)
            
            if success:
                self.current_target = tracking_commands
                self.last_target_time = time.time()
            
            return success
            
        except Exception as e:
            logger.error(f"Person following failed: {e}")
            return False
    
    async def _check_safety_conditions(self) -> bool:
        """Check if it's safe to continue flying"""
        try:
            # Check flight time
            if self.flight_start_time and time.time() - self.flight_start_time > self.max_flight_time:
                logger.warning("Maximum flight time reached")
                return False
            
            # Check battery level
            async for battery in self.drone.telemetry.battery():
                if battery.remaining_percent < 20:
                    logger.warning("Low battery, safety landing required")
                    return False
                break
            
            # Check altitude
            async for position in self.drone.telemetry.position():
                if position.relative_altitude_m < 1.0:
                    logger.warning("Too low altitude")
                    return False
                if position.relative_altitude_m > 30.0:
                    logger.warning("Too high altitude")
                    return False
                break
            
            return True
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return False
    
    async def return_to_launch(self) -> bool:
        """Return to launch position"""
        try:
            logger.info("Returning to launch...")
            
            # Stop offboard mode
            await self.drone.offboard.stop()
            
            # Execute RTL mission
            await self.drone.action.return_to_launch()
            
            # Wait for landing
            async for flight_mode in self.drone.telemetry.flight_mode():
                if flight_mode == "LAND":
                    logger.info("Landing...")
                    break
            
            # Wait for landing to complete
            async for altitude in self.drone.telemetry.position():
                if altitude.relative_altitude_m < 0.5:
                    logger.info("Landed successfully")
                    self.is_flying = False
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"RTL failed: {e}")
            return False
    
    async def emergency_landing(self) -> bool:
        """Execute emergency landing"""
        try:
            logger.warning("Executing emergency landing!")
            self.emergency_landing = True
            
            # Stop offboard mode
            await self.drone.offboard.stop()
            
            # Land immediately
            await self.drone.action.land()
            
            # Wait for landing
            async for altitude in self.drone.telemetry.position():
                if altitude.relative_altitude_m < 0.5:
                    logger.info("Emergency landing completed")
                    self.is_flying = False
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"Emergency landing failed: {e}")
            return False
    
    async def disarm(self) -> bool:
        """Disarm the drone"""
        try:
            if self.is_armed:
                logger.info("Disarming drone...")
                await self.drone.action.disarm()
                self.is_armed = False
                logger.info("Drone disarmed")
            
            return True
            
        except Exception as e:
            logger.error(f"Disarm failed: {e}")
            return False
    
    async def get_flight_status(self) -> Dict:
        """Get current flight status"""
        try:
            status = {
                'connected': self.is_connected,
                'armed': self.is_armed,
                'flying': self.is_flying,
                'emergency_landing': self.emergency_landing
            }
            
            if self.is_connected:
                # Get position
                async for position in self.drone.telemetry.position():
                    status['position'] = {
                        'lat': position.latitude_deg,
                        'lon': position.longitude_deg,
                        'alt': position.relative_altitude_m
                    }
                    break
                
                # Get battery
                async for battery in self.drone.telemetry.battery():
                    status['battery'] = {
                        'remaining': battery.remaining_percent,
                        'voltage': battery.voltage_v
                    }
                    break
                
                # Get flight mode
                async for flight_mode in self.drone.telemetry.flight_mode():
                    status['flight_mode'] = flight_mode
                    break
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get flight status: {e}")
            return {'error': str(e)}
    
    async def run_autonomous_loop(self, duration: int = 300):
        """
        Run autonomous flight loop
        
        Args:
            duration: Duration to run in seconds
        """
        logger.info(f"Starting autonomous flight loop for {duration} seconds")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Check safety conditions
                if not await self._check_safety_conditions():
                    logger.warning("Safety conditions not met, executing RTL")
                    await self.return_to_launch()
                    break
                
                # Check if target is lost
                if self.current_target and time.time() - self.last_target_time > self.target_lost_timeout:
                    logger.info("Target lost, hovering in place")
                    await self.send_velocity_command({'forward': 0, 'right': 0, 'up': 0, 'yaw': 0})
                    self.current_target = None
                
                # Get flight status
                status = await self.get_flight_status()
                logger.info(f"Flight status: {status}")
                
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            logger.info("Autonomous loop interrupted by user")
        except Exception as e:
            logger.error(f"Autonomous loop error: {e}")
        finally:
            # Clean up
            if self.is_flying:
                await self.return_to_launch()
            await self.disarm()
            logger.info("Autonomous loop finished")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.is_flying:
                await self.return_to_launch()
            if self.is_armed:
                await self.disarm()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def main():
    """Main function for testing"""
    controller = AutonomousController()
    
    try:
        # Connect to drone
        if not await controller.connect():
            logger.error("Failed to connect to drone")
            return
        
        # Arm and take off
        if not await controller.arm_and_takeoff():
            logger.error("Failed to take off")
            return
        
        # Enable offboard mode
        if not await controller.enable_offboard_mode():
            logger.error("Failed to enable offboard mode")
            return
        
        # Run autonomous loop
        await controller.run_autonomous_loop(60)
        
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        await controller.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
