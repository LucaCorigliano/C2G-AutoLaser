from geometry import eq_point, get_distance, csub
# 3D Printer Configuration
class SlaveConfig:
    max_calibration_error = 0.7
    timeout = 0
    firstwait = 1
    afterhome_wait = 2
    usermove_wait = 0.05
    base_speed = 0.1 
    base_speed = {
        'X' : 350 * 1000,
        'Y' : 350 * 1000,
    }
    user_move_speed = {
        'base' : {
            'X' : 20,
            'Y' : 20,
        },
        "fast" : {
            'X' : 400,
            'Y' : 400,
        }
    }
class CameraConfig:
    safePhotoWait = 0.8
    width = 640
    height = 480
    preview_size = [
        1280, 
        720
    ]
    preview_grid_pace = 40
    fps = 60

class CutConfig:
    #    camera_offset = {
    #    'X' : 1264,
    #    'Y' : -39,
    #}
    camera_offset = {
        'X' : 1320,
        'Y' : -10,
    }
    base_cut_offset = {
        'X' : 230,
        'Y' : -220
    }
    squiggle_count = {
        'X' : 420,
        'Y' : int(420*2),
    }
    corner_offset = [
        {
            'X' : 0,
            'Y' : 0,
        },
        {
            'X' : 0,
            'Y' : 0,
        }
    ]
    squiggle_amount = 60
    num_passes = 3
    speed = 30
    time_before_cut = 2
    corner_cut_offset = 80
    
    corner_size = 200
    corner_speed = 20
    corner_passes = 2
    corner_squiggle = 25
    corner_squiggle_count = 40

    
    side_size = 700
    side_speed = 25
    side_passes = 2
    side_squiggle = 25
    side_squiggle_count = 140   
    @staticmethod
    def get_corner_cut_points(calibration, camera_offset={"X" : 0, "Y" : 0}, relative = False):
        offset_points = CutConfig.get_corner_points(calibration, camera_offset=camera_offset)
        # Get total distance between points
        d = [
            get_distance(offset_points[0], offset_points[1]),
            get_distance(offset_points[0], offset_points[2]),
            get_distance(offset_points[3], offset_points[1]),
            get_distance(offset_points[3], offset_points[2]),
        ]      
        
        
        corner_points = [
            [
                csub(offset_points[0], offset_points[0], relative),
                csub(eq_point(offset_points[0], offset_points[1], CutConfig.corner_size, d[0]), offset_points[0], relative),
                csub(eq_point(offset_points[0], offset_points[2], CutConfig.corner_size, d[1]), offset_points[0], relative),
            ],
            [
                csub(offset_points[1], offset_points[1], relative),
                csub(eq_point(offset_points[1], offset_points[0], CutConfig.corner_size, d[0]), offset_points[1], relative),
                csub(eq_point(offset_points[1], offset_points[3], CutConfig.corner_size, d[2]), offset_points[1], relative),
            ],
            [
                csub(offset_points[2], offset_points[2], relative),
                csub(eq_point(offset_points[2], offset_points[3], CutConfig.corner_size, d[3]), offset_points[2], relative),
                csub(eq_point(offset_points[2], offset_points[0], CutConfig.corner_size, d[1]), offset_points[2], relative),
            ],
            [
                csub(offset_points[3], offset_points[3], relative),
                csub(eq_point(offset_points[3], offset_points[2], CutConfig.corner_size, d[3]), offset_points[3], relative),
                csub(eq_point(offset_points[3], offset_points[1], CutConfig.corner_size, d[2]), offset_points[3], relative),
            ],
            [
                csub(eq_point(offset_points[0], offset_points[1], (d[0] / 2) - (CutConfig.side_size) / 2, d[0]), offset_points[0], relative),
                csub(eq_point(offset_points[0], offset_points[1], (d[0] / 2) + (CutConfig.side_size) / 2, d[0]), offset_points[0], relative),
                {"X" : 0, "Y" : 0},
            ],
            [
                csub(eq_point(offset_points[0], offset_points[2], (d[1] / 2) - (CutConfig.side_size) / 2, d[1]), offset_points[0], relative),
                csub(eq_point(offset_points[0], offset_points[2], (d[1] / 2) + (CutConfig.side_size) / 2, d[1]), offset_points[0], relative),
                {"X" : 0, "Y" : 0},
            ],
            [
                csub(eq_point(offset_points[3], offset_points[1], (d[2] / 2) - (CutConfig.side_size) / 2, d[2]), offset_points[0], relative),
                csub(eq_point(offset_points[3], offset_points[1], (d[2] / 2) + (CutConfig.side_size) / 2, d[2]), offset_points[0], relative),
                {"X" : 0, "Y" : 0},
            ],
            [
                csub(eq_point(offset_points[2], offset_points[3], (d[3] / 2) - (CutConfig.side_size) / 2, d[3]), offset_points[0], relative),
                csub(eq_point(offset_points[2], offset_points[3], (d[3] / 2) + (CutConfig.side_size) / 2, d[3]), offset_points[0], relative),
                {"X" : 0, "Y" : 0},
            ],
        ]      
        return corner_points
    
    @staticmethod
    def get_cut_points(calibration, camera_offset={"X" : 0, "Y" : 0}, preview_order=False, relative = False):
        offset_points = CutConfig.get_corner_points(calibration, camera_offset=camera_offset)
        
        # Get total distance between points
        d = [
            get_distance(offset_points[0], offset_points[1]),
            get_distance(offset_points[0], offset_points[2]),
            get_distance(offset_points[3], offset_points[1]),
            get_distance(offset_points[3], offset_points[2]),
        ]
        cut_points = [
            [
                eq_point(offset_points[0], offset_points[1], CutConfig.corner_cut_offset, d[0]),
                eq_point(offset_points[0], offset_points[1], d[0] - CutConfig.corner_cut_offset, d[0])
            ],
            [
                eq_point(offset_points[0], offset_points[2], CutConfig.corner_cut_offset, d[1]),
                eq_point(offset_points[0], offset_points[2], d[1] - CutConfig.corner_cut_offset, d[1])
            ],           
            [
                eq_point(offset_points[3], offset_points[1], CutConfig.corner_cut_offset, d[2]),
                eq_point(offset_points[3], offset_points[1], d[2] - CutConfig.corner_cut_offset, d[2])
            ],      
            [
                eq_point(offset_points[3], offset_points[2], CutConfig.corner_cut_offset, d[3]),
                eq_point(offset_points[3], offset_points[2], d[3] - CutConfig.corner_cut_offset, d[3])
            ],                       
        ]
        # Make the offsets relative
        if relative:
            cut_points[0][0]["X"] -= offset_points[0]["X"]
            cut_points[0][0]["Y"] -= offset_points[0]["Y"]
            cut_points[0][1]["X"] -= offset_points[1]["X"]
            cut_points[0][1]["Y"] -= offset_points[1]["Y"]
            cut_points[1][0]["X"] -= offset_points[0]["X"]
            cut_points[1][0]["Y"] -= offset_points[0]["Y"]
            cut_points[1][1]["X"] -= offset_points[2]["X"]
            cut_points[1][1]["Y"] -= offset_points[2]["Y"]
            cut_points[2][0]["X"] -= offset_points[3]["X"]
            cut_points[2][0]["Y"] -= offset_points[3]["Y"]
            cut_points[2][1]["X"] -= offset_points[1]["X"]
            cut_points[2][1]["Y"] -= offset_points[1]["Y"]
            cut_points[3][0]["X"] -= offset_points[3]["X"]
            cut_points[3][0]["Y"] -= offset_points[3]["Y"]
            cut_points[3][1]["X"] -= offset_points[2]["X"]
            cut_points[3][1]["Y"] -= offset_points[2]["Y"]
        # Reorder them to make previewing easy
        if preview_order:
            return [
                [
                    cut_points[0][0],
                    cut_points[1][0],
                ],
                [
                    cut_points[0][1],
                    cut_points[2][1],
                ],
                [
                    cut_points[1][1],
                    cut_points[3][1],
                ],
                [
                    cut_points[3][0],
                    cut_points[2][0],
                ],
            ]
        return cut_points
    @staticmethod
    def get_corner_points(calibration, camera_offset={"X" : 0, "Y" : 0}):
        return [
            {
                'X' : calibration[0]['X'] + CutConfig.base_cut_offset['X'] + CutConfig.corner_offset[0]['X'] + camera_offset['X'],
                'Y' : calibration[0]['Y'] + CutConfig.base_cut_offset['Y'] + CutConfig.corner_offset[0]['Y'] + camera_offset['Y'],
            },
            {
                'X' : calibration[1]['X'] - CutConfig.base_cut_offset['X'] + CutConfig.corner_offset[1]['X'] + camera_offset['X'],
                'Y' : calibration[1]['Y'] + CutConfig.base_cut_offset['Y'] + CutConfig.corner_offset[0]['Y'] + camera_offset['Y'],
            },
            {
                'X' : calibration[2]['X'] + CutConfig.base_cut_offset['X'] + CutConfig.corner_offset[0]['X'] + camera_offset['X'],
                'Y' : calibration[2]['Y'] - CutConfig.base_cut_offset['Y'] + CutConfig.corner_offset[1]['Y'] + camera_offset['Y'],
            },
            {
                'X' : calibration[3]['X'] - CutConfig.base_cut_offset['X'] + CutConfig.corner_offset[1]['X'] + camera_offset['X'],
                'Y' : calibration[3]['Y'] - CutConfig.base_cut_offset['Y'] + CutConfig.corner_offset[1]['Y'] + camera_offset['Y'],
            },
        ]                   
        
if __name__ == "__main__":
    import cv2
    import numpy as np
    from geometry import gtoc, flip_y
    w = 1920
    h = 1080  
    img = np.zeros((h, w, 3), np.uint8)
    
    calibration = [
        {'X' : 200, 'Y' : -200},
        {'X' : 700, 'Y' : -250},
        {'X' : 200, 'Y' : -900},
        {'X' : 700, 'Y' : -950},
    ]
    corner_points = CutConfig.get_corner_points(calibration)
    cut_points = CutConfig.get_cut_points(calibration, preview_order=True, relative=True)
    
    colors = [
        (0, 255, 0),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
    ]
    for i in range(4):
        cv2.circle(img, gtoc(flip_y(calibration[i])), 5, colors[i], 3)
        cv2.circle(img, gtoc(flip_y(corner_points[i])), 5, colors[i], 3)
        cv2.circle(img, gtoc(flip_y(cut_points[i][0])), 5, colors[i], 3)
        cv2.circle(img, gtoc(flip_y(cut_points[i][1])), 5, colors[i], 3)
    cv2.imshow("Slope", img)
    cv2.waitKey()