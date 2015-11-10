from blender_util import addBooleanModifier
from item.wall import addTransformsVariable, addLocDiffVariable, addSinglePropVariable

class Window:
    
    floorToWindow = 0.75
    
    def __init__(self, obj, wall, o1, o2):
        self.obj = obj
        self.lookup()
        
        left = o1["l"]
        obj.location = o2.location if left else o1.location
        obj.location.z = self.floorToWindow
        
        addBooleanModifier(wall.mesh, o2["g"], self.envelope)
        
        rz = obj.driver_add("rotation_euler", 2)
        addTransformsVariable(rz, "x1", o2 if left else o1, "LOC_X")
        addTransformsVariable(rz, "x2", o1 if left else o2, "LOC_X")
        addTransformsVariable(rz, "y1", o2 if left else o1, "LOC_Y")
        addTransformsVariable(rz, "y2", o1 if left else o2, "LOC_Y")
        rz.driver.expression = "atan2(y2-y1,x2-x1)"
        
        self.keepRatioCenter(o1, o2)
        
    
    def lookup(self):
        lookups = {
            'env': 'envelope',
            'width': 'width'
        }
        numLookups = len(lookups)
        for o in self.obj.children:
            if "t" in o and o["t"] in lookups:
                setattr(self, lookups[o["t"]], o)
                numLookups -= 1
                if not numLookups:
                    # everything is found
                    break
    
    def keepRatioCenter(self, o1, o2):
        # the current ratio is 0.5
        k = 0.5
        sign1 = "+" if o1["l"] else "-"
        sign2 = "-" if o1["l"] else "+"
        
        x = self.obj.driver_add("location", 0)
        addTransformsVariable(x, "x1", o1, "LOC_X")
        addTransformsVariable(x, "x2", o2, "LOC_X")
        addTransformsVariable(x, "y1", o1, "LOC_Y")
        addTransformsVariable(x, "y2", o2, "LOC_Y")
        addLocDiffVariable(x, "d", o1, o2)
        # the width of the window
        addTransformsVariable(x, "wi", self.width, "LOC_X")
        # the width of the wall
        addSinglePropVariable(x, "wa", o2, "[\"w\"]")
        x.driver.expression = "x1+(x2-x1)*("+str(k)+sign1+"wi/2/d)"+sign1+"(y2-y1)*wa/2/d"
        
        y = self.obj.driver_add("location", 1)
        addTransformsVariable(y, "y1", o1, "LOC_Y")
        addTransformsVariable(y, "y2", o2, "LOC_Y")
        addTransformsVariable(y, "x1", o1, "LOC_X")
        addTransformsVariable(y, "x2", o2, "LOC_X")
        addLocDiffVariable(y, "d", o1, o2)
        # the width of the window
        addTransformsVariable(y, "wi", self.width, "LOC_X")
        # the width of the wall
        addSinglePropVariable(y, "wa", o2, "[\"w\"]")
        y.driver.expression = "y1+(y2-y1)*("+str(k)+sign1+"wi/2/d)"+sign2+"(x2-x1)*wa/2/d"