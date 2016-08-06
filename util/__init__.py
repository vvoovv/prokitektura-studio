import math
from base import zero2

def acos(angle):
    if angle > 1. or angle < -1.:
        angle = round(angle)
    return math.acos(angle)


def is0degrees(cos):
    return abs(1-cos) < zero2

def is90degrees(cos):
    return abs(cos) < zero2

def is180degrees(cos):
    return abs(cos+1) < zero2