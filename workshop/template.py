import mathutils, bpy
from util.blender import createMeshObject, getBmesh, setBmesh, parent_set


class Template:
    
    def __init__(self, o):
        self.o = o
        p = o.parent
        self.p = p
        # ensure <o> has the attribute <counter>
        if "counter" not in o:
            o["counter"] = 1
        # ensure <p> has the attribute <counter>
        if "counter" not in p:
            p["counter"] = 1
        # ensure <o> has the attribute <id>
        if "id" not in o:
            o["id"] =  p["counter"]
            p["counter"] += 1
        
        bm = getBmesh(o)
        # ensure <bm.verts> has a data layer
        data = bm.verts.layers.int
        if not data:
            data.new("prk")
        self.bm = bm
    
    def complete(self):
        setBmesh(self.o, self.bm)
    
    def assignJunction(self, j):
        """
        Assign Blender object <j> as a junction for the selected vertices
        """
        o = self.o
        counter = o["counter"]
        layer = self.bm.verts.layers.int["prk"]
        for v in self.bm.verts:
            if v.select:
                # set id (actually <prk> attribute) if necessary
                if not v[layer]:
                    v[layer] = counter
                    counter += 1
                # get our vertex id under the variable <vid>
                vid = v[layer]
                o[str(vid)] = j.name
                v.select = False
        o["counter"] = counter
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
        counter = p["counter"]
        parentId = self.o["id"]
        for f in faces:
            # find the coordinates of the leftmost and the lowest vertices if the <face>
            minX = float("inf")
            minZ = float("inf")
            for v in f.verts:
                if v.co.x < minX:
                    minX = v.co.x
                if v.co.z < minZ:
                    minZ = v.co.z
            # create an object for the new pane
            location = mathutils.Vector((minX, 0., minZ))
            counter += 1
            o = createMeshObject("T_Pane_" + str(parentId) + "_" + str(counter), self.o.location+location)
            o.show_wire = True
            o.show_all_edges = True
            o["id"] = counter
            # set id of the parent pane
            o["p"] = parentId
            o.parent = p
            bm = getBmesh(o)
            # create vertices for the new pane
            verts = []
            for v in f.verts:
                v = bm.verts.new(v.co - location)
                verts.append(v)
            bm.faces.new(verts)
            setBmesh(o, bm)
        p["counter"] = counter
        return self
    
    def getParent(self):
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
                children.append(Template(o))
        return children
    
    def setJunction(self, v, j, parent, context):
        """
        Set a junction Blender object <j> for the template vertex <v>
        """
        # junction wrapper
        jw = self.getJunctionWrapper(v)
        if not jw.validate(j):
            return
        # create a copy of <j> at the location of the vertex <v>
        loc = v.co
        _j = j
        j = createMeshObject(j.name, loc, _j.data)
        # copy vertex groups
        for g in _j.vertex_groups:
            j.vertex_groups.new("_" + g.name)
        jw.prepare(j)
        context.scene.update()
        parent_set(parent, j)
        context.scene.update()
        j.select = True
        bpy.ops.object.join()
        j.select = False
    
    def getJunctionWrapper(self, v):
        from .junction import LJunction, TJunction
        numEdges = len(v.link_edges)
        if numEdges == 2:
            return LJunction(v)
        elif numEdges == 3:
            return TJunction(v)