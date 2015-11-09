from item.wall import addTransformsVariable

class Window:
    
    def __init__(self, obj, wall, o1, o2):
        left = o1["l"]
        obj.location = o2.location if left else o1.location
        
        rz = obj.driver_add("rotation_euler", 2)
        addTransformsVariable(rz, "x1", o2 if left else o1, "LOC_X")
        addTransformsVariable(rz, "x2", o1 if left else o2, "LOC_X")
        addTransformsVariable(rz, "y1", o2 if left else o1, "LOC_Y")
        addTransformsVariable(rz, "y2", o1 if left else o2, "LOC_Y")
        rz.driver.expression = "atan2(y2-y1,x2-x1)"