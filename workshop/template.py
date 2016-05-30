import mathutils, bpy, bmesh
from base import zero2
from util.blender import createMeshObject, getBmesh, setBmesh, parent_set, assignGroupToVerts
from util.geometry import projectOntoPlane


def getEdges(v):
    edges = []
    for e in v.link_edges:
        _v = e.verts[1] if e.verts[0] == v else e.verts[0]
        edges.append([ (_v.co - v.co).normalized(), _v ])
    return edges


def isVectorBetweenVectors(vec, vec1, vec2):
    """
    Checks if the vector <vec> lies between vectors <vec1> and <vec2>,
    provided all three vectors share the same origin
    """
    cross1 = vec.cross(vec1)
    cross2 = vec.cross(vec2)
    # cross1 and cross2 must point in the opposite directions
    # at least one angle must be less than 90 degrees
    return cross1.dot(cross2) < 0. and (vec.dot(vec1)>0. or vec.dot(vec2)>0.)


def getNeighborEdges(vec, edges, n):
    """
    Returns two neighbor edges from <edges> for the vector <vec>
    
    Args:
        vec (mathutils.Vector): A unit vector that starts at the template vertex 
        edges (list): An ordered list of entries for edges of the template vertex.
            The list starts from the entry for the base edge. Each entry of the list is
            a list itself with 4 entries:
            (0) Unit vector along the edge the starts at the template vertex
            (1) Opposite vertex (BMvert) of the edge
            (2) Boolean variable that defines in which circle half the edge is located
            (3) Cosine of the angle between the edge and the base edge
        n (mathutils.Vector): A normal to the plane where the template vertex and its <edges> are located
    """
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
        # tv stands for template vert
        # If <templateVert>, <vec1> and <vec2> are given, that means pop a surface vert for <tv>
        # located between vectors <vec1> and <vec2>
        # If <tv>, <vec1> and <vec2> aren't given, a random surface vert is returned
        sverts = self.sverts
        if self.sl is None:
            # set the current surface layer
            self.sl = next(iter(sverts))
        sl = self.sl
        vid = self.template.getVid(tv) if tv else next(iter(sverts[sl]))
        if len(sverts[sl][vid]) == 1:
            v = sverts[sl][vid][0]
            del sverts[sl][vid]
            if not len(sverts[sl]):
                del sverts[sl]
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
        

