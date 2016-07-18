import mathutils, bpy, bmesh
from base import zero2, zeroVector
from util.blender import createMeshObject, getBmesh, setBmesh, parent_set, assignGroupToVerts, getVertsForVertexGroup
from util.geometry import projectOntoPlane, projectOntoLine, isVectorBetweenVectors


def getEdges(v):
    edges = []
    for e in v.link_edges:
        _v = e.verts[1] if e.verts[0] == v else e.verts[0]
        edges.append([ (_v.co - v.co).normalized(), _v ])
    return edges


def getVectorFromEdge(edge, vert):
    """
    Returns a vector along the <edge> originating at the vertex <vert>
    
    Args:
        edge (BMEdge): An edge
        vert (BMVert): A vertex belonging to the <edge>
    """
    v1, v2 = edge.verts
    if v2 == vert:
        v1, v2 = v2, v1
    return v2.co - v1.co


def getOuterEdgeVector(v):
    """
    Returns a vector along a BMEdge that fulfils the following conditions:
    1) the edge contains the vertex <v>
    2) the edge is an outer one for the template to which the vertex <v> belongs
    3) cross product of the edge vector with the other outer edge vector must point
    in the direction of the normal to the vertex 
    """
    # a variable for the first edge to be found
    _e = None
    # check if the vertex <v> has an outer edge
    for e in v.link_edges:
        if len(e.link_faces) == 1:
            if _e:
                # the second edge is simply <e>
                break
            else:
                # the first edge is found
                _e = e
    if not _e:
        # the vertex doesn't have outer edges
        return None
    
    # for the edges <_e> and <e> get the related vectors <_vec> and <vec> originating from the vertex <v>
    _vec = getVectorFromEdge(_e, v)
    vec = getVectorFromEdge(e, v)
    
    # the cross product of <_vec> and <vec> must point in the direction of the normal to <vert>
    if _vec.cross(vec).dot(v.normal) > 0:
        vec = _vec
    return vec


class SurfaceVerts:
    """
    A data structure to deal with vertices that constitute a surface
    """
    def __init__(self, o, bm, template):
        self.template = template
        self.numVerts = 0
        # sverts stands for surface verts
        self.sverts = {}
        self.scanForVerts(o, bm)
        # the current surface layer, sl stands for surface layer
        self.sl = None
    
    def scanForVerts(self, o, bm):
        """
        Scan for all surface verts
        """
        sverts = self.sverts
        groupIndices = []
        for i,g in enumerate(o.vertex_groups):
            name = g.name
            if name[0] == "s":
                # the name of the vertex group defines a separate surface layer
                # sl stands for surface layer
                sl = name[:name.find("_")]
                sverts[sl] = {}
                groupIndices.append(i)
        if not groupIndices:
            return
        
        layer = bm.verts.layers.deform[0]
        for v in bm.verts:
            for i in groupIndices:
                if i in v[layer]:
                    name = o.vertex_groups[i].name
                    sl = name[:name.find("_")]
                    vid = name[name.find("_")+1:]
                    if not vid in sverts[sl]:
                        sverts[sl][vid] = []
                    sverts[sl][vid].append(v)
                    self.numVerts += 1
    
    def pop(self, tv=None, vec1=None, vec2=None):
        # tv stands for template vertex
        # If <templateVert>, <vec1> and <vec2> are given, that means pop a surface vert for <tv>
        # located between vectors <vec1> and <vec2>
        # If <tv>, <vec1> and <vec2> aren't given, a random surface vertex and its vid are returned
        sverts = self.sverts
        if self.sl is None:
            # set the current surface layer
            self.sl = next(iter(sverts))
        sl = self.sl
        vid = self.template.getVid(tv) if tv else next(iter(sverts[sl]))
        # if the template vertex <tv> is given, it may not have a related surface vertex
        if not vid in sverts[sl]:
            return None, None 
        if len(sverts[sl][vid]) == 1:
            v = sverts[sl][vid][0]
            del sverts[sl][vid]
            if not len(sverts[sl]):
                del sverts[sl]
                # remember the surface layer if a reversion of the surface normal is needed
                self._sl = self.sl
                self.sl = None
        else:
            if tv:
                # get surface verts for <vid>
                for v in sverts[sl][vid]:
                    vec = v.co-tv.co
                    # we need the projection of <vec> onto the plane defined by edges of the template vertex <v>
                    vec = projectOntoPlane(vec, self.template.nodes[vid].n)
                    if isVectorBetweenVectors(vec, vec1, vec2):
                        # Stop iteration through surface verts for <vid>,
                        # the required surface vert has been found
                        break
                sverts[sl][vid].remove(v)
            else:
                v = sverts[sl][vid].pop()
        self.numVerts -= 1
        return v, vid
    
    def getSurfaceLayer(self):
        return self.sl or self._sl
    

