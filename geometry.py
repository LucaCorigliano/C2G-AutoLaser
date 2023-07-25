import math

# Get equidistant points between two points
def eq_point(a, b, current, total):
    total = total - 1
    step = 1 / total
    current = step * current
    ret = { "X" : 0, "Y" : 0 }
    ret["X"] = a["X"] + (b["X"]-a["X"]) * current
    ret["Y"] = a["Y"] + (b["Y"]-a["Y"]) * current
    return ret
# Get a point in the grid in the trapezoid
def get_point(trapezoid, x, y, grid):
    p0 = eq_point(trapezoid[0], trapezoid[2], x, grid["X"])
    p1 = eq_point(trapezoid[1], trapezoid[3], x, grid["X"])
    intersection = eq_point(p0, p1, y, grid["Y"])
    return intersection
# Get the angle between three points
def get_angle(a, b, c):
    ang = math.degrees(math.atan2(c["Y"]-b["Y"], c["X"]-b["X"]) - math.atan2(a["Y"]-b["Y"], a["X"]-b["X"]))
    return ang + 360 if ang < 0 else ang
def get_slope_x(a, b):
    return (b["Y"] - a["Y"]) / (b["X"] - a["X"]) 
def get_slope_y(a, b):
    return (b["X"] - a["X"]) / (b["Y"] - a["Y"]) 
def get_distance(a, b):
    return math.sqrt(math.pow((b["X"] - a["X"]), 2) + math.pow((b["Y"] - a["Y"]), 2))
def get_x(point, slope, y):
    return (slope * (y - point['Y'])) + point['X']
def get_y(point, slope, x):
    return (slope * (x - point['X'])) + point['Y']
# Convert a geometry point to a cv2 point
def gtoc(a):
    return [int(a["X"]), int(a["Y"])]
# Convert a cv2 point to a geometry point
def ctog(b):
    return {"X" : b[0], "Y" : b[1]}
def flip_y(a):
    return {"X" : a["X"], "Y" : -a["Y"]}
def flip_x(a):
    return {"X" : -a["X"], "Y" : a["Y"]}
def sum(a, b):
    return {
        "X" : a["X"] + b["X"],
        "Y" : a["Y"] + b["Y"],
    }
def sub(a, b):
    return {
        "X" : a["X"] - b["X"],
        "Y" : a["Y"] - b["Y"],
    }
def csub(a, b, cond):
    if cond:
        return sub(a, b)
    return a
