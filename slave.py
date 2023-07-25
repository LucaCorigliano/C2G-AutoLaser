import nano_library
import time
import pickle
from egv import egv as Translator
from fileman import fm
from config import SlaveConfig
from geometry import eq_point
from ecoords import ECoord
class Slave(nano_library.K40_CLASS):
    diagnostic = False
    position = {
        "X" : 0,
        "Y" : 0,
    }
    ##################### Movement control
    def auto_home(self, wait_override=-1):
        if wait_override >= 0:
            wait_time = wait_override
        else:
            wait_time = 3
        self.home_position()
        # Reset position
        self.position = {
            "X" : 0,
            "Y" : 0,
        }
        return wait_time
    # Absolute movement
    def move(self, movement_data, wait_override=-1, wait_for_laser=False):
        relative_data = {}
        for axis, absolute in movement_data.items():
            relative_data[axis] = absolute - self.position[axis]
        return self.move_rel(relative_data, wait_for_laser=wait_for_laser)
    def calculate_wait(self, axis, distance):
        speed = SlaveConfig.base_speed[axis]
        distance = abs(distance)
        time = distance / speed * 100 
        #print(f"Movement of {axis} axis of {distance} is going to take {time}")
        return time
    # Relative movement
    def move_rel(self, movement_data, wait_override=-1, wait_for_laser=False):
        # Fill defaults
        if not "X" in movement_data:
            movement_data["X"] = 0
        if not "Y" in movement_data:
            movement_data["Y"] = 0
        current_wait = 0
        for axis, target in movement_data.items():    
            wait_time = self.calculate_wait(axis, target)
            if wait_time > current_wait:
                current_wait = wait_time
        
        # Move the laser head
        self.rapid_move(int(movement_data["X"]), int(movement_data["Y"]), wait_for_laser=wait_for_laser)
        
        # Update local position
        for axis, offset in movement_data.items():
            self.position[axis] += offset
        # Wait as needed
        if wait_override >= 0:
            current_wait = wait_override     
        return current_wait
    # CUTCUTCUT
    def squiggly_cut(self, start, end, speed, squiggly_count, squiggly_move_x, squiggly_move_y, callback=None):
        to_send = [ord("I")]
        scale = 1
        startx = start["X"] / 1000 * scale
        starty = start["Y"] / 1000 * scale
        endx = end["X"] / 1000 * scale
        endy = end["Y"] / 1000 * scale
        
        squiggly_move_x = squiggly_move_x / 1000 * scale
        squiggly_move_y = squiggly_move_y / 1000 * scale
        
        start = {'X' : startx, 'Y' : starty}
        end = {'X' : endx, 'Y' : endy}
        start_up = {'X' : startx + (squiggly_move_x / 2), 'Y' : starty  + (squiggly_move_y / 2)}
        end_up = {'X' : endx + (squiggly_move_x / 2), 'Y' : endy + (squiggly_move_y / 2)}   
        start_down = {'X' : startx - (squiggly_move_x / 2), 'Y' : starty  - (squiggly_move_y / 2)}
        end_down = {'X' : endx - (squiggly_move_x / 2), 'Y' : endy - (squiggly_move_y / 2)}   
        
        points = [[startx, starty, 0]]
        
        for i in range(squiggly_count):
            if i == 0 or i == squiggly_count - 1:
                continue
            intermediate_up = eq_point(start_up, end_up, i, squiggly_count)
            intermediate_down = eq_point(start_down, end_down, i, squiggly_count)
            if i % 2 != 0:
                intermediate = intermediate_up
            else:
                intermediate = intermediate_down
            points.append([intermediate['X'], intermediate['Y'], 0])
        points.append([endx, endy, 0])
        #print(points)
        Vector_Cut_egv_inst = Translator(target=lambda s:to_send.append(s))   
        Vector_Cut_egv_inst.make_egv_data(
                                        points,                      \
                                        startX=startx,                    \
                                        startY=starty,                    \
                                        Feed = speed,                 \
                                        board_name="LASER-M2", \
                                        Raster_step = 0,                  \
                                        update_gui=callback,       \
                                        FlipXoffset=0,          \
                                        Rapid_Feed_Rate = 0,     \
                                        use_laser=True)

        #print(to_send)
        self.send_data(to_send, update_gui=callback, wait_for_laser=True)
        
    def vector_cut(self, start, end, speed, callback=None):
        to_send = [ord("I")]
        coords = []
        
        scale = 1
        startx = start["X"] / 1000 * scale
        starty = start["Y"] / 1000 * scale
        endx = end["X"] / 1000 * scale
        endy = end["Y"] / 1000 * scale
        points = [
            [startx, starty, 0],
            [endx, endy, 0]
        ]

        #print(points)
        Vector_Cut_egv_inst = Translator(target=lambda s:to_send.append(s))   
        Vector_Cut_egv_inst.make_egv_data(
                                        points,                      \
                                        startX=startx,                    \
                                        startY=starty,                    \
                                        Feed = speed,                 \
                                        board_name="LASER-M2", \
                                        Raster_step = 0,                  \
                                        update_gui=callback,       \
                                        FlipXoffset=0,          \
                                        Rapid_Feed_Rate = 0,     \
                                        use_laser=True)

        #print(to_send)
        self.send_data(to_send, update_gui=callback, wait_for_laser=True)