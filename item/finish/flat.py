import bpy, bmesh
from base.item import Item
from base import defaultUvMap, pContext, zAxis, getItem, getLevelHeight, getNextLevelParent,\
    getReferencesForAttached, getControlEmptyFromLoop
from util.blender import createMeshObject, getBmesh, setBmesh, assignGroupToVerts,\
    addHookModifier, addSolidifyModifier, addBooleanModifier, parent_set, getVertsForVertexGroup


class GuiFinish:
    
    def draw(self, context, layout):
        layout.operator("prk.set_material_from_texture")


class FinFlat(Item):
    
    type = "fin"
    
    name = "Finish"
    
    def createFromArea(self, area):
        context = self.context
        controls = area.getControls()
        
        obj = createMeshObject(area.obj.name+"_finish")
        obj["t"] = self.type
        self.obj = obj
        
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        # a vector along z-axis with the length equal to the wall height
        height = getLevelHeight(context, area.obj)*zAxis
        numControls = len(controls)
        for c in controls:
            group = c["g"]
            # the vert at the bottom
            v_b = bm.verts.new(c.location)
            # the vert at the top
            v_t = bm.verts.new(c.location+height)
            assignGroupToVerts(obj, layer, group, v_b, v_t)
            # assign vertex group for the top vertex
            assignGroupToVerts(obj, layer, "t", v_t)
        
        # create faces
        bm.verts.ensure_lookup_table()
        v1_b = bm.verts[-2]
        v1_t = bm.verts[-1]
        for i in range(numControls):
            # <2> is the number of vertices (of the just created wall surface) per control point
            v2_b = bm.verts[i*2]
            v2_t = bm.verts[i*2+1]
            bm.faces.new((v1_b, v1_t, v2_t, v2_b))
            v1_b = v2_b
            v1_t = v2_t
        setBmesh(obj, bm)
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        # perform parenting
        parent_set(area.obj.parent, obj)
        # one more update
        context.scene.update()
        
        # add HOOK modifiers
        for c in controls:
            group = c["g"]
            addHookModifier(obj, group, c, group)
        # add a HOOK modifier controlling the top vertices
        addHookModifier(obj, "t", getNextLevelParent(context, obj), "t")
        # add a SOLIDIFY modifier
        addSolidifyModifier(obj, "solidify", thickness=0.001, offset=1.)
        self.treatInsertions(controls)
    
    def treatInsertions(self, controls):
        """
        The function treats insertions (e.g. windows, doors) relevant for the finish.
        Namely, a BOOLEAN modifier is created for each relevant opening.
        """
        from item.opening import getReferencesForOpening
        # build a list of EMPTYs that defines each wall part that forms the finish
        walls = {}
        _c = controls[-1]
        for c in controls:
            # consider the wall part defined by <_c> and <c>
            
            if _c["t"] == "wc":
                if c["t"] == "wc":
                    # both <_c> and <c> are corner EMPTYs
                    o1 = _c
                    o2 = c
                else:
                    # <c> is attached
                    # choose <o> depending on if <_c> and <c> belong to the same wall part
                    if _c["m"] == c["m"]:
                        o1 = _c
                        o2 = c
                    else:
                        o1, o2 = getReferencesForAttached(c)
            elif c["t"] == "wc":
                # <_c> is attached
                # choose <o1> depending on if <_c> and <c> belong to the same wall part
                if _c["m"] == c["m"]:
                    o1 = _c
                    o2 = c
                else:
                    o1, o2 = getReferencesForAttached(_c)
            else:
                # both <_c> and <c> are attached EMPTYs
                _m_self = _c["m"]
                _m_base = getReferencesForAttached(_c)[0]["m"]
                m_self = c["m"]
                m_base = getReferencesForAttached(c)[0]["m"]
                
                if _m_self == m_self and (("p" in c and c["p"] == _c["g"]) or ("n" in c and c["n"] == _c["g"])):
                    o1 = _c
                    o2 = c
                elif _m_base == m_base:
                    o1, o2 = getReferencesForAttached(c)
                elif _m_base == m_self:
                    o1, o2 = getReferencesForAttached(_c)
                else: # _m_self == m_base
                    o1, o2 = getReferencesForAttached(c)
            
            # ensure that <o2> follows <o1>
            if "n" in o2 and o2["n"] == o1["g"]:
                o1, o2 = o2, o1
            # <o2> defines the wall part where the finish part defined by <_c> and <c> is placed
            # create an entry for <o2>
            walls[o2["g"]] = [o1, o2, _c, c]
            _c = c
        
        # iterate through immediate children of the parent Blender object of the finish
        for o in self.obj.parent.children:
            if "t" in o and (o["t"] == "window" or o["t"] == "door"):
                o1, o2 = getReferencesForOpening(o)
                # ensure that <o2> follows <o1>
                if "n" in o2 and o2["n"] == o1["g"]:
                    o2 = o1
                # <o2> defines the wall part where the opening <o> is placed
                # check if the finish also uses the wall part defined by <o2>
                if o2["g"] in walls:
                    # if necessary, calculate the position of the finish part along the wall part defined by <o2>
                    # lazy calculation is used!
                    e = walls[o2["g"]]
                    if not isinstance(e[2], float):
                        l1 = (e[2].location - e[0].location).length
                        l2 = (e[3].location - e[0].location).length
                        if l1 > l2:
                            l1, l2 = l2, l1
                        e[2] = l1
                        e[3] = l2
                    
                    # get an instance of <Opening> class
                    item = getItem(self.context, self.op, o)
                    # calculate the position of the origin of the opening along the wall part defined by <o2>
                    l1 = (e[1].location - e[0].location).dot(o.location - e[0].location) / (e[1].location - e[0].location).length
                    addModifier = True
                    # check if l1 is inside the finish part
                    if not e[2] < l1 <e [3]:
                        # calculate the position of the other end of the opening along the wall part defined by <o2>
                        # the width of the opening:
                        l2 = item.width.location.x
                        l2 = (l1 - l2) if o1["l"] else (l1 + l2)
                        if not e[2] < l2 <e [3]:
                            addModifier = False
                    if addModifier:
                        addBooleanModifier(self.obj, o.name, item.envelope)
    
    def assignUv(self, uvMap=None):
        if not uvMap:
            uvMap = defaultUvMap
        o = self.obj
        # create a new UV map if necessary
        if not uvMap in o:
            o.data.uv_textures.new(uvMap)
        
        bm = getBmesh(o)
        # the inital loop
        _loop = self.getInitialLoop(bm)
        # find the open end if the finish sequence isn't a closed sequence
        loop = _loop
        vert = loop.vert
        while True:
            if len(vert.link_loops) == 1:
                # found the open end
                _loop = loop
                break
            loop = (vert.link_loops[1] if vert.link_loops[0] == loop else vert.link_loops[0]).link_loop_prev
            vert = loop.vert
            if loop == _loop:
                break
        
        # finally, assign UV coordinates
        layer = bm.loops.layers.uv[uvMap]
        # the layer for vertex groups
        groupLayer = bm.verts.layers.deform[0]
        h = getLevelHeight(self.context, o)
        offsetU = 0.
        loop = _loop
        vert = loop.vert
        e1 = getControlEmptyFromLoop(loop, groupLayer, o)
        while True:
            # remember the base loop
            _vert = vert
            # remember, we are dealing with rectangles
            # left bottom
            loop[layer].uv = (offsetU, 0.)
            # left top
            loop.link_loop_prev[layer].uv = (offsetU, h)
            # right bottom
            loop = loop.link_loop_next
            e2 = getControlEmptyFromLoop(loop, groupLayer, o)
            offsetU += (e2.location - e1.location).length
            loop[layer].uv = (offsetU, 0.)
            # right top
            loop.link_loop_next[layer].uv = (offsetU, h)
            
            # the step below isn't necessary, we already came to the required loop
            #loop = loop.link_loop_next
            vert = loop.vert
            if len(vert.link_loops) == 1:
                # reached the opposite end (end if the finish sequence isn't a closed sequence)
                break
            loop = vert.link_loops[1] if vert.link_loops[0] == loop else vert.link_loops[0]
            if loop == _loop:
                break
            e1 = e2
        setBmesh(o, bm)
    
    def getInitialLoop(self, bm):
        # find the first occurrence of a number in the names of vertex groups
        for g in self.obj.vertex_groups:
            g = g.name
            if g.isdigit():
                break
        # getting bottom <vb> and top <vt> vertices
        vb, vt = getVertsForVertexGroup(self.obj, bm, g)
        if vb.co.z > vt.co.z:
            vb, vt = vt, vb
        if len(vb.link_loops) == 1:
            # <vb> and <vt> are located at an open end of the finish
            loop1 = vb.link_loops[0]
        else: # len(vb.link_loops) == 2
            loop1, loop2 = vb.link_loops
            # ensure that loop1 goes horizontally
            if loop1.link_loop_next.vert == vt:
                loop1 = loop2
        return loop1
    

pContext.register(FinFlat, GuiFinish)