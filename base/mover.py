import math
import bpy

from item.wall import addTransformsVariable, addSegmentDrivers, addAttachedDrivers


def addMoverDrivers(slave, master):
    # x
    x = slave.driver_add("location", 0)
    addTransformsVariable(x, "x", master, "LOC_X")
    x.driver.expression = "x+("+str(slave.location.x)+")-("+str(master.location.x)+")"
    # y
    y = slave.driver_add("location", 1)
    addTransformsVariable(y, "y", master, "LOC_Y")
    y.driver.expression = "y+("+str(slave.location.y)+")-("+str(master.location.y)+")"


class Mover:
    
    def __init__(self, wallAttached, o, wallOriginal, e2):
        self.wallAttached = wallAttached
        self.o = o
        # get neighbor EMPTYs for <o>
        o2 = wallAttached.getCornerEmpty(o)
        self.o2 = o2
        o1 = wallAttached.getPrevious(o2)
        self.o1 = o1
        
        # <e2> has to be on the same side as <o1> relative to the original wall segment
        if (e2["l"] and not o1["al"]) or (not e2["l"] and o1["al"]):
            e2 = wallOriginal.getNeighbor(e2)
        
        e1 = wallOriginal.getPrevious(e2)
        self.e1 = e1
        self.e2 = e2
        
        
        context = wallOriginal.context
        bpy.ops.object.select_all(action="DESELECT")
        o.select = True
        context.scene.objects.active = o
        # temporarily remove drivers for the segment EMPTY object
        o.driver_remove("location")
        o.rotation_euler[2] = math.atan2(e2.location.y-e1.location.y, e2.location.x-e1.location.x)
        context.scene.update()
        # adding drivers for o1 and o2
        addMoverDrivers(o1, o)
        addMoverDrivers(o2, o)
    
    def start(self):
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def end(self):
        o = self.o
        o.rotation_euler[2] = 0.
        o.select = False
        # delete drivers for the corner EMPTY objects self.o1 and self.o2
        self.o1.driver_remove("location")
        self.o2.driver_remove("location")
        addSegmentDrivers(o, self.o1, self.o2)
        addAttachedDrivers(self.wallAttached, self.o1, self.o2, self.e1, self.e2)