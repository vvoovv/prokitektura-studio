import math
import bpy

from blender_util import createEmptyObject, parent_set
from item.wall import addTransformsVariable

class AlongLineMover:
    
    def __init__(self, wall, o):
        self.o = o
        context = wall.context
        # consider that the line constraining movement of <o> passes through <o> and its previous corner EMPTY
        point1 = o.location
        point2 = wall.getPrevious(o).location
        
        # create a master EMPTY resembling <o>
        master = createEmptyObject("tmp", o.location, empty_draw_type=o.empty_draw_type, empty_draw_size=o.empty_draw_size)
        self.master = master
        # rotate master along the line defined by point1 and point2
        master.rotation_euler[2] = math.atan2(point2.y-point1.y, point2.x-point1.x)
        parent_set(master, o.parent)
        
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