class ChildOffsets:
    """
    A data structure to deal with offsets for child items
    
    Offsets for the vertex <vid> are stored in the same order as the entries
    for edges in <template.nodes[vid].edges>
    The corner for an offset is defined by unit vectors from entries
    with the indices <i> and <i+1> in <template.nodes[vid].edges>. However the unit vector
    from the entry with the index <i> is enough to access the relate offset. 
    """
    def __init__(self, template):
        self.nodes = template.nodes
        offsets = {}
        self.offsets = offsets
        # For the sake of correct operation set child offset to zero for all corners
        # of each vertex in the template
        for v in template.bm.verts:
            vid = template.getVid(v)
            _offsets = []
            offsets[vid] = _offsets
            for _ in v.link_edges:
                _offsets.append(zeroVector.copy())
    
    def get(self, vid, edgeVector, normalized=False):
        """
        Get offset for the corner of the vertex <vid> defined by the vector <edgeVector>
        originating from the vertex <vid>.
        
        The variable <normalized> indicated whether <edgeVector> is normalized.
        If <edgeVector> is None, then offset is taken from the first corner of the vertex <vid>.
        The use case with <edgeVector> is None happens if all corners of the vertex <vid> have
        the same offset.
        """
        offsets = self.offsets[vid]
        if edgeVector:
            node = self.nodes[vid]
            if not normalized:
                edgeVector = edgeVector.normalized()
            index = node.getEdgeIndex(edgeVector)
            return offsets[index]
        else:
            return offsets[0]
    
    def set(self, vid, edgeVector, offset, normalized=False):
        """
        Set <offset> for the corner of the vertex <vid> defined by the vector <edgeVector>
        originating from the vertex <vid>.
        
        The variable <normalized> indicated whether <edgeVector> is normalized.
        If <edgeVector> is None, then <offset> is set for all corners of the vertex <vid>.
        """
        # if edge is None, set offsets for all edges sharing the same vertex <vid>
        offsets = self.offsets[vid]
        if edgeVector:
            node = self.nodes[vid]
            if not normalized:
                edgeVector = edgeVector.normalized()
            index = node.getEdgeIndex(edgeVector)
            offsets[index] = offset
        else:
            for i in range(len(offsets)):
                offsets[i] = offset
    
    def add(self, vid, edgeVector, offset, normalized=False):
        """
        Add <offset> for the corner of the vertex <vid> defined by the vector <edgeVector>
        originating from the vertex <vid>.
        
        The variable <normalized> indicated whether <edgeVector> is normalized.
        If <edgeVector> is None, then <offset> is added for all corners of the vertex <vid>.
        """
        offsets = self.offsets[vid]
        if edgeVector:
            node = self.nodes[vid]
            if not normalized:
                edgeVector = edgeVector.normalized()
            index = node.getEdgeIndex(edgeVector)
            offsets[index] += offset
        else:
            for i in range(len(offsets)):
                offsets[i] += offset

