from config import  CameraConfig
from image_processor import ImageProcessor
import numpy as np
import cv2
import os
import shutil
import pickle

class EdgeDetector():
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
        'bilateralFilter' : [0, 1],
        'threshold' : [0, 2],
        'closeSize' : [1, 20],
        'closeIterations' : [1, 25],
        'contourMinArea' : [50000, 100000],
        'contourMinWidth' : [100, 500],
        'contourMinHeight' : [100, 500],
    }
    default_config = {
        'increaseContrast': 1.9544723842879224, 
        'scaleRatio': 1.486714200487834, 
        'saturate': 1.4395885010211593, 
        'brightness': 1.7156706125335388, 
        'blurRadius': 7, 
        'bilateralFilter': 0, 
        'threshold': 2,
        'closeSize': 1,
        'closeIterations': 9,
        'contourMinArea': 97434,
        'contourMinWidth': 468,
        'contourMinHeight': 361   
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
        success, coordinates, preview = self.detect_edges(src, self.current_config)
        if not success:
            preview = src.copy()
        cv2.imshow(self.manual_title_preview, ImageProcessor.resize_for_preview(preview, CameraConfig.preview_size))        
    def manual_config(self, src, config):
        self.current_config = config
        self.manual_image = src
        success, coordinates, preview = self.detect_edges(src, self.current_config)
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
    def detect_edges(self, src, config):
        
        # Reset debug counter
        self.debug_reset()
        self.debug_step(src)
        # Create a copy to work on
        working = src.copy()
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

        # Grayscale
        working = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
        self.debug_step(working)

        # Bit of sharpening / noise reduction
        if config['bilateralFilter'] == 1:
            working = cv2.bilateralFilter(working, 11, 17, 17)
            self.debug_step(working)

        # Get a nice and clean threshold
        
        _, t1 = cv2.threshold(working, 70, 255,  cv2.THRESH_BINARY)
        _, t2 = cv2.threshold(working, 50, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        if config["threshold"] == 0:
            working = t1
        elif config["threshold"] == 1:
            working = t2
        else:
            working = t1 + t2
        self.debug_step(working)
        
        # Threshold closing
        if config['closeIterations'] > 0:
            close_kernel_shape = cv2.MORPH_ELLIPSE
            close_kernel_size = config["closeSize"]
            # Create structure element for extracting horizontal lines through morphology operations
            close_kernel = cv2.getStructuringElement(close_kernel_shape, (close_kernel_size, close_kernel_size))
            # Apply morphology operations
            working = cv2.morphologyEx(working, cv2.MORPH_CLOSE, close_kernel, iterations=config["closeIterations"])
            self.debug_step(working)
        self.debug_step(working)
        

        contours, _ = cv2.findContours(working, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        picked_contours = []
        for c in contours:
            # Avoid small contours
            #print(cv2.contourArea(c))
            x,y,w,h = cv2.boundingRect(c)
            if cv2.contourArea(c) < config["contourMinArea"] and w < config["contourMinWidth"] and h < config["contourMinHeight"]:
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
                
                return False, None, None
            preview = cv2.circle(preview, coordinate, 20, (255, 0, 255), 10)
        cv2.drawContours(preview, picked_contours, -1, (0, 255, 255), 3)
        
        self.debug_step(preview)
        if self.debug:
            cv2.waitKey()
        


        return True, coordinates, preview
    
# Testing
if __name__ == "__main__":
    file = "E:\\C2G\\220834239\\Front\\ring\\002003.png"
    src = cv2.imread(file)
    
    ed = EdgeDetector()
    
    ed.manual_config(src, ed.default_config.copy())
    
    import sys
    sys.exit(1)
    directory = "E:\\C2G\\samples"
    best_failure_count = 8
    samples = []
    self = EdgeDetector()
    while True:
        base = self.ab_config.copy()
        with open(f"best.pickle", 'rb') as handle:
            base = pickle.load(handle)        
        #for key in base.keys():
        #    a = base[key][0]
        #    b = base[key][1]
        #    
        #    if(isinstance(a, int)):
        #        base[key] = random.randint(a, b)
        #    else:
        #        base[key] = random.uniform(a, b)
                
        baseHash = hash(frozenset(base.items()))
        print(f"Currently processing {baseHash}")                
        
        failures = 0
        count = 0
       
        shutil.rmtree(directory + "/out", ignore_errors=True)
        shutil.rmtree(directory + "/fail", ignore_errors=True)
        os.mkdir(directory + "/out")
        os.mkdir(directory + "/fail")
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            # checking if it is a file
            if os.path.isfile(f):
                src = cv2.imread(f)
                success, coordinates, dst = self.detect_edges(src, base)
                count = count + 1
                if not success:
                    #print("Failed to detect edges.")
                    failures = failures + 1
                    #cv2.imwrite(f"{directory}\\fail\\{filename}", src)
                else:
                    good_coordinate = coordinates[0]
                    if "000007" in filename:
                        good_coordinate = coordinates[1]
                        good_coordinate[0] = abs(good_coordinate[0] - 1920)
                    elif "017000" in filename:
                        good_coordinate = coordinates[2]
                        good_coordinate[1] = abs(good_coordinate[1] - 1080)
                    elif "017007" in filename:
                        good_coordinate = coordinates[3]
                        good_coordinate[0] = abs(good_coordinate[0] - 1920)
                        good_coordinate[1] = abs(good_coordinate[1] - 1080)    
                        
                    if good_coordinate[0] < 90 or good_coordinate[0] > 300:
                        #print("Failed to detect X axis.")
                        failures = failures + 1
                        success = False
                        cv2.imwrite(f"{directory}\\fail\\{filename}", dst)
                    elif good_coordinate[1] < 50 or good_coordinate[1] > 400:
                        #print("Failed to detect Y axis.")
                        failures = failures + 1
                        success = False
                        cv2.imwrite(f"{directory}\\fail\\{filename}", dst)
                    else:
                        #print(f"{filename} has {good_coordinate} ")
                        cv2.imwrite(f"{directory}\\out\\{good_coordinate[1]}_{good_coordinate[0]}.jpg", dst)
        break
            