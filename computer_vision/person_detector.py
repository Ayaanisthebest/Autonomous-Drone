#!/usr/bin/env python3
"""
Person Detection and Tracking System for Autonomous Drone
Uses YOLOv8 for real-time person detection and generates tracking commands
"""

import cv2
import numpy as np
import time
from ultralytics import YOLO
from picamera2 import Picamera2
import logging
from typing import Tuple, Optional, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonDetector:
    """Real-time person detection and tracking using YOLOv8"""
    
    def __init__(self, model_path: str = 'yolov8n.pt', confidence: float = 0.5):
        """
        Initialize the person detector
        
        Args:
            model_path: Path to YOLOv8 model file
            confidence: Minimum confidence threshold for detection
        """
        self.confidence = confidence
        self.model = None
        self.camera = None
        self.frame_width = 640
        self.frame_height = 480
        
        # Tracking parameters
        self.target_person = None
        self.tracking_history = []
        self.max_history = 10
        
        # Safety parameters
        self.min_person_size = 50  # minimum pixel size to track
        self.max_person_size = 400  # maximum pixel size (too close)
        
        # Initialize model and camera
        self._load_model(model_path)
        self._setup_camera()
        
    def _load_model(self, model_path: str):
        """Load YOLOv8 model"""
        try:
            logger.info(f"Loading YOLOv8 model from {model_path}")
            self.model = YOLO(model_path)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _setup_camera(self):
        """Initialize Raspberry Pi camera"""
        try:
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (self.frame_width, self.frame_height)},
                buffer_count=4
            )
            self.camera.configure(config)
            self.camera.start()
            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            # Fallback to USB webcam
            self._setup_usb_camera()
    
    def _setup_usb_camera(self):
        """Fallback to USB webcam if Pi camera fails"""
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            logger.info("USB camera initialized as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize USB camera: {e}")
            raise
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a frame from the camera"""
        try:
            if hasattr(self.camera, 'capture_array'):
                # Pi camera
                frame = self.camera.capture_array()
                # Convert from BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # USB camera
                ret, frame = self.camera.read()
                if not ret:
                    return None
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            return frame
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None
    
    def detect_persons(self, frame: np.ndarray) -> List[dict]:
        """
        Detect persons in the frame using YOLOv8
        
        Args:
            frame: Input image frame
            
        Returns:
            List of detected persons with bounding boxes and confidence
        """
        try:
            results = self.model(frame, verbose=False)
            persons = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Check if detected object is a person (class 0)
                        if box.cls == 0 and box.conf > self.confidence:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            
                            person = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': confidence,
                                'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                                'size': [int(x2 - x1), int(y2 - y1)]
                            }
                            persons.append(person)
            
            return persons
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def select_target_person(self, persons: List[dict]) -> Optional[dict]:
        """
        Select the best person to track based on various criteria
        
        Args:
            persons: List of detected persons
            
        Returns:
            Selected target person or None
        """
        if not persons:
            return None
        
        # Score each person based on multiple criteria
        scored_persons = []
        for person in persons:
            score = 0
            
            # Prefer persons closer to center of frame
            center_x, center_y = person['center']
            frame_center_x = self.frame_width // 2
            frame_center_y = self.frame_height // 2
            
            distance_from_center = np.sqrt((center_x - frame_center_x)**2 + (center_y - frame_center_y)**2)
            center_score = max(0, 100 - distance_from_center / 10)
            score += center_score
            
            # Prefer persons with higher confidence
            score += person['confidence'] * 100
            
            # Prefer persons with reasonable size (not too close or far)
            width, height = person['size']
            person_size = max(width, height)
            if self.min_person_size <= person_size <= self.max_person_size:
                size_score = 50
            else:
                size_score = max(0, 50 - abs(person_size - 200) / 10)
            score += size_score
            
            scored_persons.append((person, score))
        
        # Select person with highest score
        if scored_persons:
            best_person = max(scored_persons, key=lambda x: x[1])
            return best_person[0]
        
        return None
    
    def calculate_tracking_commands(self, target_person: dict) -> dict:
        """
        Calculate drone movement commands based on target person position
        
        Args:
            target_person: Target person to track
            
        Returns:
            Dictionary with movement commands
        """
        if not target_person:
            return {'forward': 0, 'right': 0, 'up': 0, 'yaw': 0}
        
        center_x, center_y = target_person['center']
        frame_center_x = self.frame_width // 2
        frame_center_y = self.frame_height // 2
        
        # Calculate normalized offsets (-1 to 1)
        x_offset = (center_x - frame_center_x) / (self.frame_width / 2)
        y_offset = (center_y - frame_center_y) / (self.frame_height / 2)
        
        # Calculate size-based distance estimate
        width, height = target_person['size']
        person_size = max(width, height)
        
        # Estimate distance based on person size (inverse relationship)
        # This is a rough approximation - would need calibration
        target_size = 200  # target size in pixels
        distance_ratio = target_size / person_size
        
        # Generate movement commands
        commands = {
            'forward': np.clip(distance_ratio - 1, -0.5, 0.5),  # Forward/backward
            'right': np.clip(-x_offset, -1, 1),  # Left/right movement
            'up': np.clip(-y_offset, -1, 1),    # Up/down movement
            'yaw': np.clip(x_offset * 0.5, -0.5, 0.5)  # Yaw rotation
        }
        
        # Apply deadzone to prevent jitter
        deadzone = 0.1
        for key in commands:
            if abs(commands[key]) < deadzone:
                commands[key] = 0
        
        return commands
    
    def update_tracking_history(self, target_person: Optional[dict]):
        """Update tracking history for smooth movement"""
        if target_person:
            self.tracking_history.append({
                'timestamp': time.time(),
                'center': target_person['center'],
                'size': target_person['size']
            })
        else:
            self.tracking_history.append({
                'timestamp': time.time(),
                'center': None,
                'size': None
            })
        
        # Keep only recent history
        if len(self.tracking_history) > self.max_history:
            self.tracking_history.pop(0)
    
    def get_smoothed_commands(self, commands: dict) -> dict:
        """Apply smoothing to movement commands using tracking history"""
        if len(self.tracking_history) < 3:
            return commands
        
        # Simple moving average smoothing
        smoothing_factor = 0.7
        smoothed_commands = {}
        
        for key in commands:
            current = commands[key]
            if current != 0:  # Only smooth non-zero commands
                smoothed_commands[key] = current * smoothing_factor
            else:
                smoothed_commands[key] = 0
        
        return smoothed_commands
    
    def process_frame(self) -> Tuple[Optional[np.ndarray], Optional[dict], Optional[dict]]:
        """
        Process a single frame and return detection results
        
        Returns:
            Tuple of (annotated_frame, target_person, tracking_commands)
        """
        # Capture frame
        frame = self.capture_frame()
        if frame is None:
            return None, None, None
        
        # Detect persons
        persons = self.detect_persons(frame)
        
        # Select target person
        target_person = self.select_target_person(persons)
        
        # Update tracking history
        self.update_tracking_history(target_person)
        
        # Calculate tracking commands
        if target_person:
            raw_commands = self.calculate_tracking_commands(target_person)
            tracking_commands = self.get_smoothed_commands(raw_commands)
        else:
            tracking_commands = {'forward': 0, 'right': 0, 'up': 0, 'yaw': 0}
        
        # Annotate frame for visualization
        annotated_frame = self._annotate_frame(frame, persons, target_person, tracking_commands)
        
        return annotated_frame, target_person, tracking_commands
    
    def _annotate_frame(self, frame: np.ndarray, persons: List[dict], 
                       target_person: Optional[dict], commands: dict) -> np.ndarray:
        """Add visual annotations to the frame"""
        annotated = frame.copy()
        
        # Draw all detected persons
        for person in persons:
            x1, y1, x2, y2 = person['bbox']
            color = (0, 255, 0) if person == target_person else (255, 0, 0)
            thickness = 3 if person == target_person else 1
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(annotated, f"Person: {person['confidence']:.2f}", 
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw center crosshair
        center_x = self.frame_width // 2
        center_y = self.frame_height // 2
        cv2.line(annotated, (center_x-20, center_y), (center_x+20, center_y), (255, 255, 255), 2)
        cv2.line(annotated, (center_x, center_y-20), (center_x, center_y+20), (255, 255, 255), 2)
        
        # Draw tracking commands
        y_offset = 30
        for key, value in commands.items():
            text = f"{key}: {value:.2f}"
            cv2.putText(annotated, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
        
        return annotated
    
    def run_detection_loop(self, duration: int = 60):
        """
        Run continuous detection loop for testing
        
        Args:
            duration: Duration to run in seconds
        """
        logger.info(f"Starting detection loop for {duration} seconds")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                frame, target, commands = self.process_frame()
                
                if frame is not None:
                    # Display frame
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imshow('Person Detection', frame_bgr)
                    
                    # Print commands
                    if target:
                        logger.info(f"Target detected: {target['center']}, Commands: {commands}")
                    else:
                        logger.info("No target detected")
                
                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.1)  # 10 FPS
                
        except KeyboardInterrupt:
            logger.info("Detection loop interrupted by user")
        finally:
            cv2.destroyAllWindows()
            logger.info("Detection loop finished")
    
    def cleanup(self):
        """Clean up resources"""
        if self.camera:
            if hasattr(self.camera, 'stop'):
                self.camera.stop()
            else:
                self.camera.release()
        cv2.destroyAllWindows()

def main():
    """Main function for testing"""
    detector = PersonDetector()
    
    try:
        # Run detection loop for 60 seconds
        detector.run_detection_loop(60)
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    main()
