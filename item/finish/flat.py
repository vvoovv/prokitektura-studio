import bpy, bmesh
from base.item import Item
from base import zAxis, getLevelHeight, getNextLevelParent, getReferencesForAttached
from util.blender import createMeshObject, getBmesh, assignGroupToVerts,\
    addHookModifier, addSolidifyModifier, addBooleanModifier, parent_set


class FinFlat(Item):
    
    def createFromArea(self, area):
        context = self.context
        controls = area.getControls()
        
        obj = createMeshObject(area.obj.name+"_finish")
        obj["t"] = "fin"
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
        bm.to_mesh(obj.data)
        bm.free()
        
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
        # build a list of EMPTYs that defines each wall part that forms the finish
        walls = []
        _c = controls[-1]
        for c in controls:
            # consider the wall part defined by <_c> and <c>
            
            if _c["t"] == "wc":
                if c["t"] == "wc":
                    # both <_c> and <c> are corner EMPTYs
                    _o = _c
                    o = c
                else:
                    # <c> is attached
                    # choose <o> depending on if <_c> and <c> belong to the same wall part
                    if _c["m"] == c["m"]:
                        _o = _c
                        o = c
                    else:
                        _o, o = getReferencesForAttached(c)
            elif c["t"] == "wc":
                # <_c> is attached
                # choose <_o> depending on if <_c> and <c> belong to the same wall part
                if _c["m"] == c["m"]:
                    _o = _c
                    o = c
                else:
                    _o, o = getReferencesForAttached(_c)
            else:
                # both <_c> and <c> are attached EMPTYs
                _m_self = _c["m"]
                _m_base = getReferencesForAttached(_c)[0]["m"]
                m_self = c["m"]
                m_base = getReferencesForAttached(c)[0]["m"]
                
                if _m_self == m_self and (("p" in c and c["p"] == _c["g"]) or ("n" in c and c["n"] == _c["g"])):
                    _o = _c
                    o = c
                elif _m_base == m_base:
                    _o, o = getReferencesForAttached(c)
                elif _m_base == m_self:
                    _o, o = getReferencesForAttached(_c)
                else: # _m_self == m_base
                    _o, o = getReferencesForAttached(c)
            
            # ensure that <o2> follows <o1>
            if "n" in o and o["n"] == _o["g"]:
                o = _o
            walls.append(o)
            _c = c
        
        # iterate through immediate children of parent object of the finish
        for o in self.obj.parent.children:
            if "t" in o and (o["t"] == "window" or o["t"] == "door"):
                # find envelop
                for p in o.children:
                    if "t" in p and p["t"]=="env":
                        addBooleanModifier(self.obj, p.name, p)
    
    def assignUv(self):
        pass