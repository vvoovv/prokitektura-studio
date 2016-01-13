import math
import bpy

from blender_util import createEmptyObject, parent_set
from item.wall import addTransformsVariable, addAttachedDrivers

class Mover:
    """
    A base class for all movers along a line
    """
    
    def setupMaster(self, context, point1, point2):
        o = self.o
        # create a master EMPTY resembling <o>
        master = createEmptyObject("tmp", o.location, empty_draw_type=o.empty_draw_type, empty_draw_size=o.empty_draw_size)
        master.lock_location[2] = True
        self.master = master
        # rotate master along the line defined by point1 and point2
        master.rotation_euler[2] = math.atan2(point2.y-point1.y, point2.x-point1.x)
        parent_set(o.parent, master)
        
        o.select = False
        # make <o> a slave of <master>
        # x
        x = o.driver_add("location", 0)
        addTransformsVariable(x, "x", master, "LOC_X")
        x.driver.expression = "x"
        # y
        y = o.driver_add("location", 1)
        addTransformsVariable(y, "y", master, "LOC_Y")
        y.driver.expression = "y"
        
        master.select = True
        context.scene.objects.active = master
    
    def start(self):
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def end(self):
        o = self.o
        o.driver_remove("location")
        bpy.context.scene.objects.unlink(self.master)
        bpy.data.objects.remove(self.master)
        o.select = True
        bpy.context.scene.objects.active = o


class AlongSegmentMover(Mover):
    
    def __init__(self, wall, o):
        self.o = o
        context = wall.context
        # The line constraining movement of <o> passes through <o> and
        # its previous corner EMPTY or the next corner EMPTY if <o> doesn't have the previous corner EMPTY
        point1 = o.location
        point2 = (wall.getNext(o) if "e" in o and not o["e"] else wall.getPrevious(o)).location
        self.setupMaster(context, point1, point2)


class AttachedMover(Mover):
    
    def __init__(self, wall, o):
        self.o = o
        self.wall = wall
        # get reference EMPTYs for the wall segment to which <o> is attached
        self.e1, self.e2 = wall.getReferencesForAttached(o)
        
        # temporarily remove drivers for the attached EMPTY object
        o.driver_remove("location")
        
        self.setupMaster(wall.context, self.e1.location, self.e2.location)
    
    def end(self):
        super().end()
        o = self.o
        wall = self.wall
        addAttachedDrivers(wall, o, wall.getPrevious(o) if o["e"] else wall.getNext(o), self.e1, self.e2, False)