import math
import bpy


class Mover:
    
    def __init__(self, context, wall, o):
        self.context = context
        self.wall = wall
        self.o = o
        o.select = True
        context.scene.objects.active = o
        p = wall.getPrevious(o)
        n = wall.getNext(o)
        # temporarily deactivate the related HOOK modifier
        #m = wall.mesh.modifiers[("l" if o["l"] else "r") + o["g"]]
        m = wall.mesh.modifiers[o["g"]]
        obj = m.object
        m.object = None
        o.rotation_euler[2] = math.atan2(n.location.y-p.location.y, n.location.x-p.location.x)
        context.scene.update()
        # activate the related modifier again
        m.object = obj
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def start(self):
        pass