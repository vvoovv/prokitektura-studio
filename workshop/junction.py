import math
import bpy
from base import zero2
from util.blender import getBmesh, setVertexGroupName


def is90degrees(cos):
    return abs(cos) < zero2


def is180degrees(cos):
    return abs(cos+1) < zero2


class Junction:
    
    def __init__(self, v, edges):
        self.valid = True
        self.v = v
        # normal to the vertex
        self.n = v.normal
        self.edges = self.arrangeEdges(edges)
    
    def setBlenderObject(self, o):
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
            return None
        
        # store edges for the Blender object <o>
        self._edges = self.arrangeEdges( self.getEdges(o, groupIndices) )
        return self._edges
    
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
                    # store also the group index
                    edges.append([ edge, i ])
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
    
    def arrangeEdges(self, edges):
        """
        Arrange input <edges> in the following way.
        
        The edge with the index zero is always the base edge.
        The other edges are arranged in the counterclockwise order starting from the base edge.
        
        Returns:
        A tuple of arranged edges
        """
        from operator import itemgetter
        # Add two extra elements to each entry of <edges> to perform one-line sorting
        # So the forth element with the index 3 is cosine of the angle between the edge and the base edge
        # The third element with the index 2 indicates in which circle half the edge is located:
        # True: the edge is located in the first circle half going counterclockwise from the base edge
        # False: the edge is located in the second circle half going counterclockwise from the base edge
        baseEdgeIndex = self.baseEdgeIndex
        baseVec = edges[baseEdgeIndex][0]
        for i,e in enumerate(edges):
            e.append(True)
            if i == baseEdgeIndex:
                # ensure that the base edge will be the first one after sorting of <edges>
                e.append(1.)
            else:
                cos = baseVec.dot(e[0])
                # check if the angle between the edge and the base edge is 180 degrees
                if is180degrees(cos):
                    e.append(-1.)
                else:
                    if self.n.dot( baseVec.cross(e[0])) < 0.:
                        e[2] = False
                    e.append(cos)
        edges.sort(key=itemgetter(2,3), reverse=True)
        return edges
    
    def transform(self, o):
        """
        Transform the Blender object <o> as a junction, e.g. rotate and shear it appropriately
        """
        # calculate rotation angle
        # remember, the base edge has the index zero in the tuple
        baseEdge = self.edges[0][0]
        _baseEdge = self._edges[0][0]
        dot = baseEdge.dot(_baseEdge)
        # check if <baseEdge> and <_baseEdge> are already aligned
        if abs(1-dot) > zero2:
            angle = math.acos(dot)
            if self.n.dot( _baseEdge.cross(baseEdge) ) < 0.:
                angle = -angle
            bpy.ops.transform.rotate(value = angle, axis=self.n)
    
    def updateVertexGroupNames(self, o, template):
        # update the names of the vertex groups that define the ends of the junction <o>
        for i in range(len(self.edges)):
            _vid = template.getVid(self.edges[i][1])
            # vertices with vids <self.vid> and <_vid> define an edge
            setVertexGroupName(o, self._edges[i][1], self.vid + "_" + _vid)
        # update the names of vertex groups that define a surface
        for i,g in enumerate(o.vertex_groups):
            if g.name[0] == "s":
                # append <self.vid>
                g.name += "_" + self.vid
            


class LJunction(Junction):
    
    def __init__(self, v, edges):
        super().__init__(v, edges)
        # store the dot product to process Blender object later
        self.cross = edges[0][0].cross(edges[1][0])
    
    def arrangeEdges(self, edges):
        cross = edges[0][0].cross(edges[1][0])
        # check if <cross> and the normal <self.n> point in the same direction
        baseEdgeIndex = 0 if self.n.dot(cross) > 0. else 1
        return (edges[baseEdgeIndex], edges[1-baseEdgeIndex])


class TJunction(Junction):
    
    def arrangeEdges(self, edges):
        # index of the middle part of the junction if it's of T-type
        middleIndex = -1
        cos01 = edges[0][0].dot(edges[1][0])
        cos02 = edges[0][0].dot(edges[2][0])
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
        if middleIndex < 0:
            return None
        self.baseEdgeIndex = middleIndex
        return super().arrangeEdges(edges)


class YJunction(Junction):
    pass


class XJunction(Junction):
    pass


class KJunction(Junction):
    pass