class Template:
    
    def __init__(self, o, parentTemplate=None, **kwargs):
        self.o = o
        self.parentTemplate = parentTemplate
        p = o.parent
        self.p = p
        
        bm = getBmesh(o)
        self.bm = bm
        # create a layer for vertex groups if necessary
        deform = bm.verts.layers.deform
        self.layer = deform[0] if deform else deform.new()
        
        if not kwargs.get("skipInit", None):
            self.nodes = {}
            self.childOffsets = ChildOffsets(self)
    
    def setVid(self, v):
        """
        Set vertex id as a vertex group
        """
        p = self.p
        layer = self.layer
        # If the number of group vertices is greater than 1,
        # it most likely means that the vertex groups were copied from the neighboring vertices
        # during the loop cut or similar operation
        if not v[layer] or len(v[layer])>1:
            v[layer].clear()
            assignGroupToVerts(self.o, layer, str(p["vert_counter"]), v)
            p["vert_counter"] += 1
    
    def getVid(self, v):
        """
        Get vertex id from the related vertex group
        
        Returns a string
        """
        self.setVid(v)
        groupIndex = v[self.layer].keys()[0]
        return self.o.vertex_groups[groupIndex].name
    
    def complete(self):
        setBmesh(self.o, self.bm)
    
    def assignNode(self, n):
        """
        Assign Blender object <n> as a node for the selected vertices
        """
        for v in self.bm.verts:
            if v.select:
                # get our vertex id under the variable <vid>
                self.o[ self.getVid(v) ] = n.name
                v.select = False
        return self
    
    def addParts(self):
        # get the selected faces
        faces = []
        for f in self.bm.faces:
            if f.select:
                faces.append(f)
        if not faces:
            return None
        
        p = self.p
        partCounter = p["part_counter"]
        parentId = self.o["id"]
        for f in faces:
            # find the coordinates of the leftmost and the lowest vertices if the <face>
            minX = float("inf")
            minZ = float("inf")
            for v in f.verts:
                # check if all vertices of the face <f> have vertex id (actually the related vertex group) set
                self.setVid(v)
                
                if v.co.x < minX:
                    minX = v.co.x
                if v.co.z < minZ:
                    minZ = v.co.z
            # create an object for the new part
            location = mathutils.Vector((minX, 0., minZ))
            o = createMeshObject("T_Part_" + str(parentId) + "_" + str(partCounter), self.o.location+location)
            o.show_wire = True
            o.show_all_edges = True
            o["id"] = partCounter
            # set id of the parent part
            o["p"] = parentId
            # reverse the surface <s1> by default
            o["s1"] = "reversed"
            o.parent = p
            bm = getBmesh(o)
            # create a layer for vertex groups
            layer = bm.verts.layers.deform.new()
            # create vertices for the new part
            verts = []
            maxVid = 0
            for v in f.verts:
                vid = self.getVid(v)
                _vid = int(vid)
                v = bm.verts.new(v.co - location)
                # copy vertex ids (actually the related vertex groups) from the parent face
                assignGroupToVerts(o, layer, vid, v)
                if _vid > maxVid:
                    maxVid = _vid
                verts.append(v)
            bm.faces.new(verts)
            setBmesh(o, bm)
            p["vert_counter"] = maxVid + 1
            partCounter += 1
        p["part_counter"] = partCounter
        return self
    
    def getTopParent(self):
        """
        Get the top level template, e.g. the outer frame for a window
        """
        # check if the template itself is a parent
        if not "p" in self.o:
            return Template(self.o)
        for o in self.p.children:
            if not "p" in o:
                return Template(o)
    
    def getChildren(self):
        """
        Get descendant templates for the template in question
        """
        children = []
        for o in self.p.children:
            if "p" in o and o["p"] == self.o["id"]:
                children.append(Template(o, self))
        return children
    
    def setNode(self, v, n, parent, context):
        """
        Set a node Blender object <n> for the template vertex <v>
        """
        # node wrapper
        nw = self.getNodeWrapper(v)
        if not nw.setBlenderObject(n):
            return
        vid = self.getVid(v)
        nw.vid = vid
        
        # keep the node wrapper <nw> in the dictionary <self.nodes>
        self.nodes[vid] = nw
        
        # create a copy of <n> at the location of the vertex <v>
        loc = v.co.copy()
        loc += self.getOffset(v, vid)
        _n = n
        n = createMeshObject(n.name, loc, _n.data)
        # copy vertex groups
        for g in _n.vertex_groups:
            n.vertex_groups.new(g.name)
        context.scene.update()
        parent_set(parent, n)
        context.scene.update()
        
        nw.updateVertexGroupNames(n, self)
        
        # select the Blender object <o>, so we can transform it, e.g. rotate it
        n.select = True
        matrix = nw.transform(n)
        
        self.scanOffsets(vid, _n, matrix)
        # <parent> is also the current Blender active object
        parent.select = True
        bpy.ops.object.join()
        
        parent.select = False
    
    def getNodeWrapper(self, v):
        from workshop.node import LNode, TNode, YNode, CrossNode, XNode
        numEdges = len(v.link_edges)
        edges = getEdges(v)
        if numEdges == 2:
            return LNode(v, edges)
        elif numEdges == 3:
            # consider, that we have a T-node
            nw = TNode(v, edges)
            return nw if nw.edges else YNode(v, edges)
        elif numEdges == 4:
            # consider, that we have c cross-node
            nw = CrossNode(v, edges)
            return nw if nw.edges else XNode(v, edges)
    
    def bridgeOrExtendNodes(self, o, bm, dissolveEndEdges):
        nodes = self.nodes
        # iterate through the edges of the template
        for e in self.bm.edges:
            vid1 = self.getVid(e.verts[0])
            vid2 = self.getVid(e.verts[1])
            if vid1 in nodes and vid2 in nodes:
                self.bridgeNodes(vid1, vid2, o, bm, dissolveEndEdges)
            elif not vid1 in nodes and not vid2 in nodes:
                # nothing to do here
                continue
            else:
                v1 = e.verts[0]
                v2 = e.verts[1]
                # only one node (either for the template vertex <vid1> or <vid2>) was set
                # assume the node was set for the template vertex <vid1>
                if vid2 in nodes:
                    v1, v2 = v2, v1
                self.extendNode(v1, v2, o, bm)
    
    def bridgeNodes(self, vid1, vid2, o, bm, dissolveEndEdges):
        """
        Bridge open edge loops from the nodes set for the template vertices <vid1> and <vid2>
        """
        layer = bm.verts.layers.deform[0]
        groupIndices = set( (o.vertex_groups["e_" + vid1 + "_" +vid2].index, o.vertex_groups["e_" + vid2 + "_" +vid1].index) )
        # We will bridge two edge loops (either open or closed) composed of the vertices belonging to
        # the vertex groups with the indices from <groupIndices>
        
        # For each vertex group index in <groupIndices> get a single vertex belonging
        # to the related vertex group
        verts = {}
        for _v in bm.verts:
            vert = None
            for i in groupIndices:
                if i in _v[layer]:
                    vert = _v
                    break
            if vert:
                verts[i] = vert
                groupIndices.remove(i)
                if not groupIndices:
                    break
        # for each key in <verts> (the key is actually a vertex group index) get edges to bridge
        edges = []
        for i in verts:
            _edges = []
            edges.append(_edges)
            vert = verts[i]
            _v = vert
            # the last visited edge
            edge = None
            while True:
                for e in _v.link_edges:
                    if e == edge:
                        continue
                    # a candidate for the next vertex
                    # 'vn' stands for 'vertex next'
                    _vn =  e.verts[1] if e.verts[0] == _v else e.verts[0]
                    if i in _vn[layer]:
                        # keep the reference to the initial edge (needed for the case of open edge loops)
                        if _v == vert:
                            _edge = e
                        _v = _vn
                        edge = e
                        _edges.append(edge)
                        break
                else:
                    # the edges don't form a closed loop!
                    # now go in the opposite direction relative to the initial vertex <vert>
                    
                    _v = vert
                    # the last visited edge is the one we saved under under the variable <_edge>
                    edge = _edge
                    # basically the same code as above
                    while True:
                        for e in _v.link_edges:
                            if e == edge:
                                continue
                            # a candidate for the next vertex
                            # 'vn' stands for 'vertex next'
                            _vn =  e.verts[1] if e.verts[0] == _v else e.verts[0]
                            if i in _vn[layer]:
                                _v = _vn
                                edge = e
                                _edges.append(edge)
                                break
                        else:
                            break
                    break
                if _v == vert:
                    break
        bmesh.ops.bridge_loops(bm, edges = edges[0] + edges[1])
        if dissolveEndEdges:
            for _edges in edges:
                bmesh.ops.dissolve_edges(bm, edges=_edges, use_verts=True, use_face_split=False)
    
    def extendNode(self, vert, toVert, o, bm):
        """
        Extend the open edge loop from the node set for the template vertex <vert> towards the template vertex <toVert>
        """
        vid = self.getVid(vert)
        toVid = self.getVid(toVert)
        
        verts = getVertsForVertexGroup(o, bm, o.vertex_groups["e_" + vid + "_" +toVid].name)
        
        # perform translation of <verts> along the vector defined by the vertices <vid> and <toVid>
        
        # unit vector for the line defined by the vertices <vid> and <toVid>
        e = (toVert.co - vert.co).normalized()
        # We need to take into account offset when calculating the amount of translation,
        # so pick up an arbitrary vertex from <verts>, get a vector by
        # subtracting <vert.co> and project that vector onto the line defined by
        # the vertices <vert> and <toVert> to calculate the offset relative to the vertex <vert>
        bmesh.ops.translate(
            bm,
            verts=getVertsForVertexGroup(o, bm, o.vertex_groups["e_" + vid + "_" +toVid].name),
            vec=toVert.co - vert.co - projectOntoLine(verts[0].co - vert.co, e)
        )
    
    def makeSurfaces(self, o, bm):
        # sverts stands for surface verts
        sverts = SurfaceVerts(o, bm, self)
        
        if not sverts.numVerts:
            return
        
        # now compose the surface out of the vertices <verts>
        while sverts.numVerts:
            v, vid = sverts.pop()
            # node wrapper for the surface vert <v>
            n = self.nodes[vid]
            # template vertex
            tv = n.v
            # ordered edges for the surface vert <v>
            edges = n.edges
            # find the pair of edges where the surface vert <v> is located
            # vector from the node origin to the location of the surface vert <v>
            vec = v.co - tv.co
            # we need the projection of <vec> onto the plane defined by edges of the template vertex <v>
            vec = projectOntoPlane(vec, n.n)
            if len(edges) == 2:
                # the simpliest case for only two edges, no need for any lookup
                l = tv.link_loops[0]
            else:
                e1, e2 = n.getNeighborEdges(vec)
                # template vertices on the ends of the edges e1 and e2
                tv1 = e1[1]
                tv2 = e2[1]
                # Get a BMLoop from tv.link_loops for which
                # BMLoops coming through tv1 and tv2 are the next and previous BMLoops
                for l in tv.link_loops:
                    if (l.link_loop_next.vert == tv1 and l.link_loop_prev.vert == tv2) or \
                        (l.link_loop_prev.vert == tv1 and l.link_loop_next.vert == tv2):
                        break
            # vertices of BMFace for the surface
            verts = [v]
            # perform a walk along BMFace containing BMLoop <l>
            # the initial loop
            loop = l
            vec2 = (l.link_loop_next.vert.co - l.vert.co).normalized()
            while True:
                l = l.link_loop_next
                if l == loop:
                    break
                vec1 = -vec2
                vec2 = (l.link_loop_next.vert.co - l.vert.co).normalized()
                v = sverts.pop(l.vert, vec1, vec2)[0]
                if v:
                    verts.append(v)
            # finally, create BMFace for the surface
            face = bm.faces.new(verts)
            # check if we need to reverse the normal to the current surface
            sl = sverts.getSurfaceLayer()
            if sl in self.o and self.o[sl] == "reversed":
                bmesh.ops.reverse_faces(bm, faces=(face,))
    
    def getOffset(self, v, vid):
        p = self.parentTemplate
        e = getOuterEdgeVector(v)
        return p.childOffsets.get(vid, e) if p and vid in p.nodes else self.childOffsets.get(vid, None)
    
    def prepareOffsets(self):
        """
        Calculate offsets for intermediary template vertices which don't
        have an ancestor in the parent template
        """
        p = self.parentTemplate
        if not p:
            # nothing to prepare
            return
        # iterate through the vertices of the template to find an outer vertex presented in <p.childOffsets>
        # also find a pair of outer edges connected to the outer vertex
        vert = None
        # a variable for the first edge to be found
        _e = None
        for v in self.bm.verts:
            vid = self.getVid(v)
            if vid in p.nodes:
                # check if the vertex <v> has an outer edge
                for e in v.link_edges:
                    if len(e.link_faces) == 1:
                        if _e:
                            # the second edge is simply <e>
                            break
                        else:
                            vert = v
                            # the first edge is found
                            _e = e
                if vert:
                    break
        if not vert:
            # nothing to prepare
            return
        
        _vec = getVectorFromEdge(_e, vert)
        vec = getVectorFromEdge(e, vert)
        # the cross product of <_e> and <p> must point in the direction of the normal to <vert>
        if _vec.cross(vec).dot(vert.normal) > 0:
            e = _e
            vec = _vec
        # the reference edges to get offset from the ChildOffset class is <e>
        
        # walk along outer edges starting from <vert>
        v = vert
        # the last visited edge
        _e = e
        # the unit vector along the current edge
        _n = None
        vids = []
        # the current offset
        offset = p.childOffsets.get(vid, vec)
        while True:
            # Walk along outer vertices until we encounter a vertex with vid in <p.childOffsets> OR
            # the direction of the current edge is changed significantly
            
            # get the next outer vertex
            for e in v.link_edges:
                if len(e.link_faces) == 1 and e != _e:
                    _v = v
                    v = e.verts[1] if e.verts[0] == v else e.verts[0]
                    break
            vid = self.getVid(v)
            
            hasOffset = vid in p.nodes
            
            # the unit vector along the edge defined by <_v> and <v>
            n = (v.co - _v.co).normalized()
            
            # check if the direction of the edge has been changed
            directionChanged = _n and abs(1.-_n.dot(n)) > zero2
            
            if hasOffset:
                # set the current offset
                offset = p.childOffsets.get(vid, getVectorFromEdge(e, v))
                _offset = None
                if directionChanged:
                    # set offset only sfor the last vid in <vids>
                    vids = [vids[-1]]
                if vids:
                    # We need the projection of <offset> vector onto the plane
                    # defined by the normal <n> to the plane
                    _offset = projectOntoPlane(offset, n)
                    # set offset for all outer vertices in <vids> list
                    for vid in vids:
                        self.childOffsets.set(vid, None, _offset)
                    vids = []
                _n = None
            else:
                if directionChanged:
                    offset = None
                    _n = None
                    vids = [vid]
                else:
                    if offset:
                        # We need the projection of <offset> vector onto the plane
                        # defined by the normal <n> to the plane
                        _offset = projectOntoPlane(offset, n)
                        self.childOffsets.set(vid, None, _offset)
                    else:
                        vids.append(vid)
                    _n = n
            # check if need to quit the cycle
            if v == vert:
                break
            _e = e
    
    def scanOffsets(self, vid, n, matrix):
        """
        Scan Blender object <n> for Blender EMPTY objects that define an offset for a child item
        """
        # offsets could have been be set in <self.prepareOffsets()>
        
        for e in n.children:
            if "t" in e and e["t"]=="offset":
                offset = matrix * e.location if matrix else e.location.copy()
                # get neighbor edges for the <offset> vector
                # actually, the first edge is enough since it unambiguously defines the related corner
                e1 = self.nodes[vid].getNeighborEdges(offset)[0][0]
                p = self.parentTemplate
                if p and vid in p.nodes:
                    offset += p.childOffsets.get(vid, e1, True)
                self.childOffsets.add(vid, e1, offset, True)