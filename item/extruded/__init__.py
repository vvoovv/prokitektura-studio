from base.item import Item
from util.blender import createMeshObject, getBmesh, parent_set, assignGroupToVerts, addHookModifier
from util.inset import Corner

class Extruded(Item):
    
    def __init__(self, context, op):
        super().__init__(context, op)
    
    def create(self, controls, parent, profile):
        context = self.context
        
        profile, closed, clockwise = self.getProfileData(profile)
        
        obj = createMeshObject("extruded")
        obj["t"] = "extruded"
        
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        numVerts = len(profile)
        numControls = len(controls)
        for i in range(numControls):
            c = controls[i]
            corner = Corner(c.location, pVert = controls[i-1].location, nVert = controls[(i+1)%numControls].location)
            group = c["g"]
            for p in profile:
                v = bm.verts.new(corner.inset(p[0], p[1]))
                assignGroupToVerts(obj, layer, group, v)
        
        # create faces
        bm.verts.ensure_lookup_table()
        for i in range(numControls):
            offset1 = (i-1)*numVerts
            offset2 = offset1+numVerts
            v1_1 = bm.verts[offset1]
            v2_1 = bm.verts[offset2]
            for p in range(1, numVerts):
                v1_2 = bm.verts[offset1+p]
                v2_2 = bm.verts[offset2+p]
                bm.faces.new((v2_2, v1_2, v1_1, v2_1) if clockwise else (v2_2, v2_1, v1_1, v1_2))
                v1_1 = v1_2
                v2_1 = v2_2
            if closed:
                v1_2 = bm.verts[offset1]
                v2_2 = bm.verts[offset2]
                bm.faces.new((v2_2, v1_2, v1_1, v2_1) if clockwise else (v2_2, v2_1, v1_1, v1_2))
        
        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        # perform parenting
        parent_set(parent, obj)
        # one more update
        context.scene.update()
        
        # add hook modifiers
        for c in controls:
            group = c["g"]
            addHookModifier(obj, group, c, group)

    def getProfileData(self, profile):
        coords = []
        
        bm = getBmesh(profile)
        bm.verts.ensure_lookup_table()
        
        # is profile a closed loop?
        closed = True if len(bm.verts)==len(bm.edges) else False
        start = bm.verts[0]
        # keep the edge visited in the previous pass of the cycle in the following variable
        e = start.link_edges[0]
        if not closed:
            # find an either open end of the profile
            while len(start.link_edges)!=1:
                e = start.link_edges[0] if start.link_edges[1] == e else start.link_edges[1]
                start = e.verts[0] if e.verts[1]==start else e.verts[1]
                
        vert = start
        # keep the edge visited in the previous pass of the cycle in the following variable
        e = vert.link_edges[0]
        while True:
            p = vert.co
            coords.append((p.x, p.z))
            if not closed and len(vert.link_edges) == 1 and vert != start:
                break
            vert = e.verts[0] if e.verts[1]==vert else e.verts[1]
            if closed and vert == start:
                break
            e = vert.link_edges[-1] if vert.link_edges[0] == e else vert.link_edges[0]
        
        bm.free()
        
        # Now determine if the coords are in the clockwise or counterclockwise order.
        # See http://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
        # The method is based on the shoelace formula
        _sum = 0.
        # store the coordinates of the previous point in the following variable
        _c = None
        for c in coords:
            if not _c:
                _c = coords[-1]
            _sum += (c[0]-_c[0])*(c[1]+_c[1])
            _c = c
        clockwise = True if _sum>0 else False
        
        return coords, closed, clockwise