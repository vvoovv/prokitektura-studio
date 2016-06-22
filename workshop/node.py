import math
import bpy, mathutils
from base import zero2, zeroVector
from util.blender import getBmesh, setVertexGroupName


def is90degrees(cos):
    return abs(cos) < zero2


def is180degrees(cos):
    return abs(cos+1) < zero2


class Node:
    """
    self.edges (list): An ordered list of entries for edges of the template vertex.
        The list starts from the entry for the base edge. Each entry of the list is
        a list itself with 4 entries:
        (0) Unit vector along the edge the starts at the template vertex
        (1) Opposite vertex (BMvert) of the edge
        (2) Boolean variable that defines in which circle half the edge is located (not available for LNode)
        (3) Cosine of the angle between the edge and the base edge (not available for LNode)
    """
    
    def __init__(self, v, edges):
        self.valid = True
        self.v = v
        # normal to the vertex
        self.n = v.normal
        self.edges = self.arrangeEdges(edges)
        
        # Offsets are stored in the order as entries in <self.edges>
        # The corner for an offset is defined by unit vectors from entries
        # with the indices <i> and <i+1> in <self.edges>
        offsets = []
        # Set child offset to zero for correct operation for all pairs of edges
        # sharing the same origin vertex <vid>
        for _ in range(len(edges)):
            offsets.append(zeroVector)
        self.offsets = offsets
    
    def setBlenderObject(self, o):
        """
        The method checks if the Blender object <o> is valid as a node and
        assigns the node edges for the Blender object <o>
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
        Get vectors that define node edges for the Blender object <o>
        
        Args:
            o: Blender object acting as a node
            groupIndices (list): A list of vertex group indices, each vertex group is assigned to vertices
            forming an open end of the node edge
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
                        # negate <cos> to have correct sorting
                        cos = -cos
                    e.append(cos)
        edges.sort(key=itemgetter(2,3), reverse=True)
        # restore the true value of cosine for the second circle half
        for i in range(len(edges)-1, -1, -1):
            if edges[i][2]:
                # reached the first circle half
                break
            else:
                edges[i][3] = -edges[i][3]
        return edges
    
    def transform(self, o):
        """
        Transform the Blender object <o> as a node, e.g. rotate and shear it appropriately
        
        Returns:
        The resulting matrix for the transformation
        """
        matrix = None
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
            matrix = mathutils.Matrix.Rotation(angle, 4, self.n)
        return matrix
    
    def updateVertexGroupNames(self, o, template):
        # update the names of the vertex groups that define the ends of the node <o>
        for i in range(len(self.edges)):
            _vid = template.getVid(self.edges[i][1])
            # vertices with vids <self.vid> and <_vid> define an edge
            setVertexGroupName(o, self._edges[i][1], "e_" + self.vid + "_" + _vid)
        # update the names of vertex groups that define a surface
        for i,g in enumerate(o.vertex_groups):
            if g.name[0] == "s":
                # append <self.vid>
                g.name += "_" + self.vid
    
    def getNeighborEdges(self, vec):
        """
        Returns two neighbor edges from <edges> for the vector <vec>
        
        Args:
            vec (mathutils.Vector): A vector that starts at the template vertex 
        """
        # get the normalized version of <vec>
        vec = vec.normalized()
        edges = self.edges
        # normal to the plane where the template vertex and its <edges> are located
        n = self.v.normal
        
        baseVec = edges[0][0]
        cos = baseVec.dot(vec)
        firstCircleHalf = n.dot( baseVec.cross(vec)) > 0.
        if firstCircleHalf:
            for i in range(len(edges)):
                e1, e2 = edges[i], edges[i+1]
                if e2[3] < cos < e1[3]:
                    return e1, e2
        else:
            e1 = edges[0]
            for i in range(len(edges)-1, -1, -1):
                e2 = e1
                e1 = edges[i]
                # remember <cos> is negated for firstCircleHalf == False
                if e1[3] < cos < e2[3]:
                    return e1, e2
    
    def getEdgeIndex(self, edge):
        # edge ins normalized
        for i, e in enumerate(self.edges):
            if abs( 1.-edge.dot(e) ) < zero2:
                return i


class LNode(Node):
    
    def __init__(self, v, edges):
        super().__init__(v, edges)
        # store the dot product to process Blender object later
        self.cross = edges[0][0].cross(edges[1][0])
    
    def arrangeEdges(self, edges):
        cross = edges[0][0].cross(edges[1][0])
        # check if <cross> and the normal <self.n> point in the same direction
        baseEdgeIndex = 0 if self.n.dot(cross) > 0. else 1
        return (edges[baseEdgeIndex], edges[1-baseEdgeIndex])


class TNode(Node):
    
    def arrangeEdges(self, edges):
        # index of the middle part of the node if it's of T-type
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


class YNode(Node):
    pass


class XNode(Node):
    pass


class KNode(Node):
    pass