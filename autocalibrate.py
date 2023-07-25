from config import CameraConfig, CutConfig
import time
from led_detector import LedDetector
from slave import Slave
from camera import Camera
import numpy as np
import cv2
import geometry as geom

class AutoCalibrate():
    slave : Slave = None
    camera : Camera = None
    calibration : dict = None
    old_calibration : dict = None
    previews = [None,None,None,None]
    angle_error = 0
    corners_preview = None
    pixel_per_inch = 1500 / 1000
    threshold = 2
    first_offset = None
    def __init__(self, camera, slave, calibration):
        self.camera = camera
        self.slave = slave
        self.calibration = calibration
        self.old_calibration = calibration
    def auto_calibrate(self, manual_config=False, show_cut_preview=False, is_corner_cut=False):

        slave = self.slave
        camera = self.camera
        ledDetector = LedDetector()
        ld_config = ledDetector.default_config
        # Four corners
        for i in range(4):
            # Move to old calibration
            time.sleep(slave.move(self.old_calibration[i]))
            # Wait
            time.sleep(CameraConfig.safePhotoWait)
            
            if i == 0 and manual_config:
                # Discard first frame because of reasons
                _, discard = camera.capturePhotoSharpness(num_samples=2)
                # Fetch a frame 
                _, src = camera.capturePhotoSharpness(num_samples=2)
                
                ld_config = ledDetector.manual_config(src, ld_config)

            # This will take several steps
            attempts = 0
            while True:
                # Discard first frame because of reasons
                _, discard = camera.capturePhotoSharpness(num_samples=2)
                # Fetch a frame 
                _, src = camera.capturePhotoSharpness(num_samples=2)
                
                success, center, preview = ledDetector.detect_led(src, config=ld_config)

                if not success:
                    attempts += 1
                    if attempts == 1 and self.first_offset != None:
                        time.sleep(slave.move_rel(self.first_offset))
                        time.sleep(0.3)
                        continue
                    if attempts > 10:
                        raise Exception("Unable to find corner")
                    
                    time.sleep(0.3)
                    continue
                
                self.previews[i] = preview

                target = [CameraConfig.height / 2, CameraConfig.width /2]
                
                
  
                       
                # Get distance we need to cover
                delta = {
                    'X' : abs(target[0]) - center[0],
                    'Y' : abs(target[1]) - center[1],
                }
                pixel_delta = delta.copy()


                #print(f"Current: {center}, Delta: {delta}")



                # Convert to mm
                delta['X'] /= self.pixel_per_inch
                delta['Y'] /= self.pixel_per_inch

                delta['X'] = int(-delta['X'])
                delta['Y'] = int(delta['Y'])
                
                if self.first_offset == None:
                    self.first_offset = delta
                
                #print(f"Movement: {delta}")
                time.sleep(slave.move_rel(delta))
                time.sleep(0.3)
                if(abs(pixel_delta['X']) <= self.threshold and abs(pixel_delta['Y']) <= self.threshold):
                    self.calibration[i] = slave.position.copy()
                    break
        # Build a preview image
        self.corners_preview = np.vstack((np.hstack((self.previews[0], self.previews[1])), np.hstack((self.previews[2], self.previews[3]))))
        if show_cut_preview:
            # Calculate the angles
            
            # These are the points for each angle
            # 0 Corner on top
            # 1 Actual corner
            # 2 Corner on left/right
            points = [
                #Y X
                [2,1],
                [3,0],
                [0,3],
                [1,2]
            ]

            
            preview_points = CutConfig.get_corner_points(self.calibration)
            cut_points = CutConfig.get_cut_points(self.calibration, preview_order=True, relative=True)
            corner_points = CutConfig.get_corner_cut_points(self.calibration)
            print(corner_points)
            
            
            cut_previews = [None, None, None, None]
            for i in range(4):
                time.sleep(slave.move(preview_points[i]))
                time.sleep(CameraConfig.safePhotoWait)
                # Discard first frame because of reasons
                _, discard = camera.capturePhotoSharpness(num_samples=2)
                # Fetch a frame 
                _, src = camera.capturePhotoSharpness(num_samples=2)  
                (h, w) = src.shape[:2]            
                
                mid_point = {"X" : w/2, "Y" : h/2}
                
                
                # Get angle to tell the user
                angle = geom.get_angle(
                    self.calibration[points[i][0]],
                    self.calibration[i],
                    self.calibration[points[i][1]],
                )
                if angle > 180:
                    angle -= 180
                difference = abs(90 - angle)
                if difference > self.angle_error:
                    self.angle_error = difference

                
                # Draw the cutting lines
                # Draw the cutting points
                src = cv2.circle(src, geom.gtoc(mid_point), 5, (0, 255, 0), 3)
                
                if is_corner_cut:
                     for j in range(2):
                        print(i)
                        print(corner_points[i])
                        p0 = geom.sum(mid_point, geom.flip_y(corner_points[i][0]))
                        p1 = geom.sum(mid_point, geom.flip_y(corner_points[i][1]))
                        p2 = geom.sum(mid_point, geom.flip_y(corner_points[i][2]))
                        for k in range(10):
                            cv2.circle(src, geom.gtoc(geom.eq_point(p0, p1, k, 10)), CutConfig.squiggle_amount, (0, 255, 0), 2 )                   
                            cv2.circle(src, geom.gtoc(geom.eq_point(p0, p2, k, 10)), CutConfig.squiggle_amount, (0, 255, 0), 2 )                   
                else:
                    for j in range(2):
                        p0 = mid_point
                        p1 = geom.sum(mid_point, geom.flip_y(cut_points[i][j]))
                        p2 = geom.eq_point(p0, p1, 400, 100)
                        cv2.circle(src, geom.gtoc(p1), CutConfig.squiggle_amount, (0, 255, 255), 2)
                        for k in range(10):
                            cv2.circle(src, geom.gtoc(geom.eq_point(p1, p2, k, 10)), CutConfig.squiggle_amount, (0, 255, 0), 2 )    
                  
                cut_previews[i] = src
                #src = cv2.circle(src, geom.gtoc(geom.sum(mid_point, geom.flip_y(cut_points[i][0]))), CutConfig.squiggle_amount, (255, 255, 0), 3)
                #src = cv2.circle(src, geom.gtoc(geom.sum(mid_point, geom.flip_y(cut_points[i][1]))), CutConfig.squiggle_amount, (0, 255, 255), 3)
                #src = cv2.circle(src, atob(startY_point), 5, (0, 255, 0), 3)                
                  
                cut_previews[i] = src
                
                

            cut_preview = np.vstack((np.hstack((cut_previews[0], cut_previews[1])), np.hstack((cut_previews[2], cut_previews[3]))))
            tmp = np.hstack((self.corners_preview, cut_preview))
            self.corners_preview = tmp