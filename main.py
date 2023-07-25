
#External dependencies
import time
import signal
import sys
from datetime import timedelta
from pathlib import Path
import pickle
import os
import colorama
from autocalibrate import AutoCalibrate


# Internal dependencies
from config import SlaveConfig, CutConfig
from slave import Slave
from camera import Camera
from arg_parser import ArgumentParser
from utils import colors
from viewfinder import Viewfinder, ViewfinderModes
from fileman import fm


# Handle CTRL+C Exit
exit_attempts = 0
def keyboardExit(sig, frame):
    print("------------------------------------------------------------------")
    print(f"{colors.cross} User requested exit")
    try:
        if slave:
            print("Killing slave")
            slave.stop_sending_data()
            slave.pause_un_pause()
            slave.release_usb()
        raise SystemExit()

    except:
        sys.exit(99)
        raise SystemExit()
signal.signal(signal.SIGINT, keyboardExit)

# Global variables
verbose = False
slave = None
# Diagnostic print
def dprint(text):
    if verbose:
        print(f"{colors.DEBUG} [DBG]{text}{colors.ENDC}")
def laser_callback(message=None, bgcolor=None):
    return True
    if message!=None:
        print(f"{colors.laser} {message}")
    return True
if __name__ == "__main__":
    colorama.init()
    try:
        print(f"{colors.OKGREEN} [ C2G AutoLaser ] {colors.ENDC}- 2022 Corigliano Luca")
        
        # Load config
        args = ArgumentParser.get() 
        if args.verbose:
            verbose = True
        
        # Choose working folder
        fm.set_cwd(args.topFolder)
        # Start time
        startTime = time.time()

           
        # Camera 
        attempts = 0
        while True:
            attempts += 1
            print(f"{colors.wait} Connecting to Microscope at index {args.webcamIndex}, attempt {attempts}")
            camera, cw, ch = Camera.connect(args.webcamIndex)
            if int(cw) == 0:
                if attempts == 10:
                    print(f"{colors.cross} Failed to connect to camera")
                    sys.exit(-5)
                continue
            print(f"{colors.check} Done, got a resolution of {int(cw)}x{int(ch)}")
            break
        
        # Slave
        slave = Slave()
        slave.initialize_device(verbose=slave.diagnostic)
    
        # Waiting a bit
        print(f"{colors.check} Connected, waiting {SlaveConfig.firstwait}s before homing")
        time.sleep(SlaveConfig.firstwait)

        # Auto home
        slave.auto_home()
        print(f"{colors.wait} Waiting {SlaveConfig.afterhome_wait}s for homing")
        time.sleep(SlaveConfig.afterhome_wait)      
        
        # Initialize Viewfinder
        viewFinder = Viewfinder(camera, slave, {"workingFolder" : args.topFolder})

        # Do calibration
        if args.calibrate:
            # Load old calibration to be fast
            hasCalibration = False
            if fm.isfile("calibration.pickle"):
                with fm.open('calibration.pickle', 'rb') as handle:
                    calibration = pickle.load(handle)
                hasCalibration = True
            else:
                calibration = [{}] * 4
            if hasCalibration:
                time.sleep(slave.move( calibration[0]))
            viewFinder.currentMode = ViewfinderModes.MODE_CALIBRATION
            viewFinder.calibrationStep = 0
            viewFinder.calibrationData = calibration
            # Show viewfinder
            viewFinder.show()
            # Save calibration
            calibration = viewFinder.calibrationData
            for i in range(4):
                print(f"{colors.line} Calibration {i} = {calibration[i]['X']} {calibration[i]['Y']}!")
            with fm.open('calibration.pickle', 'wb') as handle:
                pickle.dump(calibration, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"{colors.check} Done, calibration saved!")
            sys.exit(1)
        
        # Load calibration
        if not fm.isfile("calibration.pickle"):
            print(f"{colors.cross} Calibration not found!")
            print(f"{colors.space} Launch calibration with the --calibrate argument")	
            sys.exit(-4)
            
        with fm.open('calibration.pickle', 'rb') as handle:
            calibration = pickle.load(handle)

        # Moving
        print(f"{colors.line} Moving to base position")
        time.sleep(slave.move(calibration[0]))
        
        # Asking user to line up the card
        print(f"{colors.userwait} Asking user for focus and line up")
        viewFinder.show()

        # If it's viewfinder mode we can quit after it
        if args.viewFinder:
            sys.exit(1)

        # Reset to base position if we moved
        if viewFinder.moved: 
            time.sleep(slave.move( calibration[0]))





        # Perform automatic calibration finetuning
        print(f"{colors.line} Automatic calibration")
        autoCalibrate = AutoCalibrate(camera, slave, calibration)
        autoCalibrate.auto_calibrate(manual_config=args.difficultCalibration, show_cut_preview=True, is_corner_cut=args.corners)
        
        if autoCalibrate.angle_error > SlaveConfig.max_calibration_error:
            print(f"{colors.cross} Automatic calibration failed, angle error {autoCalibrate.angle_error} is higher than allowed ({SlaveConfig.max_calibration_error})")
        else:
            print(f"{colors.check} Automatic calibration success! Max error {autoCalibrate.angle_error}")
        # Save the auto calibration
        calibration = autoCalibrate.calibration      
        with fm.open('calibration.pickle', 'wb') as handle:
            pickle.dump(calibration, handle, protocol=pickle.HIGHEST_PROTOCOL)              
        # Show a preview for confirmation
        print(f"{colors.userwait} Asking user to confirm calibration")
        viewFinder.currentMode = ViewfinderModes.MODE_STATIC
        viewFinder.show(autoCalibrate.corners_preview)

        # Calculate offsets for cutting
        
        
        if args.corners:
            cut_coordinates = CutConfig.get_corner_cut_points(calibration, camera_offset=CutConfig.camera_offset)
            
            for i in range(4):
                # Cut
                print(f"{colors.laser} Corner #{i}: A -> B, Pass [{CutConfig.corner_passes}] : ", end='')
                time.sleep(slave.move(cut_coordinates[i][0]))
                time.sleep(CutConfig.time_before_cut)
                for j in range(CutConfig.corner_passes):
                    print(f"{j+1}...", end='')
                    slave.squiggly_cut(cut_coordinates[i][0],
                                    cut_coordinates[i][1], 
                                    CutConfig.corner_speed,
                                    CutConfig.corner_squiggle_count,
                                    CutConfig.corner_squiggle,
                                    CutConfig.corner_squiggle,
                                    callback=laser_callback)   
                print(f" / ", end='')    
                time.sleep(CutConfig.time_before_cut)
                for j in range(CutConfig.corner_passes):
                    print(f"{j+1}...", end='')
                    slave.squiggly_cut(cut_coordinates[i][0],
                                    cut_coordinates[i][2], 
                                    CutConfig.corner_speed,
                                    CutConfig.corner_squiggle_count,
                                    CutConfig.corner_squiggle,
                                    CutConfig.corner_squiggle,
                                    callback=laser_callback)      
                print('\n')
            for i in range(4):
                # Cut
                print(f"{colors.laser} Side #{i}: A -> B, Pass [{CutConfig.side_passes}] : ", end='')
                time.sleep(slave.move(cut_coordinates[4+i][0]))
                time.sleep(CutConfig.time_before_cut)

                
                for j in range(CutConfig.side_passes):
                    print(f"{j+1}...", end='')
                    slave.squiggly_cut(cut_coordinates[4+i][0],
                                    cut_coordinates[4+i][1], 
                                    CutConfig.side_speed,
                                    CutConfig.side_squiggle_count,
                                    CutConfig.side_squiggle,
                                    CutConfig.side_squiggle,
                                    callback=laser_callback)   
                print('\n')
            
        else:
            cut_coordinates = CutConfig.get_cut_points(calibration, camera_offset=CutConfig.camera_offset)
        
            # Cut
            print(f"{colors.laser} Cut #1: A -> B, Pass : ", end='')
            time.sleep(slave.move( cut_coordinates[0][0]))
            time.sleep(CutConfig.time_before_cut)
            for i in range(CutConfig.num_passes):
                print(f"{i+1}...", end='')
                slave.squiggly_cut(cut_coordinates[0][0],
                                cut_coordinates[0][1], 
                                CutConfig.speed,
                                CutConfig.squiggle_count['X'],
                                0,
                                CutConfig.squiggle_amount,
                                callback=laser_callback)
            
            print(f"\n{colors.laser} Cut #2: A -> C, Pass : ", end='')  
            time.sleep(slave.move( cut_coordinates[1][0]))
            time.sleep(CutConfig.time_before_cut)       
            for i in range(CutConfig.num_passes):
                print(f"{i+1}...", end='')
                slave.squiggly_cut(cut_coordinates[1][0],
                                cut_coordinates[1][1], 
                                CutConfig.speed,
                                CutConfig.squiggle_count['Y'],
                                CutConfig.squiggle_amount,
                                0,
                                callback=laser_callback)
            
            print(f"\n{colors.laser} Cut #3: D -> B, Pass : ", end='')   
            time.sleep(slave.move(cut_coordinates[2][0]))
            time.sleep(CutConfig.time_before_cut)
            for i in range(CutConfig.num_passes):
                print(f"{i+1}...", end='')
                slave.squiggly_cut(cut_coordinates[2][0],
                                cut_coordinates[2][1], 
                                CutConfig.speed,
                                CutConfig.squiggle_count['Y'],
                                CutConfig.squiggle_amount,
                                0,
                                callback=laser_callback)
            
            print(f"\n{colors.laser} Cut #4: D -> C, Pass : ", end='')   
            time.sleep(slave.move( cut_coordinates[3][0]))
            time.sleep(CutConfig.time_before_cut)   
            for i in range(CutConfig.num_passes):
                print(f"{i+1}...", end='')
                slave.squiggly_cut(cut_coordinates[3][0],
                                cut_coordinates[3][1], 
                                CutConfig.speed,
                                CutConfig.squiggle_count['X'],
                                0,
                                CutConfig.squiggle_amount,
                                callback=laser_callback)
            print(f"\n{colors.laser} Finished cutting, homing and releasing...")  
            slave.auto_home()
            time.sleep(3)
        
        slave.release_usb()
        camera.release()
        endTime = time.time()
        elapsed = endTime - startTime
        delta = timedelta(seconds=elapsed)
        delta = delta - timedelta(microseconds=delta.microseconds)
        print(f"{colors.OKGREEN}[ \u2713 ] Done!{colors.ENDC} The process took {delta}s.")			   
    except:
        print("------------------------------------------------------------------")
        print(f"{colors.cross} Program exiting non-succesfully.")
        try:
            slave.stop_sending_data()
        except:
            pass
        try:
            slave.release_usb()
        except:
            pass
        camera.release()
        raise
