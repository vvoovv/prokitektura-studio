import math
import bpy
from base import zero2, yAxis
from util.blender import getBmesh


def is90degrees(cos):
    return abs(cos) < zero2


def is180degrees(cos):
    return abs(-1-cos) < zero2


class Junction:
    
    def __init__(self, v, baseEdge):
        self.v = v
        self.baseEdge = baseEdge
    
    def validate(self, o):
        """
        The method checks if the Blender object <o> is valid as a junction and
        assigns the junction edges for the Blender object <o>
        """
        # calculate the number of "edges" defined by vertex groups with the name starting from <e_>
        numEdges = 0
        groupIndices = set()
        for g in o.vertex_groups:
            if g.name[:2] == "e_":
                numEdges += 1
                groupIndices.add(g.index)
        if not len(self.v.link_edges) == numEdges:
            return False
        
        # store edges for the Blender object <o>
        self._edges = self.getEdges(o, groupIndices)
        return True
    
    def getEdges(self, o, groupIndices):
        """
        Get vectors that define junction edges for the Blender object <o>
        
        Args:
            o: Blender object acting as a junction
            groupIndices (list): A list of vertex group indices, each vertex group is assigned to vertices
            forming an open end of the junction edge
        """
        edges = []
        bm = getBmesh(o)
        layer = bm.verts.layers.deform[0]
        # Iterate through vertices
        for v in bm.verts:
            edge = None
            for i in groupIndices:
                if i in v[layer]:
                    # now find the vertex that doesn't have the group with the index <i>
                    loop = v.link_loops[0]
                    _v = (loop.link_loop_prev if i in loop.link_loop_next.vert[layer] else loop.link_loop_next).vert
                    edge = (v.co - _v.co).normalized()
                    edges.append(edge)
                    # we found the vertex belonging to the group with the index <i>,
                    # we don't need to continue iteration through groupIndices
                    break
            if edge:
                # we'll skip the other vertices belonging to the group with the index <i>
                groupIndices.remove(i)
            if not groupIndices:
                # nothing is left to search for
                break
        bm.free()
        return edges
    
    def prepare(self, o):
        """
        Prepare the Blender object <o> as a junction, e.g. rotate and shear it appropriately
        """
        self.updateVertexGroupNames()
        # calculate rotation angle
        dot = self.baseEdge.dot(self._baseEdge)
        # check if <self.baseEdge> and <self._baseEdge> are already aligned
        if abs(1-dot) > zero2:
            angle = math.acos(dot)
            if yAxis.dot( self._baseEdge.cross(self.baseEdge) ) < 0.:
                angle = -angle
            bpy.ops.transform.rotate(value = angle, axis=yAxis)
    
    def updateVertexGroupNames(self):
        pass


class LJunction(Junction):
    
    def __init__(self, v, edges):
        # take the first edge as the base one
        super().__init__(v, edges[0])
        # store the dot product to process Blender object later
        self.cross = edges[0].cross(edges[1])
    
    def validate(self, o):
        if not super().validate(o):
            return False
        # store the base edge for the Blender object <o> using the cross product of the edges
        edges = self._edges
        cross = edges[0].cross(edges[1])
        self._baseEdge = edges[0] if self.cross.dot(cross) > 0 else edges[1]
        return True


class TJunction(Junction):
    
    def validate(self, o):
        if not super().validate(o):
            return False
        middleEdge = TJunction.getMiddleEdge(self._edges)
        if not middleEdge:
            return False
        # store the middle edge for the Blender object <o>
        self._baseEdge = middleEdge
        return True
    
    @staticmethod
    def getMiddleEdge(edges):
        # index of the middle part of the junction if it's of T-type
        middleIndex = -1
        cos01 = edges[0].dot(edges[1])
        cos02 = edges[0].dot(edges[2])
        if is90degrees(cos01):
            if is90degrees(cos02):
                middleIndex = 0
            elif is180degrees(cos02):
                middleIndex = 1
        elif is90degrees(cos02):
            if is90degrees(cos01):
                middleIndex = 0
            elif is180degrees(cos01):
                middleIndex = 2
        return edges[middleIndex] if middleIndex >=0 else None


class YJunction(Junction):
    pass


class XJunction(Junction):
    pass


class KJunction(Junction):
    pass