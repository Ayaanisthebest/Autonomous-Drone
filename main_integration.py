#!/usr/bin/env python3
"""
Main Integration Script for Person-Following Drone
Combines computer vision with autonomous flight control
"""

import asyncio
import logging
import time
import signal
import sys
from typing import Dict, Optional
import threading
import queue

# Import our modules
from computer_vision.person_detector import PersonDetector
from flight_control.autonomous_controller import AutonomousController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('drone_following.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PersonFollowingDrone:
    """Main class that integrates person detection with autonomous flight"""
    
    def __init__(self, connection_string: str = "udp://:14540"):
        """
        Initialize the person-following drone system
        
        Args:
            connection_string: MAVLink connection string for flight controller
        """
        self.connection_string = connection_string
        
        # Initialize components
        self.person_detector = PersonDetector()
        self.flight_controller = AutonomousController(connection_string)
        
        # System state
        self.is_running = False
        self.is_following = False
        self.emergency_stop = False
        
        # Communication queues
        self.detection_queue = queue.Queue(maxsize=10)
        self.command_queue = queue.Queue(maxsize=10)
        
        # Threads
        self.detection_thread = None
        self.flight_thread = None
        
        # Configuration
        self.following_distance = 5.0  # meters
        self.max_following_speed = 2.0  # m/s
        self.detection_fps = 10
        self.flight_update_rate = 20  # Hz
        
        # Safety parameters
        self.max_flight_time = 600  # 10 minutes
        self.low_battery_threshold = 20  # percent
        self.max_altitude = 30.0  # meters
        self.min_altitude = 2.0  # meters
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.emergency_stop = True
        self.stop_system()
    
    async def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("Initializing person-following drone system...")
            
            # Initialize person detector
            logger.info("Initializing person detector...")
            # Person detector is already initialized in constructor
            
            # Initialize flight controller
            logger.info("Initializing flight controller...")
            if not await self.flight_controller.connect():
                logger.error("Failed to connect to flight controller")
                return False
            
            # Wait for GPS lock
            if not await self.flight_controller.wait_for_gps():
                logger.error("Failed to acquire GPS lock")
                return False
            
            logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            return False
    
    def start_detection_thread(self):
        """Start the person detection thread"""
        def detection_loop():
            logger.info("Person detection thread started")
            
            while self.is_running and not self.emergency_stop:
                try:
                    # Process frame and detect persons
                    frame, target_person, tracking_commands = self.person_detector.process_frame()
                    
                    if target_person is not None:
                        # Add timestamp and additional info
                        detection_data = {
                            'timestamp': time.time(),
                            'target_person': target_person,
                            'tracking_commands': tracking_commands,
                            'frame': frame
                        }
                        
                        # Put in queue (non-blocking)
                        try:
                            self.detection_queue.put_nowait(detection_data)
                        except queue.Full:
                            # Remove old detection if queue is full
                            try:
                                self.detection_queue.get_nowait()
                                self.detection_queue.put_nowait(detection_data)
                            except queue.Empty:
                                pass
                    
                    # Control detection rate
                    time.sleep(1.0 / self.detection_fps)
                    
                except Exception as e:
                    logger.error(f"Error in detection loop: {e}")
                    time.sleep(0.1)
            
            logger.info("Person detection thread stopped")
        
        self.detection_thread = threading.Thread(target=detection_loop, daemon=True)
        self.detection_thread.start()
    
    def start_flight_thread(self):
        """Start the autonomous flight control thread"""
        def flight_loop():
            logger.info("Flight control thread started")
            
            while self.is_running and not self.emergency_stop:
                try:
                    # Get latest detection data
                    detection_data = None
                    try:
                        detection_data = self.detection_queue.get_nowait()
                    except queue.Empty:
                        pass
                    
                    if detection_data and self.is_following:
                        # Execute person following
                        tracking_commands = detection_data['tracking_commands']
                        await self.flight_controller.follow_person(tracking_commands)
                        
                        logger.info(f"Following person: {tracking_commands}")
                    else:
                        # Hover in place
                        await self.flight_controller.send_velocity_command({
                            'forward': 0, 'right': 0, 'up': 0, 'yaw': 0
                        })
                    
                    # Control flight update rate
                    time.sleep(1.0 / self.flight_update_rate)
                    
                except Exception as e:
                    logger.error(f"Error in flight loop: {e}")
                    time.sleep(0.1)
            
            logger.info("Flight control thread stopped")
        
        # Note: This won't work directly due to async/await in threading
        # We'll need to use asyncio.run_coroutine_threadsafe or restructure
        logger.warning("Flight thread needs to be restructured for async operations")
    
    async def start_following_mode(self) -> bool:
        """Start person following mode"""
        try:
            logger.info("Starting person following mode...")
            
            # Check if system is ready
            if not self.flight_controller.is_connected:
                logger.error("Flight controller not connected")
                return False
            
            # Arm and take off
            if not await self.flight_controller.arm_and_takeoff():
                logger.error("Failed to arm and take off")
                return False
            
            # Enable offboard mode
            if not await self.flight_controller.enable_offboard_mode():
                logger.error("Failed to enable offboard mode")
                return False
            
            self.is_following = True
            logger.info("Person following mode started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start following mode: {e}")
            return False
    
    async def stop_following_mode(self) -> bool:
        """Stop person following mode and return to launch"""
        try:
            logger.info("Stopping person following mode...")
            
            self.is_following = False
            
            # Return to launch
            if await self.flight_controller.return_to_launch():
                logger.info("Successfully returned to launch")
                return True
            else:
                logger.error("Failed to return to launch")
                return False
                
        except Exception as e:
            logger.error(f"Failed to stop following mode: {e}")
            return False
    
    async def run_main_loop(self, duration: int = 300):
        """
        Run the main system loop
        
        Args:
            duration: Duration to run in seconds
        """
        logger.info(f"Starting main system loop for {duration} seconds")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration and not self.emergency_stop:
                # Check system health
                if not await self._check_system_health():
                    logger.warning("System health check failed, stopping following")
                    await self.stop_following_mode()
                    break
                
                # Get flight status
                status = await self.flight_controller.get_flight_status()
                logger.info(f"Flight status: {status}")
                
                # Check for emergency conditions
                if await self._check_emergency_conditions():
                    logger.error("Emergency conditions detected, executing emergency landing")
                    await self.flight_controller.emergency_landing()
                    break
                
                await asyncio.sleep(1.0)
                
        except KeyboardInterrupt:
            logger.info("Main loop interrupted by user")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            # Clean up
            await self.cleanup()
            logger.info("Main system loop finished")
    
    async def _check_system_health(self) -> bool:
        """Check overall system health"""
        try:
            # Check flight controller connection
            if not self.flight_controller.is_connected:
                logger.error("Flight controller disconnected")
                return False
            
            # Check battery level
            status = await self.flight_controller.get_flight_status()
            if 'battery' in status:
                battery_level = status['battery']['remaining']
                if battery_level < self.low_battery_threshold:
                    logger.warning(f"Low battery: {battery_level}%")
                    return False
            
            # Check altitude
            if 'position' in status:
                altitude = status['position']['alt']
                if altitude < self.min_altitude or altitude > self.max_altitude:
                    logger.warning(f"Altitude out of safe range: {altitude}m")
                    return False
            
            # Check flight time
            if self.flight_controller.flight_start_time:
                flight_time = time.time() - self.flight_controller.flight_start_time
                if flight_time > self.max_flight_time:
                    logger.warning(f"Maximum flight time exceeded: {flight_time}s")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return False
    
    async def _check_emergency_conditions(self) -> bool:
        """Check for emergency conditions requiring immediate action"""
        try:
            # Check for critical battery level
            status = await self.flight_controller.get_flight_status()
            if 'battery' in status:
                battery_level = status['battery']['remaining']
                if battery_level < 10:  # Critical battery level
                    logger.error(f"Critical battery level: {battery_level}%")
                    return True
            
            # Check for excessive altitude
            if 'position' in status:
                altitude = status['position']['alt']
                if altitude > 50:  # Emergency altitude limit
                    logger.error(f"Emergency altitude limit exceeded: {altitude}m")
                    return True
            
            # Check for loss of GPS
            if not await self.flight_controller.wait_for_gps(timeout=5):
                logger.error("GPS signal lost")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Emergency condition check failed: {e}")
            return True  # Assume emergency if check fails
    
    def start_system(self):
        """Start the complete system"""
        try:
            logger.info("Starting person-following drone system...")
            
            self.is_running = True
            
            # Start detection thread
            self.start_detection_thread()
            
            # Start flight thread (note: needs restructuring)
            # self.start_flight_thread()
            
            logger.info("System started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop_system()
    
    def stop_system(self):
        """Stop the complete system"""
        try:
            logger.info("Stopping person-following drone system...")
            
            self.is_running = False
            self.is_following = False
            
            # Wait for threads to finish
            if self.detection_thread and self.detection_thread.is_alive():
                self.detection_thread.join(timeout=5.0)
            
            logger.info("System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    async def cleanup(self):
        """Clean up system resources"""
        try:
            logger.info("Cleaning up system resources...")
            
            # Stop following mode
            if self.is_following:
                await self.stop_following_mode()
            
            # Clean up flight controller
            await self.flight_controller.cleanup()
            
            # Clean up person detector
            self.person_detector.cleanup()
            
            logger.info("System cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def main():
    """Main function"""
    drone_system = PersonFollowingDrone()
    
    try:
        # Initialize system
        if not await drone_system.initialize_system():
            logger.error("System initialization failed")
            return
        
        # Start system
        drone_system.start_system()
        
        # Start following mode
        if not await drone_system.start_following_mode():
            logger.error("Failed to start following mode")
            return
        
        # Run main loop
        await drone_system.run_main_loop(300)  # 5 minutes
        
    except Exception as e:
        logger.error(f"Main function error: {e}")
    finally:
        # Clean up
        drone_system.stop_system()
        await drone_system.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program error: {e}")
