from config import  CameraConfig
from image_processor import ImageProcessor
import numpy as np
import cv2
import os
import shutil
import pickle

class LedDetector():
    # Debug stuff
    debug = False
    debug_current_step = 0    
    
    # A/B Testing
    ab_config = {
        'increaseContrast' : [0.5, 3.0],
        'scaleRatio' : [0.2, 3.0],
        'saturate' : [1.0, 2.5],
        'brightness' : [0.8, 2.5],
        'blurRadius' : [1, 91],
        'closeSize' : [1, 20],
        'closeIterations' : [1, 25],
        'contourMinArea' : [0, 100000],
        'maskMinH' : [0, 255],
        'maskMinS' : [0, 255],
        'maskMinV' : [0, 255],
        'maskMaxH' : [0, 255],
        'maskMaxS' : [0, 255],
        'maskMaxV' : [0, 255],
    }
    default_config_bkp = {
        'increaseContrast': 1.50, 
        'scaleRatio': 0.8, 
        'saturate': 1, 
        'brightness': 1.06, 
        'blurRadius': 11, 
        'closeSize': 1,
        'closeIterations': 9,
        'contourMinArea': 20000,
        'maskMinH' : 25,
        'maskMinS' : 19,
        'maskMinV' : 102,
        'maskMaxH' : 43,
        'maskMaxS' : 255,
        'maskMaxV' : 255,
    }
    default_config = {
        'increaseContrast': 1.30, 
        'scaleRatio': 1.0,
        'saturate': 1, 
        'brightness': 1.06, 
        'blurRadius': 49,
        'closeSize': 1,
        'closeIterations': 0,
        'contourMinArea': 20000,
        'maskMinH' : 14,
        'maskMinS' : 42,
        'maskMinV' : 120,
        'maskMaxH' : 50,
        'maskMaxS' : 255,
        'maskMaxV' : 255,
    }
    current_config = None
    
    # Manual config stuff
    manual_title_config = "Manual configuration"
    manual_title_preview = "Preview"
    manual_image = None
        
    
    
    
    def debug_step(self, image):
        if self.debug:
            cv2.imshow(f"step{self.debug_current_step}", ImageProcessor.resize_for_preview(image, CameraConfig.preview_size))
            self.debug_current_step += 1
    
    def debug_reset(self):
        self.debug_current_step = 0
        
    def on_manual_change(self, val):
        for key in self.ab_config.keys():
            
            val = cv2.getTrackbarPos(key, self.manual_title_config)
            if isinstance(self.ab_config[key][0], float):
                val = float(val) / 100
            self.current_config[key] = val
        src = self.manual_image
        success, center, preview = self.detect_led(src, self.current_config)
        if not success:
            preview = src.copy()
        cv2.imshow(self.manual_title_preview, ImageProcessor.resize_for_preview(preview, CameraConfig.preview_size))        
    def manual_config(self, src, config):
        self.current_config = config
        self.manual_image = src
        success, center, preview = self.detect_led(src, self.current_config)
        if not success:
            preview = src.copy()
        cv2.imshow(self.manual_title_preview, ImageProcessor.resize_for_preview(preview, CameraConfig.preview_size))
        cv2.imshow(self.manual_title_config, ImageProcessor.resize_aspect_ratio(preview, width=500))
        bounds = self.ab_config
        for key in bounds.keys():
            min = bounds[key][0]
            max = bounds[key][1]
            val = config[key]
            
            if isinstance(min, float):
                min = int(min * 100)
                max = int(max * 100)
                val = int(val * 100)
            
            cv2.createTrackbar(key, self.manual_title_config, val, max, self.on_manual_change)
            cv2.setTrackbarMin(key, self.manual_title_config, min)
        cv2.waitKey(0) & 0xFF
        cv2.destroyWindow(self.manual_title_config)
        cv2.destroyWindow(self.manual_title_preview)
        return self.current_config
    def detect_led(self, src, config):
        
        # Reset debug counter
        self.debug_reset()
        self.debug_step(src)
        # Create a copy to work on
        working = src.copy()
        #print(f"Calculated brightness {ImageProcessor.brightness(working)}")
        # Increase contrast
        if config['increaseContrast'] > 0.5:
            working = ImageProcessor.increase_contrast(src, clipLimit=config['increaseContrast'])
        self.debug_step(working)
        # Scale
        if config['scaleRatio'] > 1.02 or config['scaleRatio'] < 0.98:
            scaleSize = int(src.shape[1] * config['scaleRatio'])
            working = ImageProcessor.resize_aspect_ratio(working, width=scaleSize)
            working = ImageProcessor.resize_aspect_ratio(working, width=src.shape[1], inter = cv2.INTER_LINEAR)
        self.debug_step(working)
        
        # Saturate
        if config['saturate'] > 1.02:
            working = ImageProcessor.increase_saturation(working, saturation=config['saturate'])
        self.debug_step(working)
        
        # Blur 
        if config['blurRadius'] > 1.5:
            blurRadius = round(config['blurRadius'])
            if blurRadius % 2 == 0:
                blurRadius += 1
            working = cv2.GaussianBlur(working,(blurRadius, blurRadius), 0)
        self.debug_step(working)
            
        # Detect yellow
        working = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)
        
        # Define yellow mask
        working = cv2.inRange(working, (config['maskMinH'], config['maskMinS'], config['maskMinV']), (config['maskMaxH'], config['maskMaxS'], config['maskMaxV']))
        # Only get yellow-ish
        #working = cv2.bitwise_and(working, working, mask=mask)
        #self.debug_step(working)
        


        
        # Threshold closing
        if config['closeIterations'] > 0:
            close_kernel_shape = cv2.MORPH_ELLIPSE
            close_kernel_size = config["closeSize"]
            # Create structure element for extracting horizontal lines through morphology operations
            close_kernel = cv2.getStructuringElement(close_kernel_shape, (close_kernel_size, close_kernel_size))
            # Apply morphology operations
            working = cv2.morphologyEx(working, cv2.MORPH_CLOSE, close_kernel, iterations=config["closeIterations"])
        self.debug_step(working)
        

        contours, _ = cv2.findContours(working, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        picked_contours = []
        for c in contours:
            if cv2.contourArea(c) < config["contourMinArea"] :
               continue
            picked_contours.append(c)
        
        coordinates = [
            [None, None], # Top Left
            [None, None], # Top Right
            [None, None], # Bottom Left
            [None, None], # Bottom Right
        ]

        # Find current points
        # Foreach contour
        for c in picked_contours:
            # Foreach point
            for s in c:
                for p in s:
                    # Are we more on the left?
                    if coordinates[0][0] == None or p[0] < coordinates[0][0]:
                        coordinates[0][0] = p[0]
                        coordinates[2][0] = p[0]
                    # Or on the right
                    if coordinates[1][0] == None or p[0] > coordinates[1][0]:
                        coordinates[1][0] = p[0]
                        coordinates[3][0] = p[0]
                    # Are we more on the top?
                    if coordinates[0][1] == None or p[1] < coordinates[0][1]:
                        coordinates[0][1] = p[1]
                        coordinates[1][1] = p[1]
                    # Or on the bottom
                    if coordinates[2][1] == None or p[1] > coordinates[2][1]:
                        coordinates[2][1] = p[1]
                        coordinates[3][1] = p[1]

        # Draw a circle in the points we found
        preview = src.copy()
        for coordinate in coordinates:
            if coordinate[0] == None or coordinate[1] == None:
                if self.debug:
                    cv2.waitKey()             
                return False, None, None
            preview = cv2.circle(preview, coordinate, 20, (255, 0, 255), 10)
            
        center = [
            int((coordinates[0][0] + coordinates[3][0]) / 2),
            int((coordinates[0][1] + coordinates[3][1]) / 2)
        ]
        fake_center = [
            int((coordinates[0][0] + coordinates[1][0]) / 2),
            int((coordinates[0][1] + (coordinates[1][0] - coordinates[0][0]) / 2) )
        ]
        cv2.circle(preview, center, 5, (255, 255, 0), 3)
        cv2.circle(preview, fake_center, 10, (0, 255, 0), 3)
        cv2.drawContours(preview, picked_contours, -1, (0, 255, 255), 3)
        
        self.debug_step(preview)
        if self.debug:
            cv2.waitKey()
        


        return True, fake_center, preview
    
# Testing
if __name__ == "__main__":
    file = "F:\\repo\\AutoLaser\\sample\\snap500000_500000.png"
    src = cv2.imread(file)
    
    ed = LedDetector()
    
    ed.manual_config(src, ed.default_config.copy())