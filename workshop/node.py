import math
import bpy, bmesh, mathutils
from base import zero2, zeroVector
from util import acos, is90degrees, is180degrees
from util.blender import getBmesh, setBmesh, getVertsForVertexGroup


# value of the shape key offset for the shape key value equal to 1.
shapeKeyOffset = 0.05 # 5cm

# the base bisector is needed for the correct operation of the shear transformation in LNode.shear(..)
baseBisector = mathutils.Vector((1., 0., 1.)).normalized()


class Node:
    """
    self.edges (list): An ordered list of entries for edges of the template vertex.
        The list starts from the entry for the base edge. Each entry of the list is
        a list itself with 4 entries:
        (0) Unit vector along the edge the starts at the template vertex
        (1) Opposite vertex (BMVert) of the edge
        (2) Boolean variable that defines in which circle half the edge is located (not available for LNode)
        (3) Cosine of the angle between the edge and the base edge (not available for LNode)
    """
    
    def __init__(self, v, edges):
        self.valid = True
        self.v = v
        # normal to the vertex
        self.n = v.normal
        self.edges = self.arrangeEdges(edges)
    
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
            angle = acos(dot)
            if self.n.dot( _baseEdge.cross(baseEdge) ) < 0.:
                angle = -angle
            bpy.ops.transform.rotate(value = angle, axis=self.n)
            matrix = mathutils.Matrix.Rotation(angle, 4, self.n)
        
        angle = self.rotate(o)
        
        self.shear(o, angle)
        
        # remember the transformation matrix
        self.matrix = matrix
        
        return matrix
    
    def rotate(self, o):
        """
        Rotate a group vertices with the name <i_?> which are located
        at an open end of the Blender object <o> serving as a node for the template vertex <self.v>
        
        Returns:
            float: Angle between edges in radians, if rotation is needed, None otherwise
            In future implementations a tuple of angle can be returned
        """
        pass
    
    def shear(self, o, angle):
        """
        Perform a shear transformation of the central part of the Blender object <o>
        serving as a node for the template vertex <self.v>
        
        The central part to shear is defined by a group of vertices with the name <c>
        
        The variable <angle> is supplied by <self.rotate(..)>. See documentation to <self.rotate(..)>
        for the definition of the <angle>. If <angle> is None, no shear transformation is needed.
        """
        pass
    
    def updateVertexGroupNames(self, o, template):
        # update the names of the vertex groups that define the open ends of the node <o>
        # store the correspondence of the old and new names in the dictionary <ends> 
        ends = {}
        self.ends = ends
        for i in range(len(self.edges)):
            group = o.vertex_groups[ self._edges[i][1] ]
            _vid = template.getVid(self.edges[i][1])
            # vertices with vids <self.vid> and <_vid> define an edge
            ends[group.name] = (self.vid, _vid)
            group.name = "e_" + self.vid + "_" + _vid
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
        
        # treat the special case for only two edges
        if len(edges) == 2:
            e1, e2 = edges
            _cos = baseVec.dot(edges[1][0])
            return e1,e2 if firstCircleHalf and cos < _cos else e2,e1
        
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
    
    def getEdgeIndex(self, edgeVector):
        """
        Get <index> of <self.edges> for which <self.edges[index][0] == edgeVector>.
        <edgeVector> must be normalized!
        """
        for i, e in enumerate(self.edges):
            if abs( 1.-edgeVector.dot(e[0]) ) < zero2:
                return i


