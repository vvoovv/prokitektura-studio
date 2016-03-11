import bpy, bmesh
from base.item import Item
from base import zAxis, getLevelHeight, getNextLevelParent
from util.blender import createMeshObject, getBmesh, assignGroupToVerts, addHookModifier, parent_set


class FinFlat(Item):
    
    def createFromArea(self, area):
        context = self.context
        controls = area.getControls()
        
        obj = createMeshObject(area.obj.name+"_finish")
        obj["t"] = "fin"
        
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        # a vector along z-axis with the length equal to the wall height
        height = getLevelHeight(context, area.obj)*zAxis
        numControls = len(controls)
        for c in controls:
            group = c["g"]
            # the vert at the bottom
            v_b = bm.verts.new(c.location)
            # the vert at the top
            v_t = bm.verts.new(c.location+height)
            assignGroupToVerts(obj, layer, group, v_b, v_t)
            # assign vertex group for the top vertex
            assignGroupToVerts(obj, layer, "t", v_t)
        
        # create faces
        bm.verts.ensure_lookup_table()
        v1_b = bm.verts[-2]
        v1_t = bm.verts[-1]
        for i in range(numControls):
            # <2> is the number of vertices (of the just created wall surface) per control point
            v2_b = bm.verts[i*2]
            v2_t = bm.verts[i*2+1]
            bm.faces.new((v1_b, v1_t, v2_t, v2_b))
            v1_b = v2_b
            v1_t = v2_t
        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        # perform parenting
        parent_set(area.obj.parent, obj)
        # one more update
        context.scene.update()
        
        # add HOOK modifiers
        for c in controls:
            group = c["g"]
            addHookModifier(obj, group, c, group)
        # add a HOOK modifier controlling the top vertices
        addHookModifier(obj, "t", getNextLevelParent(context, obj), "t")
    
    def assignUv(self):
        pass