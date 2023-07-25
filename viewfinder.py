# External dependencies
import cv2
import keyboard
import time
from camera import Camera
from os import path
from enum import Enum
# Internal dependencies
from image_processor import ImageProcessor
from config import SlaveConfig, CameraConfig, CutConfig
from slave import Slave
from camera import Camera

class ViewfinderModes(Enum):
    MODE_VIEWFINDER = 0
    MODE_CALIBRATION = 1
    MODE_STATIC = 2   

class Viewfinder():
    currentMode = ViewfinderModes.MODE_VIEWFINDER
    
    # Camera / Axis control
    camera : Camera = None
    slave : Slave = None
    # Config passed from main
    config = {
        "workingFolder" : '.',
    }
    # Text to draw on screen
    displayText = ""
    # Has the viewfinder moved at all?
    moved = False
    # What step of the calibration are we at?
    calibrationData = None
    calibrationStep = 0
    # When can we move again?
    nextMovementTime = 0
    
    #
    def __init__(self, camera, slave, config={}):
        self.camera = camera
        self.slave = slave
        for key, value in config.items():
            self.config[key] = value
    def get_name(self):
        if self.currentMode == ViewfinderModes.MODE_CALIBRATION:
            return "Calibration Viewfinder"
        if self.currentMode == ViewfinderModes.MODE_STATIC:
            return "Preview"
        return "Viewfinder "
    # Show the window and initialize the main loop
    def show(self, frame=None):
        if not self.main_loop(frame):
            raise(BaseException("Something went wrong."))
        cv2.destroyWindow(self.get_name())
    # Handle camera and input loop
    def main_loop(self, frame):
        # First of all get the first frame to set up the windows
        cv2.namedWindow(self.get_name())
        if self.currentMode == ViewfinderModes.MODE_STATIC:
            frame = ImageProcessor.resize_for_preview(frame, CameraConfig.preview_size)
            cv2.imshow(self.get_name(), frame)
            while True:
                # Catch ESC with cv2 input
                key = cv2.waitKey(20)
                if key == 27: # exit on ESC
                    return True
        if not self.camera.isOpened():
            raise (BaseException("Camera is not ready"))

        frame = self.camera.capturePhoto()

        while True:


            # Process the frame
            ImageProcessor.draw_grid(frame, pxstep=CameraConfig.preview_grid_pace)
            ImageProcessor.draw_center(frame)
            frame = ImageProcessor.resize_for_preview(frame, CameraConfig.preview_size)
            if len(self.displayText) > 0:
                ImageProcessor.draw_text(frame, self.displayText)
            # Display the frame
            cv2.imshow(self.get_name(), frame)
            
            # Catch ESC with cv2 input
            key = cv2.waitKey(20)
            if key == 27 and (self.currentMode != ViewfinderModes.MODE_CALIBRATION): # exit on ESC
                return True

            # Handle input
            if  self.handle_input():
                return True

            # Fetch next frame
            frame = self.camera.capturePhoto()
        return False
    # Handle user input
    def handle_input(self):
        # Only move if we are allowed
        if self.nextMovementTime < time.time():
            # Handle movement
            speed = keyboard.is_pressed('shift') and SlaveConfig.user_move_speed["fast"] or SlaveConfig.user_move_speed["base"]
            movement = {}
            # X Axis W/S
            if keyboard.is_pressed('a'):
                movement["X"] = -speed["X"]
            elif keyboard.is_pressed('d'):
                movement["X"] = speed["X"]
            # Y Axis A/D
            if keyboard.is_pressed('s'):
                movement["Y"] = -speed["Y"]
            elif keyboard.is_pressed('w'):
                movement["Y"] = speed["Y"]
            elif keyboard.is_pressed('o'):
                movement["X"] = -CutConfig.camera_offset['X']
                movement["Y"] = -CutConfig.camera_offset['Y']
            elif keyboard.is_pressed('p'):
                movement["X"] = CutConfig.camera_offset['X']
                movement["Y"] = CutConfig.camera_offset['Y']
            # Move only if needed
            if len(movement) > 0:
                self.moved = True
               
                self.nextMovementTime = time.time() + (self.slave.move_rel(movement) * 2)
                self.displayText = f"Position {self.slave.position['X']}/{self.slave.position['Y']}"
            # Handle stuff that's not allowed in Calibration Mode
            if self.currentMode != ViewfinderModes.MODE_CALIBRATION:
                if keyboard.is_pressed('space'):
                    photo = self.camera.capturePhoto()
                    outfile = path.join(
                        self.config["workingFolder"],
                        f"snap{str(int(self.slave.position['X']*100)).zfill(6)}_{str(int(self.slave.position['X']*100)).zfill(6)}.png"
                    )
                    ImageProcessor.save_image(photo, outfile)
            # Handle calibration mode
            else:
                self.displayText = f"Calibration {self.calibrationStep+1}/4 [SPACE] to confirm"
                if keyboard.is_pressed('space') and self.nextMovementTime < time.time():
                    self.calibrationData[self.calibrationStep] = self.slave.position.copy()
                    self.calibrationStep += 1
                    if self.calibrationStep >= 4:
                        return True # Calibration done, let's quit
                    time.sleep(1)
                    time.sleep(self.slave.move(self.calibrationData[self.calibrationStep]))
					
        return False