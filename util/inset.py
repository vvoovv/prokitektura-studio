from base import zero, zAxis


class Corner:
    
    def __init__(self, vert, axis=None, **kwargs):
        evenInset = kwargs.get("evenInset", True)
        # The edges can be specified with with
        # 1)
        # pVert is the previous vertex for <vert>
        # nVert is the next vertex for <vert>
        # or with
        # 2)
        # a pair of unit vectors <vec1> and <vec2> originating from <vert>;
        # the cross product between <vec1> and <vec2> must be oriented along <axis>
        if not axis:
            axis = zAxis
        self.vert = vert
        if "pVert" in kwargs:
            vec1 = vert - kwargs["pVert"]
            vec1.normalize()
        else:
            vec1 = -kwargs["vec2"]
        if "nVert" in kwargs:
            vec2 = kwargs["nVert"] - vert
            vec2.normalize()
        else:
            vec2 = kwargs["vec1"]
        # cross product between edge1 and edge2
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
            if evenInset:
                self.multiplier = normal + (1.+cos)/sin*vec1
            else:
                self.vec1 = vec1
                self.sin = sin
                self.cos = cos
                self.normal = normal
    
    def inset(self, *args):
        if len(args)==2:
            dx, dz = args
            inset = self.vert - dx*self.multiplier + dz*zAxis
        else:
            # notice the order of <d1> and <d2>
            d2, d1, dz = args
            inset = self.vert - d1*self.normal - (d2+d1*self.cos)/self.sin*self.vec1
        return inset
    
    def getDriverExpressions(self, x0, z0, w1, w2):
        # exchange the values of <w1> and <w2>
        w1, w2 = w2, w1
        n = self.normal
        vec1 = self.vec1
        d1 = str(w1)+"*fw"
        d2 = str(w2)+"*fw"
        cos = str(self.cos)
        sin = str(self.sin)
        strPart = "-("+d2 + "+" + d1 + "*" +cos + ")/" + sin + "*"
        driverExpressionX = str(x0) + "-" + d1 + "*" + str(n.x) + strPart + str(vec1.x)
        driverExpressionZ = str(z0) + "-" + d1 + "*" + str(n.z) + strPart + str(vec1.z)
        return driverExpressionX, driverExpressionZ