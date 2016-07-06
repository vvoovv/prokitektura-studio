import math

def acos(angle):
    if angle > 1. or angle < -1.:
        angle = round(angle)
    return math.acos(angle)