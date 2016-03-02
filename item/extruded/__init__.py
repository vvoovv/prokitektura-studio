from base.item import Item
from util.blender import createMeshObject, getBmesh, parent_set
from util.inset import Corner

class Extruded(Item):
    
    def __init__(self, context, op):
        super().__init__(context, op)
    
    def create(self, controls, parent, profile):
        context = self.context
        obj = createMeshObject("extruded")
        obj["t"] = "extruded"
        
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        numControls = len(controls)
        for i in range(numControls):
            corner = Corner(controls[i].location, controls[i-1].location, controls[(i+1)%numControls].location)
            # we store the vertex created in the previous cycle in <_v> variable
            _v = None
            for p in profile:
                v = bm.verts.new(corner.inset(p[0], p[2]))
                if _v:
                    bm.edges.new((_v, v))
                _v = v

        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        self.context.scene.update()
        # perform parenting
        parent_set(parent, obj)
        # one more update
        context.scene.update()