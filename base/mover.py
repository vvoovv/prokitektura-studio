import math
import bpy

from item.wall import addTransformsVariable


def addMoverDrivers(slave, master):
    x = slave.driver_add("location", 0)
    addTransformsVariable(x, "x", master, "LOC_X")
    x.driver.expression = "x+("+str(slave.location.x)+")-("+str(master.location.x)+")"
    y = slave.driver_add("location", 1)
    addTransformsVariable(y, "y", master, "LOC_Y")
    y.driver.expression = "y+("+str(slave.location.y)+")-("+str(master.location.y)+")"


class Mover:
    
    def __init__(self, wall, o, e1, e2):
        context = wall.context
        self.o = o
        bpy.ops.object.select_all(action="DESELECT")
        o.select = True
        context.scene.objects.active = o
        # temporarily remove driver for the segment EMPTY object
        o.driver_remove("location")
        o.rotation_euler[2] = math.atan2(e2.location.y-e1.location.y, e2.location.x-e1.location.x)
        context.scene.update()
        # get neighbor EMPTYs for <o>
        o2 = wall.getCornerEmpty(o)
        o1 = wall.getPrevious(o2)
        # adding drivers for o1 and o2
        addMoverDrivers(o1, o)
        addMoverDrivers(o2, o)
        
        # activate the related modifier again
        #m.object = obj
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def start(self):
        pass