from base import zAxis, zero

class Corner:
    
    def __init__(self, vert, pVert, nVert, axis=None):
        # pVert is the previous vertex for <vert>
        # nVert is the next vertex for <vert>
        if not axis:
            axis = zAxis
        self.vert = vert
        vec1 = vert - pVert
        vec1.normalize()
        vec2 = nVert - vert
        vec2.normalize()
        # cross product between edge1 and edge1
        cross = vec1.cross(vec2)
        # To check if have a concave (>180) or convex angle (<180) between edge1 and edge2
        # we calculate dot product between cross and axis
        # If the dot product is positive, we have a convex angle (<180), otherwise concave (>180)
        dot = cross.dot(axis)
        self.convex = True if dot>0 else False
        # sine of the angle between -self.edge1.vec and self.edge2.vec
        sin = cross.length
        self.isLine = True if sin<zero and self.convex else False
        if not self.isLine:
            if not self.convex:
                sin = -sin
            # normal to <vec1>
            normal = vec1.cross(axis)
            normal.normalize()
            # cosine of the angle between -vec2 and vec2
            cos = -(vec1.dot(vec2))
            self.multiplier = normal + (1.+cos)/sin*vec1
    
    def inset(self, dx, dz):
        return self.vert - dx*self.multiplier + dz*zAxis