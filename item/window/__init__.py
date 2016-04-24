import bpy, bmesh
from base import pContext
from item.opening import Opening
from util.blender import createMeshObject, getBmesh, setBmesh, parent_set


class GuiWindow:
    
    def draw(self, context, layout):
        layout.label("A window")


class Window(Opening):

    type = "window"
    
    name = "Window"
    
    floorToWindow = 0.75
    
    allowZ = True
    
    def make(self, t):
        verts = t.bm.verts
        context = self.context
        # parent for the whole hierarchy of window Blender objects
        p = t.p
        # template Blender object
        _o = t.o
        # start a Blender object for the template, its name doesn't have the <T_> prefix
        o = createMeshObject(_o.name[2:], _o.location)
        context.scene.update()
        parent_set(p, o)
        context.scene.update()
        context.scene.objects.active = o
        # iterate through the vertices of the template Blender object
        for v in verts:
            # id of the vertex
            vid = str(v[t.layer])
            if not (vid in _o and _o[vid] in bpy.data.objects):
                continue
            # Blender object for the junction at the vertex
            j = bpy.data.objects[_o[vid]]
            t.setJunction(v, j, o, context)
        t.bridgeJunctions(o)


pContext.register(Window, GuiWindow)