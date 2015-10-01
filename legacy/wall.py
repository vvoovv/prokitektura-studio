
class Wall:
    
    def inset0(self, location, w1, w2, n2, vec1, vec2):
        zero = 0.000001
        # cross product between edge1 and edge1
        cross = vec1.cross(vec2)
        # To check if have a concave (>180) or convex angle (<180) between edge1 and edge2
        # we calculate dot product between cross and axis
        # If the dot product is positive, we have a convex angle (<180), otherwise concave (>180)
        dot = cross.dot(zAxis)
        convex = True if dot>0 else False
        # sine of the angle between -self.edge1.vec and self.edge2.vec
        sin = cross.length
        isLine = True if sin<zero and convex else False
        if not isLine:
            #sin = sin if convex else -sin
            # cosine of the angle between -self.edge1.vec and self.edge2.vec
            cos = -(vec1.dot(vec2))
        
        return location + w2*n2 + (w1+w2*cos)/sin*vec2

    def inset(self, location, w1, w2, p0, p1, p2):
        import math
        zero = 0.000001
        x0 = p0.x
        y0 = p0.y
        
        x1 = p1.x
        y1 = p1.y
        
        x2 = p2.x
        y2 = p2.y
        
        d1 = math.sqrt((x1-x0)*(x1-x0)+(y1-y0)*(y1-y0))
        d2 = math.sqrt((x2-x1)*(x2-x1)+(y2-y1)*(y2-y1))
        
        # cross product between edge1 and edge1
        #cross = vec1.cross(vec2)
        cross = ((x1-x0)*(y2-y1) - (y1-y0)*(x2-x1)) / (d1*d2)
        n2x = (y2-y1)/d2
        n2y = (x1-x2)/d2
        # To check if have a concave (>180) or convex angle (<180) between edge1 and edge2
        # we calculate dot product between cross and axis
        # If the dot product is positive, we have a convex angle (<180), otherwise concave (>180)
        #dot = cross.dot(zAxis)
        #convex = True if dot>0 else False
        # sine of the angle between -self.edge1.vec and self.edge2.vec
        sin = -cross
        #isLine = True if sin<zero and convex else False
        #if not isLine:
            #sin = sin if convex else -sin
            # cosine of the angle between -self.edge1.vec and self.edge2.vec
            #cos = -(vec1.dot(vec2))
        cos = -((x1-x0)*(x2-x1)+(y1-y0)*(y2-y1))
        
        return (
            location.x + w2*(y2-y1)/d2 - (w1-w2*((x1-x0)*(x2-x1)+(y1-y0)*(y2-y1))) *(x2-x1) / ((x1-x0)*(y2-y1) - (y1-y0)*(x2-x1)) * d1,
            location.y + w2*(x1-x2)/d2 - (w1-w2*((x1-x0)*(x2-x1)+(y1-y0)*(y2-y1))) *(y2-y1) / ((x1-x0)*(y2-y1) - (y1-y0)*(x2-x1)) * d1,
            location.z
        )
        
    def startAdjoiningWall(self, o, locEnd):
        o = self.getCornerEmpty(o)
        
        locEnd.z = 0.
        # convert the end location to the coordinate system of the wall
        locEnd = self.parent.matrix_world.inverted() * locEnd
        vec = self.getPrevious(o).location
        # Will the adjoining wall be located on the left side (True) or on the right one (False)
        # relative to the original wall segment? This is defined by relative position
        left = True if (o.location - vec).cross(locEnd - vec)[2]>=0 else False
        
        context = self.context
        prk = context.window_manager.prk
        atRight = prk.wallAtRight
        w = prk.newWallWidth
        _w = w
        
        mesh = self.mesh
        counter = mesh["counter"] + 1
        group = str(counter)
        bm = getBmesh(mesh)
        layer = bm.verts.layers.deform[0]
        prefix = "l" if o["l"] else "r"
        
        prev = self.getPrevious(o)["g"]
        
        v1 = self.getVertsForVertexGroup(bm, prefix+o["g"])
        _v1 = self.getVertsForVertexGroup(bm, prefix+prev)
        # verts for the opposite side of the wall
        _o = self.getNeighbor(o)
        prefix = "l" if _o["l"] else "r"
        v2 = self.getVertsForVertexGroup(bm, prefix+_o["g"])
        _v2 = self.getVertsForVertexGroup(bm, prefix+prev)
        bmesh.ops.delete(
            bm,
            geom=(
                getFaceFortVerts(_v1, v1),
                getFaceFortVerts(_v2, v2),
                getFaceFortVerts( (v1[0], v2[0]), (_v1[0], _v2[0]) ),
                getFaceFortVerts( (v1[1], v2[1]), (_v1[1], _v2[1]) )
            ),
            context=5
        )
        # create the loop cuts for the adjoining wall
        # position the adjoining wall at the middle of the wall segment
        w = w*(v1[0].co-_v1[0].co).normalized()
        l1 = 0.5*(v1[0].co-_v1[0].co) - 0.5*w
        
        _u1 = (
            bm.verts.new(_v1[0].co + l1),
            bm.verts.new(_v1[1].co + l1)
        )
        u1 = (
            bm.verts.new(_v1[0].co + l1 + w),
            bm.verts.new(_v1[1].co + l1 + w)
        )
        #assignGroupToVerts(mesh, layer, group, _u1[0], _u1[1], u1[0], u1[1])
        
        # perpendicular to the wall segment with the length equal to the width of the wall segment
        n = o["w"]*l1.cross(zAxis).normalized()
        if not o["l"]:
            n = -n
        
        l2 = _v1[0].co - _v2[0].co + l1 + n
        _u2 = (
            bm.verts.new(_v2[0].co + l2),
            bm.verts.new(_v2[1].co + l2)
        )
        u2 = (
            bm.verts.new(_v2[0].co + l2 + w),
            bm.verts.new(_v2[1].co + l2 + w)
        )
        assignGroupToVerts(mesh, layer, group, _u1[0], _u1[1], u1[0], u1[1], _u2[0], _u2[1], u2[0], u2[1])
        
        # left
        bm.faces.new((_v1[0], _v1[1], _u1[1], _u1[0]))
        if not left:
            bm.faces.new((_u1[0], _u1[1], u1[1], u1[0]))
        bm.faces.new((u1[0], u1[1], v1[1], v1[0]))
        # right
        bm.faces.new((_u2[0], _u2[1], _v2[1], _v2[0]))
        if left:
            bm.faces.new((u2[0], u2[1], _u2[1], _u2[0]))
        bm.faces.new((v2[0], v2[1], u2[1], u2[0]))
        # top
        bm.faces.new((_v2[1], _u2[1], _u1[1], _v1[1]))
        bm.faces.new((_u2[1], u2[1], u1[1], _u1[1]))
        bm.faces.new((u2[1], v2[1], v1[1], u1[1]))
        # bottom
        bm.faces.new((_v1[0], _u1[0], _u2[0], _v2[0]))
        bm.faces.new((_u1[0], u1[0], u2[0], _u2[0]))
        bm.faces.new((u1[0], v1[0], v2[0], u2[0]))
        
        condition = (left and atRight) or (not left and not atRight)
        loc1 = (_u1 if condition else u1)[0].co
        loc2 = (_u2 if condition else u2)[0].co
        
        mesh["counter"] = counter
        # apply changes to bmesh
        bm.to_mesh(self.mesh.data)
        bm.free()
        
        condition = (left and o["l"]) or (not left and not o["l"])
        e1 = self.createAdjoiningEmptyObject(("l" if o["l"] else "r") + group, loc1, False if condition else True)
        setCustomAttributes(e1, l=1 if atRight else 0, g=group, w=_w, p=prev, n=o["g"])
        
        e2 = self.createAdjoiningEmptyObject(("r" if o["l"] else "l") + group, loc2, False if not condition else True)
        setCustomAttributes(e2, l=1 if atRight else 0, g=group, w=_w, p=prev, n=o["g"])
        
        context.scene.update()
        
        parent_set((e1, e2), self.parent)
        
        context.scene.update()
        
        active = e1 if condition else e2
        
        # add hook modifiers
        addHookModifier(mesh, group, active, group)
                
        # delete the related segment EMPTYs
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.parent.children:
            if obj.type == "EMPTY" and "t" in obj and obj["t"]=="ws" and obj["g"] == o["g"]:
                hide_select(obj, True)
                obj.select = True
        bpy.ops.object.delete()
        
        return active
    