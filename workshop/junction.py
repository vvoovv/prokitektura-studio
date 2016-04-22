from util.blender import getBmesh


class Junction:
    
    def __init__(self, v):
        self.v = v
    
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
        
        edges = self.getEdges(o, groupIndices)
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
    
    def updateVertexGroupNames(self):
        pass


class LJunction(Junction):
    pass


class TJunction(Junction):
    
    def validate(self, o):
        if not super().validate(o):
            return False
        
        return True


class YJunction(Junction):
    pass


class XJunction(Junction):
    pass


class KJunction(Junction):
    pass