class Template:
    
    def __init__(self, o, parentTemplate=None):
        self.o = o
        self.parentTemplate = parentTemplate
        p = o.parent
        self.p = p
        
        bm = getBmesh(o)
        self.bm = bm
        # create a layer for vertex groups if necessary
        deform = bm.verts.layers.deform
        self.layer = deform[0] if deform else deform.new()
        
        self.nodes = {}
        self.childOffsets = {}
    
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
        groupIndex = v[self.layer].keys()[0]
        return self.o.vertex_groups[groupIndex].name
    
    def complete(self):
        setBmesh(self.o, self.bm)
    
    def assignNode(self, j):
        """
        Assign Blender object <j> as a node for the selected vertices
        """
        for v in self.bm.verts:
            if v.select:
                self.setVid(v)
                # get our vertex id under the variable <vid>
                self.o[ self.getVid(v) ] = j.name
                v.select = False
        return self
    
    def addPanes(self):
        # get the selected faces
        faces = []
        for f in self.bm.faces:
            if f.select:
                faces.append(f)
        if not faces:
            return None
        
        p = self.p
        paneCounter = p["pane_counter"]
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
            # create an object for the new pane
            location = mathutils.Vector((minX, 0., minZ))
            o = createMeshObject("T_Pane_" + str(parentId) + "_" + str(paneCounter), self.o.location+location)
            o.show_wire = True
            o.show_all_edges = True
            o["id"] = paneCounter
            # set id of the parent pane
            o["p"] = parentId
            o.parent = p
            bm = getBmesh(o)
            # create a layer for vertex groups
            layer = bm.verts.layers.deform.new()
            # create vertices for the new pane
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
            paneCounter += 1
        p["pane_counter"] = paneCounter
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
    
    def setNode(self, v, j, parent, context):
        """
        Set a node Blender object <j> for the template vertex <v>
        """
        # node wrapper
        jw = self.getNodeWrapper(v)
        if not jw.setBlenderObject(j):
            return
        vid = self.getVid(v)
        jw.vid = vid
        
        # create a copy of <j> at the location of the vertex <v>
        loc = v.co.copy()
        offset = self.getOffset(vid)
        if offset:
            loc += offset
        _j = j
        j = createMeshObject(j.name, loc, _j.data)
        # copy vertex groups
        for g in _j.vertex_groups:
            j.vertex_groups.new(g.name)
        context.scene.update()
        parent_set(parent, j)
        context.scene.update()
        # select the Blender object <o>, so we can transform it, e.g. rotate it
        j.select = True
        matrix = jw.transform(j)
        
        self.scanOffsets(vid, _j, matrix)
                
        jw.updateVertexGroupNames(j, self)
        # <parent> is also the current Blender active object
        parent.select = True
        bpy.ops.object.join()
        parent.select = False
        # keep the node wrapper <js> in the dictionary <self.nodes>
        self.nodes[vid] = jw
    
    def getNodeWrapper(self, v):
        from workshop.node import LNode, TNode, YNode
        numEdges = len(v.link_edges)
        edges = getEdges(v)
        if numEdges == 2:
            return LNode(v, edges)
        elif numEdges == 3:
            # consider, that we have a T-node
            jw = TNode(v, edges)
            return jw if jw.edges else YNode(v, edges)
    
    def bridgeNodes(self, o, bm):
        layer = bm.verts.layers.deform[0]
        # keep track of visited edges
        edges = set()
        for v in self.bm.verts:
            for e in v.link_edges:
                if e.index in edges:
                    continue
                vid1 = self.getVid(e.verts[0])
                vid2 = self.getVid(e.verts[1])
                groupIndices = set(( o.vertex_groups[vid1 + "_" +vid2].index, o.vertex_groups[vid2 + "_" +vid1].index ))
                # for each vertex group index in <groupIndices> get a vertex
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
                # for each key in <verts> (the key is actually a vertex group index) get edges to bridge
                edges = []
                for i in verts:
                    vert = verts[i]
                    _v = vert
                    # the last visited edge
                    edge = None
                    while True:
                        for e in _v.link_edges:
                            if e == edge:
                                continue
                            # a candidate for the next vertex
                            _vn =  e.verts[1] if e.verts[0] == _v else e.verts[0]
                            if i in _vn[layer]:
                                _v = _vn
                                edge = e
                                edges.append(edge)
                                break
                        if _v == vert:
                            break
                bmesh.ops.bridge_loops(bm, edges = edges)
    
    def makeSurfaces(self, o, bm):
        # sverts stands for surface verts
        sverts = SurfaceVerts(o, bm, self)
        
        if not sverts.numVerts:
            return
        
        # now compose the surface out of the vertices <verts>
        while sverts.numVerts:
            v, vid = sverts.pop()
            # node wrapper for the surface vert <v>
            j = self.nodes[vid]
            # template vertex
            tv = j.v
            # ordered edges for the surface vert <v>
            edges = j.edges
            # find the pair of edges where the surface vert <v> is located
            # vector from the node origin to the location of the surface vert <v>
            vec = v.co - tv.co
            # we need the projection of <vec> onto the plane defined by edges of the template vertex <v>
            vec = projectOntoPlane(vec, j.n)
            vec.normalize()
            if len(edges) == 2:
                # the simpliest case for only two edges, no need for any lookup
                l = tv.link_loops[0]
            else:
                e1, e2 = getNeighborEdges(vec, edges, tv.normal)
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
            bm.faces.new(verts)
    
    def getOffset(self, vid):
        p = self.parentTemplate
        return p.childOffsets[vid] if p and vid in p.childOffsets\
            else (self.childOffsets[vid] if vid in self.childOffsets else None)
    
    def prepareOffsets(self):
        """
        Calculate offsets for intermediary template vertices which don't
        have an ancestor in the parent template
        """
        p = self.parentTemplate
        if not p:
            # nothing to prepare
            return
        # iterate through the vertices of the template to find an outer vert presented in <p.childOffsets>
        vert = None
        for v in self.bm.verts:
            vid = self.getVid(v)
            if vid in p.childOffsets:
                # check if the vertex <v> has an outer edge
                for e in v.link_edges:
                    if len(e.link_faces) == 1:
                        vert = v
                        break
                if vert:
                    break
        if not vert:
            # nothing to prepare
            return
        # walk along outer edges starting from <vert>
        v = vert
        # the last visited edge
        _e = None
        # the unit vector along the current edge
        _n = None
        vids = []
        # the current offset
        offset = p.childOffsets[vid]
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
            if vid in p.childOffsets:
                # set the current offset
                offset = p.childOffsets[vid]
                if vids:
                    # the unit vector along the edge defined by <_v> and <v>
                    n = (v.co - _v.co).normalized()
                    # We need the projection of <offset> vector onto the plane
                    # defined by the normal <n> to the plane
                    _offset = projectOntoPlane(offset, n)
                    # assign offsets to all outer vertices in <vids> list
                    for vid in vids:
                        self.childOffsets[vid] = _offset
                    vids = []
                _n = None
            else:
                # the unit vector along the edge defined by <_v> and <v>
                n = (v.co - _v.co).normalized()
                if offset:
                    if _n:
                        # check if the direction of the edge has been changed
                        # if changed then reset the offset
                        if abs(1.-_n.dot(n)) > zero2:
                            offset = None
                        else:
                            self.childOffsets[vid] = offset
                    else:
                        # We need the projection of <offset> vector onto the plane
                        # defined by the normal <n> to the plane
                        offset = projectOntoPlane(offset, n)
                        self.childOffsets[vid] = offset
                else:
                    if _n:
                        # the direction of the edge has been changed
                        if abs(1.-_n.dot(n)) > zero2:
                            if vids:
                                vids = []
                        else:
                            vids.append(vid)
                    else:
                        vids.append(vid)
                _n = n
            # check if need to quit the cycle
            if v == vert:
                break
            _e = e
    
    def scanOffsets(self, vid, j, matrix):
        """
        Scan Blender object <j> for Blender EMPTY objects that define an offset for a child item
        """
        for e in j.children:
            if "t" in e and e["t"]=="offset":
                offset = matrix * e.location if matrix else e.location.copy()
                p = self.parentTemplate
                if p and vid in p.childOffsets:
                    offset += p.childOffsets[vid]
                if vid in self.childOffsets:
                    # <self.childOffsets[vid]> could be set in <self.prepareOffsets()>
                    self.childOffsets[vid] += offset
                else:
                    self.childOffsets[vid] = offset
    
    def scanVerts(self, j, vid):
        """
        Scan vertices of the node Blender object <j> to find ones belonging to particular vertex groups
        
        Args:
            j: Blender object
            vid (String): id of the template vertex for which <j> is to be set as a node
        """
        return
        for v in j.data.vertices:
            for g in v.groups:
                # group name
                n = j.vertex_groups[g.group].name
                if n == "c": # offset for a child template
                    offsets = self.childOffsets
                    if not vid in offsets:
                        offsets[vid] = []
                    offsets[vid].append(v.co)
                elif n[0] == "s": # defines a surface
                    surfaces = self.surfaces
                    # index if the surface
                    si = "0" if len(n) == 1 else n[1:]
                    if not si in surfaces:
                        surfaces[si] = []
                    surfaces[si].append(0) # TODO