class LNode(Node):
    
    def __init__(self, v, edges):
        super().__init__(v, edges)
        # store the dot product to process Blender object later
        self.cross = edges[0][0].cross(edges[1][0])
    
    def arrangeEdges(self, edges):
        # the code is splitted for template edges and edges from a Blender object
        if isinstance(edges[0][1], bmesh.types.BMVert):
            # The main problem for the node with two edges when <edges> represent template edges is
            # that angle can be concave
            # check the order of vertices
            baseEdgeIndex = 1 if self.v.link_loops[0].link_loop_prev.vert == edges[0][1] else 0
            vec1 = edges[baseEdgeIndex][0]
            vec2 = edges[1-baseEdgeIndex][0]
            # cross product between the vectors
            cross = vec1.cross(vec2)
            # To check if have a concave (>180) or convex angle (<180) between <vec1> and <vec2>
            # we calculate dot product between <cross> and the normal <self.n> to the vertex <self.v>
            # If the dot product is positive, we have a convex angle (<180), otherwise concave (>180)
            dot = cross.dot(self.n)
            convex = True if dot>0 else False
        else:
            cross = edges[0][0].cross(edges[1][0])
            # check if <cross> and the normal <self.n> point in the same direction
            baseEdgeIndex = 0 if self.n.dot(cross) > 0. else 1
            # the angle between the edges is always convex in this case
            convex = True
        
        edges = (edges[baseEdgeIndex], edges[1-baseEdgeIndex])
        # add two extra elements to each entry of <edges> as described in <Node.arrangeNodes(..)>
        # the cosine of the angle between the edges will be used in <self.rotate(..)>
        edges[0].extend(( 1., True ))
        edges[1].extend(( edges[0][0].dot(edges[1][0]), convex))
        return edges
    
    def rotate(self, o):
        """
        Realization of <Node.rotate(..)>
        """
        # check if we need to perform rotation
        cos = self.edges[1][2]
        convex = self.edges[1][3]
        if convex and abs(cos) < zero2:
            return
        
        angle = acos(cos)
        
        bm = getBmesh(o)
        bmesh.ops.rotate(
            bm,
            cent = zeroVector,
            matrix = mathutils.Matrix.Rotation(
                angle-math.pi/2. if convex else 1.5*math.pi-angle,
                3,
                self.n
            ),
            verts = getVertsForVertexGroup(o, bm, o.vertex_groups[ self._edges[1][1] ].name)
        )
        setBmesh(o, bm)
        
        return angle
    
    def shear(self, o, angle):
        """
        Realization of <Node.shear(..)>
        """
        if angle is None or not "c" in o.vertex_groups:
            return
        
        _edges = self._edges
        
        convex = self.edges[1][3]
        bm = getBmesh(o)
        shearFactor = 1./math.tan(angle/2.)
        if convex:
            shearFactor = shearFactor - 1.
        else:
            shearFactor = -shearFactor - 1.
        
        # For the share transformation of the central part defined by the vertex group <c>
        # we may have to provide a space matrix, since the parameters of the share transformation are
        # defined under assumtions that the central part defined by the vertex group <c> is oriented
        # along the <baseBisector>. So the <space> matrix defines the rotation that orients
        # the actual bisector along the <baseBisector>
        bisector = (_edges[0][0] + _edges[1][0]).normalized()
        dot = bisector.dot(baseBisector)
        # check if <bisector> and <baseBisector> are already aligned
        if abs(1-dot) > zero2:
            _angle = acos(dot)
            if self.n.dot( bisector.cross(baseBisector) ) < 0.:
                _angle = -_angle
            spaceMatrix = mathutils.Matrix.Rotation(_angle, 4, self.n)
        else:
            spaceMatrix = mathutils.Matrix.Identity(4)
        
        bmesh.ops.transform(
            bm,
            matrix = mathutils.Matrix.Shear('XY', 4, (shearFactor, 0.)),
            verts = getVertsForVertexGroup(o, bm, "c"),
            space = spaceMatrix
        )
        # Set BMesh here to get the correct result in the next section
        # of the code related to the shape key update
        setBmesh(o, bm)
        
        # update shape key data (if available) for the vertices of the vertex group <c>
        shape_keys = o.data.shape_keys
        if shape_keys:
            if shape_keys.key_blocks.get("frame_width", None):
                bm = getBmesh(o)
                
                shapeKey = bm.verts.layers.shape.get("frame_width")
                # the bisector of the edges after the shear transformation
                bisector = mathutils.Matrix.Rotation(
                    angle/2. - math.pi/4. if convex else 0.75*math.pi - angle/2.,
                    3,
                    self.n
                ) * bisector
                # offset vector for the shape key
                offset = shapeKeyOffset / math.sin(angle/2.) * bisector
                for v in getVertsForVertexGroup(o, bm, "c"):
                    # check if the vertex changes its location for the shape key
                    if ( (v[shapeKey] - v.co).length > zero2):
                        v[shapeKey] = v.co + offset
                
                setBmesh(o, bm)


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


class CrossNode(Node):
    
    def arrangeEdges(self, edges):
        self.baseEdgeIndex = 0
        edges = super().arrangeEdges(edges)
        # check if all angle are the right ones
        return edges if abs(edges[1][3])<zero2 and abs(edges[2][3]+1)<zero2 and abs(edges[3][3]<zero2) else None


class XNode(Node):
    pass


class KNode(Node):
    pass