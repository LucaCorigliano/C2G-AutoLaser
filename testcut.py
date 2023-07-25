from tkinter import W
from geometry import eq_point
import cv2
import numpy as np
def squiggly_cut(img, start, end, speed, squiggly_count, squiggly_move_x, squiggly_move_y, callback=None):
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
    
    
    img = cv2.line(img, [int(start_up['X'] * 1000), int(start_up['Y'] * 1000)], [int(end_up['X'] * 1000), int(end_up['Y'] * 1000)], (255, 255, 255), 1)
    img = cv2.line(img, [int(start_down['X'] * 1000), int(start_down['Y'] * 1000)], [int(end_down['X'] * 1000), int(end_down['Y'] * 1000)], (255, 255, 255), 1)
    
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
    return points



w = 1280
h = 720
img = np.zeros((h, w, 3), np.uint8)
points = squiggly_cut(img, {'X' : 20, 'Y' : 30}, {'X' : 400, 'Y' : 20}, 10, 40, 0, 10)
points = points[::-1]
points += squiggly_cut(img, {'X' : 20, 'Y' : 30}, {'X' : 40, 'Y' : 600}, 10, 40, 10, 0)
print(points)
point_len = len(points)
for i in range(point_len):
    p = [int(points[i][0] * 1000), int(points[i][1] * 1000)]
    if i == point_len - 1 or i == 0: 
        img = cv2.circle(img, p, 3, (0, 255, 0), 2)
        if i == point_len - 1:
            break
    next = [int(points[i+1][0] * 1000), int(points[i+1][1] * 1000)]
    img = cv2.line(img, p, next, (255, 0, 255), 2)
cv2.imshow("Squiggly", img)
cv2.waitKey()