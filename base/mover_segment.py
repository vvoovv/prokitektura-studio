import math
import bpy

from mathutils.geometry import intersect_line_line

from item.wall import addTransformsVariable, addSegmentDrivers, addAttachedDrivers


def addMoverDrivers(e, o, p):
    """
    Add drivers
    
    Args:
        e: A slave, a corner EMPTY that is a direct neighbor of <o>
        o: Segment EMPTY
        p: Intersection point of wall segments that are neighbors of the wall segment defined by <o>
    """
    
    # inital vector connecting <p> and <o>
    m0 = o.location - p
    # initial vector connecting <p> and <e> divided by m0.length_squared
    v0 = (e.location - p)/m0.length_squared
    
    # x
    x = e.driver_add("location", 0)
    addTransformsVariable(x, "ox", o, "LOC_X")
    addTransformsVariable(x, "oy", o, "LOC_Y")
    # p.x +(m0.x*(ox-p.x)+m0.y*(oy-p.y))*v0.x
    x.driver.expression = str(p.x) + "+("+str(m0.x)+"*(ox-"+str(p.x)+")+"+str(m0.y)+"*(oy-"+str(p.y)+"))*"+str(v0.x)
    # y
    y = e.driver_add("location", 1)
    addTransformsVariable(y, "ox", o, "LOC_X")
    addTransformsVariable(y, "oy", o, "LOC_Y")
    # p.y +(m0.x*(ox-p.x)+m0.y*(oy-p.y))*v0.y
    y.driver.expression = str(p.y) + "+("+str(m0.x)+"*(ox-"+str(p.x)+")+"+str(m0.y)+"*(oy-"+str(p.y)+"))*"+str(v0.y)


class AttachedSegmentMover:
    """
    Used only for creation of the initial segment of an attached wall
    """
    
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


class SegmentMover:
    
    def __init__(self, wall, o):
        self.o = o
        # get neighbor EMPTYs for <o>
        o2 = wall.getCornerEmpty(o)
        self.o2 = o2
        o1 = wall.getPrevious(o2)
        self.o1 = o1
        
        context = wall.context
        # temporarily remove drivers for the segment EMPTY object
        o.driver_remove("location")
        
        # get neighbor EMPTYs for <o1> and <o2>
        e1 = wall.getPrevious(o1)
        e2 = wall.getNext(o2)
        # vectors
        if e1:
            v1 = o1.location - e1.location
        if e2:
            v2 = e2.location - o2.location
        
        if e1 and e2:
            # point where the line defined by v1 and v2 intersect
            p = intersect_line_line(e1.location, o1.location, o2.location, e2.location)[0]
            # orient <o> along the line defined by <o> and <p>
            dy, dx = o.location.y-p.y, o.location.x-p.x
        elif e1 or e2:
            _v = v1 if v1 else v2
            # orient <o> along <_v>
            dy, dx = _v.y, _v.x
        else:
            # orient <o> along the normal to the wall segment defined by <o>
            dy, dx = o1.location.x-o2.location.x, o2.location.y-o1.location.y
        
        o.rotation_euler[2] = math.atan2(dy, dx)
        context.scene.update()
        # adding drivers for o1 and o2
        addMoverDrivers(o1, o, p)
        addMoverDrivers(o2, o, p)
        
        o.select = True
        context.scene.objects.active = o
    
    def start(self):
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def end(self):
        o = self.o
        o.rotation_euler[2] = 0.
        # delete drivers for the corner EMPTY objects self.o1 and self.o2
        self.o1.driver_remove("location")
        self.o2.driver_remove("location")
        addSegmentDrivers(o, self.o1, self.o2)