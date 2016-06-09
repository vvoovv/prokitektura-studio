import bpy, bmesh
from base import pContext
from item.opening import Opening
from util.blender import createMeshObject, createEmptyObject, getBmesh, setBmesh, parent_set, addEdgeSplitModifier


class GuiWindow:
    
    def draw(self, context, layout):
        layout.label("A window")


class Window(Opening):

    type = "window"
    
    name = "Window"
    
    floorToWindow = 0.75
    
    allowZ = True
    
    def make(self, t, **kwargs):
        verts = t.bm.verts
        context = self.context
        # template Blender object
        _o = t.o
        # Create a Blender EMPTY object to serve as a parent for the window mesh;
        # its name doesn't have <T_> prefix
        name = _o.name[2:]
        # <pt> stands for parent template
        pt = t.parentTemplate
        if pt:
            p = createEmptyObject(name, _o.location-pt.o.location, False, empty_draw_type='PLAIN_AXES', empty_draw_size=0.01)
        else:
            # parent for the whole hierarchy of window Blender objects
            p = t.p
        t.meshParent = p
        # start a Blender object for the template
        o = createMeshObject(name + "_mesh")
        context.scene.update()
        # perform parenting
        parent_set(p, o)
        if t.parentTemplate:
            parent_set(pt.meshParent, p)
        context.scene.update()
        context.scene.objects.active = o
        
        t.prepareOffsets()
        
        # iterate through the vertices of the template Blender object
        numVerts = 0
        for v in verts:
            # id of the vertex
            vid = t.getVid(v)
            if not (vid in _o and _o[vid] in bpy.data.objects):
                continue
            # Blender object for the node at the vertex
            j = bpy.data.objects[_o[vid]]
            t.setNode(v, j, o, context)
            numVerts += 1
        if numVerts == len(verts):
            bm = getBmesh(o)
            t.bridgeNodes(o, bm)
            t.makeSurfaces(o, bm)
            setBmesh(o, bm)
            
            # apply Edge Split modifier
            if kwargs["addEdgeSplitModifier"]:
                addEdgeSplitModifier(o, o.name, use_edge_angle=False)
            
            # hide the template Blender object
            t.o.hide = True


pContext.register(Window, GuiWindow)