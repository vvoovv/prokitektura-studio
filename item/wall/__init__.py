import bmesh
from base import pContext, getLevelLocation, getLevelZ, getModelParent, xAxis, yAxis, zAxis, zero, getReferencesForAttached
from base.item import Item
from util.blender import *


def getWallFromEmpty(context, op, empty, end=False):
    # The end==True means empty must be at either open end of the wall
    # check validity of empty
    if not (empty and empty.type == "EMPTY" and (not end or ("e" in empty and not "al" in empty))):
        return None
    wall = Wall(context, op)
    wall.init(empty)
    return wall


def addSegmentDrivers(e, e0, e1):
    # add driver for empty.location.x
    x = e.driver_add("location", 0)
    # x0
    addTransformsVariable(x, "x0", e0, "LOC_X")
    # x1
    addTransformsVariable(x, "x1", e1, "LOC_X")
    # expression
    x.driver.expression = "(x0+x1)/2."
    
    # add driver for empty.location.y
    y = e.driver_add("location", 1)
    # y0
    addTransformsVariable(y, "y0", e0, "LOC_Y")
    # y1
    addTransformsVariable(y, "y1", e1, "LOC_Y")
    # expression
    y.driver.expression = "(y0+y1)/2."


def addAttachedDrivers(wallAttached, o1, o2, e1, e2, both=True):
    """
    Add drivers for the end <o1> of <wallAttached> that is attached to a wall segment cotrolled by <e1> and <e2>.

    Args:
        wallAttached (Wall): The attached wall
        o1: The attached end of <wallAttached> is controlled by <o1>
        o2: The next or the previous corner EMPTY of <o1>
        e1: The wall segment to which <o1> is attached is contolled by corner EMPTYs <e1> and <e2>
        e2: The wall segment to which <o1> is attached is contolled by corner EMPTYs <e1> and <e2>
        both (bool): Add drivers also for the neighbor of <o1>
    """
    # neighbor of <o1>
    _o1 = wallAttached.getNeighbor(o1)
    end = o1["e"]
    # delete corner drivers
    o1.driver_remove("location")
    if both:
        _o1.driver_remove("location")
    
    # Create drivers that keep <o1> always located on the wall segment defined by <e1> and <e2> and
    # that keep distance between <e1> and <o1> constant
    
    #
    # <o1>
    #
    # distance between <e1> and <o1>
    l = (o1.location-e1.location).length
    # x
    x = o1.driver_add("location", 0)
    addTransformsVariable(x, "x1", e1, "LOC_X")
    addTransformsVariable(x, "x2", e2, "LOC_X")
    addLocDiffVariable(x, "d", e1, e2)
    x.driver.expression = "x1+" + str(l) + "*(x2-x1)/max(d,0.001)"
    # y
    y = o1.driver_add("location", 1)
    addTransformsVariable(y, "y1", e1, "LOC_Y")
    addTransformsVariable(y, "y2", e2, "LOC_Y")
    addLocDiffVariable(y, "d", e1, e2)
    y.driver.expression = "y1+" + str(l) + "*(y2-y1)/max(d,0.001)"
    
    if both:
        #
        # <_o1>
        #
        left = o1["l"]
        end = o1["e"]
        sign = "+" if (left and not end) or (not left and end) else "-"
        # x
        x = _o1.driver_add("location", 0)
        addTransformsVariable(x, "o1x", o1, "LOC_X")
        addTransformsVariable(x, "o2x", o2, "LOC_X")
        addTransformsVariable(x, "o1y", o1, "LOC_Y")
        addTransformsVariable(x, "o2y", o2, "LOC_Y")
        addLocDiffVariable(x, "do", o1, o2)
        addTransformsVariable(x, "e1x", e1, "LOC_X")
        addTransformsVariable(x, "e2x", e2, "LOC_X")
        addTransformsVariable(x, "e1y", e1, "LOC_Y")
        addTransformsVariable(x, "e2y", e2, "LOC_Y")
        addSinglePropVariable(x, "w", o1 if end else o2, "[\"w\"]")
        x.driver.expression = "o1x"+sign+"w*do*(e2x-e1x)/( (o2y-o1y)*(e2x-e1x)+(o1x-o2x)*(e2y-e1y) )"
        # y
        y = _o1.driver_add("location", 1)
        addTransformsVariable(y, "o1x", o1, "LOC_X")
        addTransformsVariable(y, "o2x", o2, "LOC_X")
        addTransformsVariable(y, "o1y", o1, "LOC_Y")
        addTransformsVariable(y, "o2y", o2, "LOC_Y")
        addLocDiffVariable(y, "do", o1, o2)
        addTransformsVariable(y, "e1x", e1, "LOC_X")
        addTransformsVariable(y, "e2x", e2, "LOC_X")
        addTransformsVariable(y, "e1y", e1, "LOC_Y")
        addTransformsVariable(y, "e2y", e2, "LOC_Y")
        addSinglePropVariable(y, "w", o1 if end else o2, "[\"w\"]")
        y.driver.expression = "o1y"+sign+"w*do*(e2y-e1y)/( (o2y-o1y)*(e2x-e1x)+(o1x-o2x)*(e2y-e1y) )"


def getFaceFortVerts(verts1, verts2):
    # find the common face for both verts1 and verts2
    for face in verts1[0].link_faces:
        if face in verts2[0].link_faces and face in verts2[1].link_faces:
            return face


def getWidth(self):
    """Returns the width of the wall segment defined by an active segment EMPTY"""
    context = bpy.context
    o = context.scene.objects.active
    return getWallFromEmpty(context, None, o).getWidth(o)


def setWidth(self, value):
    """Sets the width for the wall segment defined by an active segment EMPTY"""
    context = bpy.context
    o = context.scene.objects.active
    wall = getWallFromEmpty(context, None, o)
    if context.scene.prk.widthForAllSegments:
        closed = wall.isClosed()
        if closed:
            o = wall.getCornerEmpty(o)
            e = o
        else:
            e = wall.getStart(o["l"])
        while True:
            wall.setWidth(e, value)
            e = wall.getNext(e)
            if (closed and e == o) or (not closed and e is None):
                break
    else:
        wall.setWidth(o, value)


def getLength(self):
    """Returns the length of the wall segment defined by an active segment EMPTY"""
    context = bpy.context
    o = context.scene.objects.active
    return getWallFromEmpty(context, None, o).getLength(o)


def setLength(self, value):
    """Sets the length for the wall segment defined by an active segment EMPTY"""
    context = bpy.context
    o = context.scene.objects.active
    getWallFromEmpty(context, None, o).setLength(o, value)


class GuiWall:
    
    def draw(self, context, layout):
        o = context.scene.objects.active
        
        layout.operator("prk.area_make")
        
        layout.separator()
        layout.operator("prk.add_window")
        layout.operator("prk.add_door")
        
        layout.operator("prk.wall_flip_controls")
        if o["t"] == "ws" or o["t"] == "wc" or o["t"] == "wa":
            prk = context.scene.prk
            box = layout.box()
            box.prop(prk, "widthForAllSegments")
            box.prop(prk, "wallSegmentWidth")
            layout.prop(prk, "wallSegmentLength")


class Wall(Item):
    
    type = "wall"
    
    name = "Wall"
    
    emptyPropsCorner = {'empty_draw_type':'CUBE', 'empty_draw_size':0.02}
    emptyPropsSegment = {'empty_draw_type':'SPHERE', 'empty_draw_size':0.05}
    emptyPropsLevel = {'empty_draw_type':'PLAIN_AXES', 'empty_draw_size':0.05, 'lock_location':(True, True, False)}
    
    def __init__(self, context, op):
        super().__init__(context, op)
        # self.inheritLevelFrom indicates if need to inherit the level height and
        # the level z-position from the given EMPTY or take it from GUI
        self.inheritLevelFrom = None
    
    def init(self, o):
        if o["t"] == self.type:
            # <o> is the parent object for all wall parts, so it can be moved freely
            self.moveFreely = True
        else:
            parent = o.parent
            self.parent = parent.parent
            meshIndex = o["m"]
            # get mesh object
            for obj in parent.children:
                if "t" in obj and obj["t"] == "wall_part" and obj["m"] == meshIndex:
                    self.mesh = obj
                    break
            # check if have external or internal wall part
            self.external = True if "co" in parent and parent["co"] else False
    
    def create(self, locEnd=None):
        from mathutils import Vector
        
        context = self.context
        prk = context.scene.prk
        op = self.op
        
        # check if we have a parent for the whole model
        parent = getModelParent(context)
        
        loc = getLevelLocation(context)
        
        external = prk.newWallType == "external"
        self.external = external
        
        h = self.getHeight()
        w = prk.newWallWidth
        
        # the initial wall segment is oriented along Y-axis by default
        alongX = False
        # check if the initial wall segment should be oriented along X-axis or along Y-axis
        if locEnd:
            if parent:
                # convert to the coordinate system of <parent>
                matrix = parent.matrix_world.inverted()
                locEnd = matrix * locEnd
                loc = matrix * loc
            dx = locEnd.x-loc.x
            dy = locEnd.y-loc.y
            if abs(dx) > abs(dy):
                alongX = True
                l = dx
            else:
                l = dy
        else:
            l = op.length
            
        atRight = prk.wallAtRight
        
        if parent:
            counter = parent["counter"] + 1
            group0 = str(counter)
            group1 = str(counter+1)
            meshIndex = counter+2
        else:
            # parent one vert mesh
            parent = createOneVertObject("Model", loc)
            loc = Vector((0., 0., 0.))
            # type
            parent["t"] = "model"
            parent["container"] = 1
            parent.dupli_type = "VERTS"
            parent.hide_select = True
            group0 = "0"
            group1 = "1"
            meshIndex = 2
        
        self.parent = parent
        
        parent["counter"] = meshIndex
        obj = createMeshObject("wall_part")
        obj["t"] = "wall_part"
        obj["start"] = group0
        obj["end"] = group1
        obj["m"] = meshIndex
        obj.hide_select = True
        
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        # verts
        if atRight:
            v = [
                (0., 0., 0.), (0., -w, 0.), (l, -w, 0.), (l, 0., 0.),
                (0., 0., h), (0., -w, h), (l, -w, h), (l, 0., h)
            ] if alongX else [
                (0., 0., 0.), (w, 0., 0.), (w, l, 0.), (0, l, 0.),
                (0., 0., h), (w, 0., h), (w, l, h), (0., l, h)
            ]
        else:
            v = [
                (0., 0., 0.), (l, 0., 0.), (l, w, 0.), (0., w, 0.),
                (0., 0., h), (l, 0., h), (l, w, h), (0., w, h)
            ] if alongX else [
                (0., 0., 0.), (0., l, 0.), (-w, l, 0.), (-w, 0., 0.),
                (0., 0., h), (0., l, h), (-w, l, h), (-w, 0., h)
            ]
        
        # create verts
        for i in range(len(v)):
            v[i] = bm.verts.new(loc+Vector(v[i]))
        
        # create faces
        # bottom face
        bm.faces.new((v[0], v[3], v[2], v[1]))
        # top face
        bm.faces.new((v[4], v[5], v[6], v[7]))
        # left face
        bm.faces.new((v[0], v[4], v[7], v[3]))
        # right face
        bm.faces.new((v[1], v[2], v[6], v[5]))
        # front face
        bm.faces.new((v[0], v[1], v[5], v[4]))
        # back face
        bm.faces.new((v[3], v[7], v[6], v[2]))
        
        # assign vertex group for the top face
        assignGroupToVerts(obj, layer, "t", v[4], v[5], v[6], v[7])
        
        # assign vertex groups for each vertical wall edge
        if atRight:
            # for the wall origin
            assignGroupToVerts(obj, layer, "l"+group0, v[0], v[4])
            assignGroupToVerts(obj, layer, "r"+group0, v[1], v[5])
            # for the wall end
            assignGroupToVerts(obj, layer, "l"+group1, v[3], v[7])
            assignGroupToVerts(obj, layer, "r"+group1, v[2], v[6])
        else:
            # for the wall origin
            assignGroupToVerts(obj, layer, "l"+group0, v[3], v[7])
            assignGroupToVerts(obj, layer, "r"+group0, v[0], v[4])
            # for the wall end
            assignGroupToVerts(obj, layer, "l"+group1, v[2], v[6])
            assignGroupToVerts(obj, layer, "r"+group1, v[1], v[5])
        
        bm.to_mesh(obj.data)
        bm.free()
        
        # l means left
        # e means end: e==0 for the start, e==1 for the end
        # n means next
        # p means previous
        # g means group to identify the related modifier and vertex group
        # w means width
        # m means mesh index
        # al (for an attached wall only) informs if the wall is attached to the left (1) or to the right (0)
        if atRight:
            l0 = self.createCornerEmptyObject("l"+group0, loc, False)
            r0 = self.createCornerEmptyObject("r"+group0, loc + Vector((0., -w, 0.) if alongX else (w, 0., 0.)), True)
            l1 = self.createCornerEmptyObject("l"+group1, loc + Vector((l, 0., 0.) if alongX else (0., l, 0.)), False)
            r1 = self.createCornerEmptyObject("r"+group1, loc + Vector((l, -w, 0.) if alongX else (w, l, 0.)), True)
        else:
            l0 = self.createCornerEmptyObject("l"+group0, loc + Vector((0., w, 0.) if alongX else (-w, 0., 0.)), True)
            r0 = self.createCornerEmptyObject("r"+group0, loc, False)
            l1 = self.createCornerEmptyObject("l"+group1, loc + Vector((l, w, 0.) if alongX else (-w, l, 0.)), True)
            r1 = self.createCornerEmptyObject("r"+group1, loc + Vector((l, 0., 0.) if alongX else (0., l, 0.)), False)
        
        setCustomAttributes(l0, l=1, e=0, g=group0, w=w, n=group1, m=meshIndex)
        setCustomAttributes(r0, l=0, e=0, g=group0, w=w, n=group1, m=meshIndex)
        setCustomAttributes(l1, l=1, e=1, g=group1, w=w, p=group0, m=meshIndex)
        setCustomAttributes(r1, l=0, e=1, g=group1, w=w, p=group0, m=meshIndex)
        
        # without scene.update() parenting and hook modifiers will not work correctly
        context.scene.update()
        
        # perform parenting
        directParent = self.parent_set(obj, l0, r0, l1, r1)
        # without scene.update() parenting and hook modifiers will not work correctly
        # this step is probably optional here, however it's required in self.extend(..)
        context.scene.update()
        
        # add a HOOK modifier controlling the wall height
        addHookModifier(obj, "t",
            self.getTotalHeightEmpty() if (external or prk.levelIndex == len(prk.levels)-1) else self.getLevelParent(1),
            "t"
        )
        # add hook modifiers
        addHookModifier(obj, "l"+group0, l0, "l"+group0)
        addHookModifier(obj, "r"+group0, r0, "r"+group0)
        addHookModifier(obj, "l"+group1, l1, "l"+group1)
        addHookModifier(obj, "r"+group1, r1, "r"+group1)
        
        # add drivers
        if atRight:
            self.addEndEdgeDrivers(r0, l0, l1, False, atRight)
            self.addEndEdgeDrivers(r1, l0, l1, True, atRight)
        else:
            self.addEndEdgeDrivers(l0, r0, r1, False, atRight)
            self.addEndEdgeDrivers(l1, r0, r1, True, atRight)
            
        # create Blender EMPTY objects for the initial wall segment:
        _l = self.createSegmentEmptyObject(l0, l1, directParent, False if atRight else True)
        _r = self.createSegmentEmptyObject(r0, r1, directParent, True if atRight else False)
        setCustomAttributes(_l, l=1, m=meshIndex)
        setCustomAttributes(_r, l=0, m=meshIndex)
        
        bpy.ops.object.select_all(action="DESELECT")
        makeActiveSelected(context, l1 if atRight else r1)
        
        return (alongX, not alongX, False)
    
    def extend(self, o, locEnd = None):
        if locEnd:
            # convert the end location to the coordinate system of the wall
            locEnd = self.parent.matrix_world.inverted() * locEnd
        
        op = self.op
        # are we at the end (1) or at the start (0)
        end = o["e"]
        left = o["l"]
        condition = (left and end) or (not left and not end)
        # the width of the new wall segment
        w = o["w"]
        
        # Will the wall be extended the left side (True) or on the right one (False)
        # relative to the original wall segment? This is defined by relative position of the mouse
        # and the original wall segment.
        _v = (self.getPrevious(o) if end else o).location
        v = (o if end else self.getNext(o)).location
        # vector along the current wall segment
        u = (v - _v).normalized()
        extendLeft = True if u.cross(locEnd - _v)[2]>=0 else False
        
        # normal to the current wall segment in the direction of the new wall segment to be extended
        n = ( zAxis.cross(u) if extendLeft else u.cross(zAxis) ).normalized()
        # Normal with the length equal to the length of the new wall segment to be extended
        # The length is defined by locEnd
        N = (n.dot(locEnd-_v) if locEnd else op.length)*n
        
        p1 = o.location + N
        # normal to the line between empty1.location and p1
        n = n.cross(zAxis) if condition else zAxis.cross(n)
        p2 = p1 + w*n
        e1, e2 = self.createExtension(o, p1, p2)
        
        # add drivers
        if end:
            self.addEndEdgeDrivers(e2, o, e1, True, left)
        else:
            self.addEndEdgeDrivers(e2, e1, o, False, left)
        
        return e1
    
    def createExtension(self, o1, p1, p2):
        self.inheritLevelFrom = o1
        
        o2 = self.getNeighbor(o1)
        
        context = self.context
        parent = self.parent
        mesh = self.mesh
        meshIndex = mesh["m"]
        h = self.getHeight()
        counter = parent["counter"] + 1
        group = str(counter)
        
        # We have to apply the HOOK modifier that controls the level height,
        # otherwise the height of the extension will not be equal to the height of
        # the rest of the wall if the height was changed before
        # Remember the Blender EMPTY object controlling the height of the level
        hEmpty = mesh.modifiers["t"].object
        modifier_apply(mesh, "t") 
        
        bm = getBmesh(mesh)
        # All vertex groups are in the deform layer.
        # There can be only one deform layer
        layer = bm.verts.layers.deform[0]
        
        # the width of the new wall segment
        w = o1["w"]
        # are we at the end (1) or at the start (0)
        end = o1["e"]
        left = o1["l"]
        condition = (left and end) or (not left and not end)
        
        prefix1 = "l" if left else "r"
        group1 = prefix1 + group
        # prefix for the neighbor verts located to the left or to the right
        prefix2 = "r" if left else "l"
        group2 = prefix2 + group
        # delete the face at the open end of the wall, defined by the related vertex groups
        verts1 = self.getVertsForVertexGroup(bm, prefix1+o1["g"])
        verts2 = self.getVertsForVertexGroup(bm, prefix2+o1["g"])
        bmesh.ops.delete(
            bm,
            geom=(getFaceFortVerts(verts1, verts2),),
            context=3
        )
        
        # <e1>: extension of <o1>
        e1 = self.createCornerEmptyObject(group1, p1, False)
        setCustomAttributes(e1, l=1 if left else 0, e=end, g=group, w=w, m=meshIndex)
        if end:
            setCustomAttributes(e1, p=o1["g"])
            setCustomAttributes(o1, n=group)
        else:
            setCustomAttributes(e1, n=o1["g"])
            setCustomAttributes(o1, p=group)
        del o1["e"]
        # create also the accompanying verts
        v1_1 = bm.verts.new(p1)
        v1_2 = bm.verts.new(p1 + h*zAxis)
        
        # <e2>: extension of <o2>, neighbor of <e1>
        e2 = self.createCornerEmptyObject(group2, p2, True)
        setCustomAttributes(e2, l=0 if left else 1, e=end, g=group, w=w, m=meshIndex)
        if end:
            setCustomAttributes(e2, p=o1["g"])
            setCustomAttributes(o2, n=group)
        else:
            setCustomAttributes(e2, n=o1["g"])
            setCustomAttributes(o2, p=group)
        del o2["e"]
        # create also the accompanying verts
        v2_1 = bm.verts.new(e2.location)
        v2_2 = bm.verts.new(v2_1.co + h*zAxis)
        
        if end:
            self.addInternalEdgeDrivers(o2, self.getPrevious(o1), o1, e1, 1, left)
        else:
            self.addInternalEdgeDrivers(o2, e1, o1, self.getNext(o1), 0, left)
        
        # create all necessary faces
        bm.faces.new( (verts1[0], verts1[1], v1_2, v1_1) if condition else (v1_1, v1_2, verts1[1], verts1[0]) )
        bm.faces.new( (v1_1, v1_2, v2_2, v2_1) if condition else (v2_1, v2_2, v1_2, v1_1) )
        bm.faces.new((v2_1, v2_2, verts2[1], verts2[0]) if condition else (verts2[0], verts2[1], v2_2, v2_1) )
        bm.faces.new((verts1[1], verts2[1], v2_2, v1_2) if condition else (v1_2, v2_2, verts2[1], verts1[1]) )
        bm.faces.new((v1_1, v2_1, verts2[0], verts1[0]) if condition else (verts1[0], verts2[0], v2_1, v1_1) )
        
        # assign vertex group for the verices located at the top
        assignGroupToVerts(mesh, layer, "t", v1_2, v2_2)
        # assign vertex group for for each new vertical wall edge
        assignGroupToVerts(mesh, layer, group1, v1_1, v1_2)
        assignGroupToVerts(mesh, layer, group2, v2_1, v2_2)
        
        parent["counter"] = counter
        if end:
            mesh["end"] = group
        else:
            mesh["start"] = group
        bm.to_mesh(mesh.data)
        bm.free()
        
        # without scene.update() parenting and hook modifiers will not work correctly
        # this step is probably optional here, however it's required in self.create()
        context.scene.update()
        
        # perform parenting
        directParent = self.parent_set(e1, e2)
        
        # without scene.update() parenting and hook modifiers will not work correctly
        context.scene.update()
        
        # add HOOK modifier controlling the top vertices (i.e the height of the level)
        addHookModifier(mesh, "t", hEmpty, "t")
        # add HOOK modifiers
        addHookModifier(mesh, group1, e1, group1)
        addHookModifier(mesh, group2, e2, group2)
        
        # create Blender EMPTY objects for the just created wall segment:
        if end:
            s1 = self.createSegmentEmptyObject(o1, e1, directParent, False)
            s2 = self.createSegmentEmptyObject(o2, e2, directParent, True)
        else:
            s1 = self.createSegmentEmptyObject(e1, o1, directParent, False)
            s2 = self.createSegmentEmptyObject(e2, o2, directParent, True)
        setCustomAttributes(s1, m=meshIndex)
        setCustomAttributes(s2, m=meshIndex)
        
        return e1, e2
    
    def createAttachment(self, verts, attachLeft, freeEnd):
        context = self.context
        parent = self.parent
        prk = context.scene.prk
        w = prk.newWallWidth
        atRight = prk.wallAtRight
        
        counter = parent["counter"] + 1
        group0 = str(counter)
        group1 = str(counter+1)
        
        obj = createMeshObject("wall_part")
        obj["t"] = "wall_part"
        meshIndex = counter+2
        obj["m"] = meshIndex
        obj["start"] = group0
        obj["end"] = group1
        obj.hide_select = True
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        l0 = self.createAttachedEmptyObject("l"+group0, verts[0] if attachLeft else verts[1], False if atRight else True)
        r0 = self.createAttachedEmptyObject("r"+group0, verts[1] if attachLeft else verts[0], True if atRight else False)
        if freeEnd:
            l1 = self.createCornerEmptyObject("l"+group1, verts[3] if attachLeft else verts[2], False if atRight else True)
            r1 = self.createCornerEmptyObject("r"+group1, verts[2] if attachLeft else verts[3], True if atRight else False)
        else:
            l1 = self.createAttachedEmptyObject("l"+group1, verts[3] if attachLeft else verts[2], False if atRight else True)
            r1 = self.createAttachedEmptyObject("r"+group1, verts[2] if attachLeft else verts[3], True if atRight else False)
        
        setCustomAttributes(l0, l=1, e=0, g=group0, w=w, n=group1, m=meshIndex, al=1 if attachLeft else 0)
        setCustomAttributes(r0, l=0, e=0, g=group0, w=w, n=group1, m=meshIndex, al=1 if attachLeft else 0)
        setCustomAttributes(l1, l=1, e=1, g=group1, w=w, p=group0, m=meshIndex)
        setCustomAttributes(r1, l=0, e=1, g=group1, w=w, p=group0, m=meshIndex)
        
        for i in range(len(verts)):
            verts[i] = bm.verts.new(verts[i])
        
        # bottom
        bm.faces.new( (verts[0], verts[3], verts[2], verts[1]) if attachLeft else (verts[1], verts[2], verts[3], verts[0]) )
        # top
        bm.faces.new( (verts[5], verts[6], verts[7], verts[4]) if attachLeft else (verts[4], verts[7], verts[6], verts[5]) )
        # front
        bm.faces.new( (verts[0], verts[4], verts[7], verts[3]) if attachLeft else (verts[0], verts[3], verts[7], verts[4]) )
        # back
        bm.faces.new( (verts[1], verts[2], verts[6], verts[5]) if attachLeft else (verts[1], verts[5], verts[6], verts[2]) )
        # left
        bm.faces.new( (verts[3], verts[7], verts[6], verts[2]) if attachLeft else (verts[0], verts[4], verts[5], verts[1]) )
        # right
        bm.faces.new( (verts[1], verts[5], verts[4], verts[0]) if attachLeft else (verts[2], verts[6], verts[7], verts[3]) )
        
        # assign vertex group for the top face
        assignGroupToVerts(obj, layer, "t", verts[5], verts[6], verts[7], verts[4])
        # assign vertex groups for each vertical wall edge
        # for the wall origin
        assignGroupToVerts(obj, layer, "l"+group0, *((verts[0], verts[4]) if attachLeft else (verts[1], verts[5])) )
        assignGroupToVerts(obj, layer, "r"+group0, *((verts[1], verts[5]) if attachLeft else (verts[0], verts[4])) )
        # for the wall end
        assignGroupToVerts(obj, layer, "l"+group1, *((verts[3], verts[7]) if attachLeft else (verts[2], verts[6])) )
        assignGroupToVerts(obj, layer, "r"+group1, *((verts[2], verts[6]) if attachLeft else (verts[3], verts[7])) )
        
        parent["counter"] = meshIndex

        bm.to_mesh(obj.data)
        bm.free()
        
        context.scene.update()
        # perform parenting
        directParent = self.parent_set(obj, l0, r0, l1, r1)
        # add a HOOK modifier controlling the wall height
        addHookModifier(obj, "t",
            self.getTotalHeightEmpty() \
            if (
                self.external or
                (self.inheritLevelFrom and self.inheritLevelFrom.parent["level"]==prk.levels[-1].index) or
                (not self.inheritLevelFrom and prk.levelIndex == len(prk.levels)-1)
            ) \
            else self.getLevelParent(1),
            "t"
        )
        context.scene.update()
        
        # add hook modifiers
        addHookModifier(obj, "l"+group0, l0, "l"+group0)
        addHookModifier(obj, "r"+group0, r0, "r"+group0)
        addHookModifier(obj, "l"+group1, l1, "l"+group1)
        addHookModifier(obj, "r"+group1, r1, "r"+group1)
        
        # add drivers
        if freeEnd:
            if atRight:
                self.addEndEdgeDrivers(r0, l0, l1, False, atRight)
                self.addEndEdgeDrivers(r1, l0, l1, True, atRight)
            else:
                self.addEndEdgeDrivers(l0, r0, r1, False, atRight)
                self.addEndEdgeDrivers(l1, r0, r1, True, atRight)
            
        # create Blender EMPTY objects for the attached wall segment:
        lEmpty = self.createSegmentEmptyObject(l0, l1, directParent, False if atRight else True)
        rEmpty = self.createSegmentEmptyObject(r0, r1, directParent, True if atRight else False)
        setCustomAttributes(lEmpty, m=meshIndex)
        setCustomAttributes(rEmpty, m=meshIndex)
        
        return (l0, lEmpty, l1) if atRight else (r0, rEmpty, r1)
    
    def complete(self, left):
        mesh = self.mesh
        meshIndex = mesh["m"]
        start = self.getStart(left)
        end = self.getEnd(left)
        
        bm = getBmesh(mesh)
        
        prefix1 = "l" if left else "r"
        # prefix for the neighbor verts located to the left or to the right
        prefix2 = "r" if left else "l"
        
        # delete the faces at the open ends of the wall, defined by the related vertex groups
        # for empty1
        verts1_1 = self.getVertsForVertexGroup(bm, prefix1+start["g"])
        verts1_2 = self.getVertsForVertexGroup(bm, prefix2+start["g"])
        # for empty2
        verts2_1 = self.getVertsForVertexGroup(bm, prefix1+end["g"])
        verts2_2 = self.getVertsForVertexGroup(bm, prefix2+end["g"])
        bmesh.ops.delete(
            bm,
            geom=( getFaceFortVerts(verts1_1, verts1_2), getFaceFortVerts(verts2_1, verts2_2) ),
            context=3
        )
        
        # create faces
        # top and bottom
        bm.faces.new((verts2_1[1], verts2_2[1], verts1_2[1], verts1_1[1]) if left else (verts1_1[1], verts1_2[1], verts2_2[1], verts2_1[1]))
        bm.faces.new((verts1_1[0], verts1_2[0], verts2_2[0], verts2_1[0]) if left else (verts2_1[0], verts2_2[0], verts1_2[0], verts1_1[0]))
        # front and back
        bm.faces.new((verts2_1[0], verts2_1[1], verts1_1[1], verts1_1[0]) if left else (verts1_1[0], verts1_1[1], verts2_1[1], verts2_1[0]))
        bm.faces.new((verts1_2[0], verts1_2[1], verts2_2[1], verts2_2[0]) if left else (verts2_2[0], verts2_2[1], verts1_2[1], verts1_2[0]))
        
        end["n"] = start["g"]
        start["p"] = end["g"]
        del start["e"], end["e"], mesh["start"], mesh["end"]
        
        bm.to_mesh(self.mesh.data)
        bm.free()
        
        # without scene.update() parenting and hook modifiers will not work correctly
        self.context.scene.update()
        
        self.addInternalEdgeDrivers(self.getNeighbor(start), end, start, self.getNext(start), 0, left)
        self.addInternalEdgeDrivers(self.getNeighbor(end), self.getPrevious(end), end, start, 1, left)
        
        # update also attributes for the neighbors of start and end
        start = self.getNeighbor(start)
        end = self.getNeighbor(end)
        end["n"] = start["g"]
        start["p"] = end["g"]
        del start["e"], end["e"]
        
        # create segment EMPTYs for the just created wall segment
        s1 = self.createSegmentEmptyObject(end, start, mesh.parent, start.hide)
        s2 = self.createSegmentEmptyObject(self.getNeighbor(end), self.getNeighbor(start), mesh.parent, not start.hide)
        setCustomAttributes(s1, m=meshIndex)
        setCustomAttributes(s2, m=meshIndex)
    
    def flipControls(self, o):
        left = o["l"]
        
        # keep reference to the input EMPTY object
        _o = o 
        
        closed = self.isClosed()
        
        if not closed:
            start = self.getStart(left)
            end = self.getEnd(left)
            attached1 = self.getReferencesForAttached(start)
            attached2 = self.getReferencesForAttached(end)
        
        # 1) deal with corner empties
        o = self.getCornerEmpty(o)
        
        # remove drivers from the active side defined by left variable
        e = o if closed else self.getStart(left)
        while True:
            self.getNeighbor(e).driver_remove("location")
            hide_select(e, True)
            e = self.getNext(e)
            if (closed and e == o) or (not closed and e is None):
                break
        
        # add drivers for the currently inactive side
        if closed:
            left = not left
            m1 = self.getNeighbor(o)
            m0 = self.getPrevious(m1)
            m2 = self.getNext(m1)
            e = o
            while True:
                self.addInternalEdgeDrivers(e, m0, m1, m2, 1, left, False)
                hide_select(m1, False)
                e = self.getNext(e)
                if e == o:
                    break
                m0 = m1
                m1 = m2
                m2 = self.getNext(m2)
        else:
            hide_select(start, True)
            hide_select(end, True)
            m0 = self.getNeighbor(start)
            m1 = self.getNext(m0)
            m2 = self.getNext(m1)
            
            left = not left
            # start
            if attached1:
                addAttachedDrivers(self, m0, m1, attached1[0], attached1[1], True)
            else:
                self.addEndEdgeDrivers(start, m0, m1, False, left)
            hide_select(m0, False)
            # in-betweens
            if m2:
                e = self.getNext(start)
                while True:
                    self.addInternalEdgeDrivers(e, m0, m1, m2, 1, left, False)
                    hide_select(m1, False)
                    e = self.getNext(e)
                    if e == end:
                        break
                    m0 = m1
                    m1 = m2
                    m2 = self.getNext(m2)
            else:
                m1, m2 = m0, m1
            # end
            if attached2:
                addAttachedDrivers(self, m2, m1, attached2[0], attached2[1], True)
            else:
                self.addEndEdgeDrivers(end, m1, m2, True, left)
            hide_select(m2, False)
        
        # 2) deal with segment empties 
        o = _o
        meshIndex = o["m"]
        neighbor = None
        for obj in o.parent.children:
            if obj.type == "EMPTY" and "t" in obj and obj["t"]=="ws" and obj["m"]==meshIndex:
                hide_select(obj, False if obj["l"]==left else True)
                # find the neighbor of <o> if <o> is a segment EMPTY 
                if o["t"] == "ws" and not neighbor and obj["g"] == o["g"] and o!=obj:
                    neighbor = obj
        
        # select the neighbor of <o>
        o = neighbor if neighbor else self.getNeighbor(o)
        makeActiveSelected(self.context, o)
    
    def isAttached(self, o):
        """
        Returns True if <o> is attached to another wall segment or False otherwise
        """
        return o and "al" in o
            
    def getNeighbor(self, o):
        if o["t"] == "ws":
            # we have to iterate through all segment EMPTYs to find the neighbor
            for obj in self.parent.children:
                if obj.type == "EMPTY" and "t" in obj and obj["t"]=="ws" and obj["m"]==o["m"] and obj["g"] == o["g"] and obj["l"] != o["l"]:
                    return obj
        else:
            prefix = "r" if o["l"] else "l"
            return self.mesh.modifiers[prefix+o["g"]].object
    
    def getNext(self, o):
        if "e" in o and o["e"]:
            return None
        prefix = "l" if o["l"] else "r"
        return self.mesh.modifiers[prefix+o["n"]].object

    def getPrevious(self, o):
        if "e" in o and not o["e"]:
            return None
        prefix = "l" if o["l"] else "r"
        return self.mesh.modifiers[prefix+o["p"]].object
    
    def getStart(self, left=True):
        return None if self.isClosed() else self.getEmpty(self.mesh["start"], left)
        
    def getEnd(self, left=True):
        return None if self.isClosed() else self.getEmpty(self.mesh["end"], left)
    
    def getEmpty(self, group, left):
        prefix = "l" if left else "r"
        return self.mesh.modifiers[prefix+group].object
    
    def getCornerEmpty(self, o):
        if o["t"] == "ws":
            # get corner EMPTY object if the input was a segment EMPTY object
            o = self.getEmpty(o["g"], o["l"])
        return o
    
    def getReferencesForAttached(self, o):
        """
        Get reference EMPTYs for the wall segment to which <o> is attached.
        
        Returns:
            A tuple with corner EMPTYs or None it <o> isn't attached to a wall segment.
        """
        if not self.isAttached(o):
            return None
        return getReferencesForAttached(o)
    
    def isClosed(self):
        return not "end" in self.mesh
    
    def getWidth(self, o):
        return self.getCornerEmpty(o)["w"]
    
    def getLength(self, o):
        o2 = self.getCornerEmpty(o)
        # check if <o2> is at the start of a wall part
        if "e" in o2 and not o2["e"]:
            o2 = self.getNext(o2)
        o1 = self.getPrevious(o2)
        return (o2.location - o1.location).length
    
    def getHeight(self):
        """Get height of the wall to be created"""
        from base import getLevelHeight
        prk = self.context.scene.prk
        if not self.external:
            if self.inheritLevelFrom:
                return getLevelHeight(self.context, self.inheritLevelFrom)
            else:
                levelIndex = prk.levelIndex
        return self.getTotalHeight() \
            if self.external else \
            prk.levelBundles[prk.levels[levelIndex].bundle].height
    
    def getTotalHeight(self):
        prk = self.context.scene.prk
        return sum(prk.levelBundles[level.bundle].height for level in prk.levels)
    
    def setWidth(self, o, value):
        o = self.getCornerEmpty(o)
        o["w"] = value
        self.getNeighbor(o)["w"] = value
        # treat the special case when o is at the starting EMPTY or just after the starting EMPTY
        if not self.isClosed():
            if "e" in o and o["e"] == 0:
                # set the width for the next EMPTY
                o = self.getNext(o)
                o["w"] = value
                self.getNeighbor(o)["w"] = value
            else:
                # set the width for the starting EMPTY
                o = self.getPrevious(o)
                if "e" in o and o["e"] == 0:
                    o["w"] = value
                    self.getNeighbor(o)["w"] = value
        # a hack, without it the width of the related wall segment won't be updated
        o.location = o.location
    
    def setLength(self, o, value):
        o2 = self.getCornerEmpty(o)
        # check if <o2> is at the start of a wall part
        if "e" in o2 and not o2["e"]:
            o2 = self.getNext(o2)
        o1 = self.getPrevious(o2)
        # we can't set length for the attached wall segment
        if not self.isAttached(o2):
            o2.location = o1.location + value/(o2.location-o1.location).length*(o2.location-o1.location)
    
    def createCornerEmptyObject(self, name, location, hide):
        empty = createEmptyObject(name, location, hide, **self.emptyPropsCorner)
        empty.lock_location[2] = True
        # wc stands for "wall corner"
        empty["t"] = "wc"
        return empty
    
    def createSegmentEmptyObject(self, e0, e1, parent, hide):
        left = e1["l"]
        # the name is derived from e1
        empty = createEmptyObject(("sl" if left else "sr") + e1["g"], (e0.location + e1.location)/2, hide, **self.emptyPropsSegment)
        empty.lock_location[2] = True
        # ws stands for "wall segment"
        setCustomAttributes(empty, t="ws", l=left, g=e1["g"])
        parent_set(parent, empty)
        
        addSegmentDrivers(empty, e0, e1)
        
        return empty
    
    def createAttachedEmptyObject(self, name, location, hide):
        empty = createEmptyObject(name, location, hide, **self.emptyPropsCorner)
        empty.lock_location[2] = True
        # wa stands for "wall attached"
        empty["t"] = "wa"
        return empty
    
    def getVertsForVertexGroup(self, bm, group):
        """
        Gets verts for the vertex group and rearranges them if necessary
        """
        verts = getVertsForVertexGroup(self.mesh, bm, group)
        # rearrange verts if necessary
        if verts[0].co.z>verts[1].co.z:
            verts[0], verts[1] = verts[1], verts[0]
        
        return verts

    def addEndEdgeDrivers(self, slave, m0, m1, end, left, createExpression=True):
        """
        Adds drivers for an end vertical edge (a slave edge) of the wall
        
        Args:
            slave: A Blender empty object that controls the slave open vertical edge of the wall
            m0: A Blender empty object that defines the start of the master horizontal edge of the wall
            m1: A Blender empty object that defines the end of the master horizontal edge of the wall
            end (bool): Defines which of m0 (False) and m1 (True) controls the master open vertical edge of the wall
            left (bool): Defines if the slave is on the left side of the wall (True) or on the right one (False)
        """
        sign = "+" if left else "-"
        
        master = m1 if end else m0
        
        # add driver for slave.location.x
        x = slave.driver_add("location", 0)
        # x
        addTransformsVariable(x, "x", master, "LOC_X")
        # y0 or y1
        addTransformsVariable(x, "y0" if end else "y1", m0, "LOC_Y")
        # y1 or y2
        addTransformsVariable(x, "y1" if end else "y2", m1, "LOC_Y")
        # d1 or d2: distance between m0 and m1
        addLocDiffVariable(x, "d1" if end else "d2", m0, m1)
        # w1 or w2: width
        addSinglePropVariable(x, "w1" if end else "w2", m1, "[\"w\"]")
        # expression
        if createExpression:
            x.driver.expression = "x" +sign+ "w1*(y1-y0)/max(d1, 0.001)" if end else "x" +sign+ "w2*(y2-y1)/max(d2, 0.001)"
        
        # add driver for x slave.location.y
        y = slave.driver_add("location", 1)
        # y
        addTransformsVariable(y, "y", master, "LOC_Y")
        # x0 or x1
        addTransformsVariable(y, "x0" if end else "x1", m0, "LOC_X")
        # x1 or x2
        addTransformsVariable(y, "x1" if end else "x2", m1, "LOC_X")
        # d1 or d2: distance between m0 and m1
        addLocDiffVariable(y, "d1" if end else "d2", m0, m1)
        # w1 or w2: width
        addSinglePropVariable(y, "w1" if end else "w2", m1, "[\"w\"]")
        # expression
        if createExpression:
            y.driver.expression = "y" +sign+ "w1*(x0-x1)/max(d1, 0.001)" if end else "y" +sign+ "w2*(x1-x2)/max(d2, 0.001)"

    def addInternalEdgeDrivers(self, slave, m0, m1, m2, end, left, update=True):
        sign1 = "+" if left else "-"
        sign2 = "-" if left else "+"
        
        if not update:
            self.addEndEdgeDrivers(slave, m0, m1, end, left, False)
        
        # update the driver for slave.location.x
        x = slave.animation_data.drivers[0]
        # x0
        addTransformsVariable(x, "x0", m0, "LOC_X")
        # x1
        addTransformsVariable(x, "x1", m1, "LOC_X")
        # x2
        addTransformsVariable(x, "x2", m2, "LOC_X")
        # y2 or y0
        addTransformsVariable(x, "y2" if end else "y0", m2 if end else m0, "LOC_Y")
        # d2 or d1: distance between m1 and m2 or m1 and m0
        addLocDiffVariable(x, "d2" if end else "d1", m1, m2 if end else m0)
        # w2 or w1: width
        addSinglePropVariable(x, "w2" if end else "w1", m2 if end else m1, "[\"w\"]")
        # expression
        x.driver.expression = "x" +sign1+ "w2*(y2-y1)/max(d2,0.001)" +sign2+ "(w1-w2*((x1-x0)*(x2-x1)+(y1-y0)*(y2-y1))/max(d1,0.001)/max(d2,0.001)) * (x2-x1) * d1 / ((x1-x0)*(y2-y1)-(y1-y0)*(x2-x1) if abs((x1-x0)*(y2-y1)-(y1-y0)*(x2-x1))>0.001 else 0.001)"

        # update the driver for slave.location.y
        y = slave.animation_data.drivers[1]
        # x2 or x0
        addTransformsVariable(y, "x2" if end else "x0", m2 if end else m0, "LOC_X")
        # y0
        addTransformsVariable(y, "y0", m0, "LOC_Y")
        # y1
        addTransformsVariable(y, "y1", m1, "LOC_Y")
        # y2
        addTransformsVariable(y, "y2", m2, "LOC_Y")
        # d2 or d1: distance between m1 and m2 or m1 and m0
        addLocDiffVariable(y, "d2" if end else "d1", m1, m2 if end else m0)
        # w2 or w1: width
        addSinglePropVariable(y, "w2" if end else "w1", m2 if end else m1, "[\"w\"]")
        # expression
        y.driver.expression = "y" +sign1+ "w2*(x1-x2)/max(d2,0.001)" +sign2+ "(w1-w2*((x1-x0)*(x2-x1)+(y1-y0)*(y2-y1))/max(d1,0.001)/max(d2,0.001)) * (y2-y1) * d1 / ((x1-x0)*(y2-y1)-(y1-y0)*(x2-x1) if abs((x1-x0)*(y2-y1)-(y1-y0)*(x2-x1))>0.001 else 0.001)"
    
    def resetHookModifiers(self):
        objects = bpy.context.scene.objects
        mesh = self.mesh
        # keep a reference to the current active object
        active = objects.active
        objects.active = mesh
        # modifier index in the list of modifiers
        i = 0
        data = []
        for m in mesh.modifiers:
            if m.type == "HOOK":
                data.append((i, m.name, m.object))
                bpy.ops.object.modifier_apply(modifier=m.name)
            i += 1
        # recreate the modifiers and move them to the original position in the list of modifiers
        i = len(mesh.modifiers)
        for m in data:
            # add a modifier and keep in <m> tuple
            name = m[1]
            addHookModifier(mesh, name, m[2], name)
            for _ in range(m[0], i):
                bpy.ops.object.modifier_move_up(modifier=name)
            i += 1
        # restore the original active object
        objects.active = active
        
    def startAttachedWall(self, o, locEnd):
        context = self.context
        prk = context.scene.prk
        
        if self.external:
            if prk.newWallType == "internal":
                # override self.external
                self.external = False
        else:
            self.inheritLevelFrom = o
        
        locEnd.z = 0.
        # convert the end location to the coordinate system of the wall
        locEnd = self.parent.matrix_world.inverted() * locEnd
        o2 = self.getCornerEmpty(o)
        o1 = self.getPrevious(o2)
        # vector along the current wall segment
        u = (o2.location - o1.location).normalized()
        # Will the attached wall be located on the left side (True) or on the right one (False)
        # relative to the original wall segment? This is defined by relative position of the mouse
        # and the original wall segment.
        attachLeft = True if u.cross(locEnd - o1.location)[2]>=0 else False
        
        if (attachLeft and not o["l"]) or (not attachLeft and o["l"]):
            # the attached wall to be created can't cross the current wall segment!
            o1 = self.getNeighbor(o1)
            o2 = self.getNeighbor(o2)
        
        w = prk.newWallWidth
        h = self.getHeight()
        H = h*zAxis
        
        # normal to the current wall segment in the direction of the attached wall to be created
        n = ( zAxis.cross(u) if attachLeft else u.cross(zAxis) ).normalized()
        # normal with the length equal to the length of the attached wall defined by locEnd
        N = n.dot(locEnd-o1.location)*n
        # verts of the attached wall along the current wall segment
        u1 = 0.5*(o1.location + o2.location) - 0.5*w*u
        u2 = 0.5*(o1.location + o2.location) + 0.5*w*u
        verts = [
            u1, u2, u2+N, u1+N,
            u1+H, u2+H, u2+N+H, u1+N+H 
        ]
        
        # <a1>, <a2> are corner EMPTYs controlling the attached segment
        # <a> is a segment EMPTY fot the attached segment
        a1, a, a2 = self.createAttachment(verts, attachLeft, True)
        wallAttached = getWallFromEmpty(context, self.op, a)
        
        # create drivers
        addAttachedDrivers(wallAttached, a1, a2, o1, o2, True)
        
        return a
    
    def completeAttachedWall(self, o, targetWall, target):
        # <o> it the free end of the attached wall
        e2 = targetWall.getCornerEmpty(target)
        e1 = targetWall.getPrevious(e2)
        # vector along the target wall segment
        u = e2.location - e1.location
        # Will the attached wall be located on the left side (True) or on the right one (False)
        # relative to the target wall segment? This is defined by relative position of <o>
        # and the target wall segment defined by <e1> and <e2>.
        attachLeft = True if u.cross(o.location - e1.location)[2]>=0 else False
        
        if (attachLeft and not e1["l"]) or (not attachLeft and e1["l"]):
            # the attached wall to be created can't cross the current wall segment!
            e1 = targetWall.getNeighbor(e1)
            e2 = targetWall.getNeighbor(e2)
        
        # find where continuation of <o> will meet the target wall defined by <e1> and <e2>
        # normal to the target wall segment
        n = u.cross(zAxis).normalized()
        p1 = o.location - n.dot(o.location-e1.location)*n
        # normal to the wall segment defined by <o> and <p>
        n = (p1 - o.location).cross(zAxis).normalized()
        if not o["l"]:
            n = -n
        # continuation of the neighbor of <o>
        p2 = p1 + o["w"]*n
        
        _e1, _e2 = self.createExtension(o, p1, p2)
        
        setCustomAttributes(_e1, t="wa", al=1 if attachLeft else 0)
        setCustomAttributes(_e2, t="wa", al=1 if attachLeft else 0)
        
        addAttachedDrivers(self, _e1, o, e1, e2)
        
        return e1
    
    def connect(self, wall2, o1, o2):
        """
        Connect two wall segments defined by <o1> and <o2> with a new wall segment.
        <o1> belongs to <self>, <o2> belongs to <wall2>
        """
        from mathutils.geometry import intersect_line_line
        # Try to attach a new segment perpendicular to longest one from <o1> and <o2> and
        # try to start the new segment from the middle of the shortest from <o1> and <o2>
        
        context = self.context
        prk = context.scene.prk
        wall1 = self
        referenceWall = wall1 if not wall1.external or wall2.external else wall2
        if referenceWall.external:
            if prk.newWallType == "internal":
                # override referenceWall.external
                referenceWall.external = False
        else:
            referenceWall.inheritLevelFrom = o1 if not wall1.external else o2
        w = prk.newWallWidth
        h = referenceWall.getHeight()
        H = h*zAxis
        
        o12 = wall1.getCornerEmpty(o1)
        o11 = wall1.getPrevious(o12)
        o22 = wall2.getCornerEmpty(o2)
        o21 = wall2.getPrevious(o22)
        # The new segment can't cross wall segments defined by <o1> and <o2>,
        # so check if need to use neighbor of <o11>-<o12> and <o21>-<o22>
        # The meaning of <attachedLeft> variable is explained in self.startAttachedWall(..) and self.completeAttachedWall(..)
        # <o11>-<o12>
        u1 = o12.location-o11.location
        u1l = u1.length
        u1 = u1/u1l
        # <o21>-<o22>
        u2 = o22.location-o21.location
        u2l = u2.length
        u2 = u2/u2l
        
        # flip <wall1> and <wall2> if necessary
        if u2l<u1l:
            wall1, wall2 = wall2, wall1
            o11, o12, o21, o22, u1, u2 = o21, o22, o11, o12, u2, u1
        
        # <o11>-<o12>
        attachLeft1 = True if u1.cross(o21.location - o11.location)[2]>=0 else False
        if (attachLeft1 and not o11["l"]) or (not attachLeft1 and o11["l"]):
            # the attached wall to be created can't cross the current wall segment!
            o11 = wall1.getNeighbor(o11)
            o12 = wall1.getNeighbor(o12)
        # normal to the wall segment defined by <o1> in the direction of the connecting wall segment to be created
        n1 = zAxis.cross(u1) if attachLeft1 else u1.cross(zAxis)
        # <o21>-<o22>
        attachLeft2 = True if u2.cross(o11.location - o21.location)[2]>=0 else False
        if (attachLeft2 and not o21["l"]) or (not attachLeft2 and o21["l"]):
            # the attached wall to be created can't cross the current wall segment!
            o21 = wall2.getNeighbor(o21)
            o22 = wall2.getNeighbor(o22)
        # normal to the wall segment defined by <o2> in the direction of the connecting wall segment to be created
        n2 = zAxis.cross(u2) if attachLeft2 else u2.cross(zAxis)
        
        # verts of the attached wall along <o1>
        # normal to <n2>
        n = n2.cross(zAxis)
        # the middle of <o1>
        m = (o11.location + o12.location)/2.
        # verts of the attached wall along <o1>
        u11 = m - 0.5*w/u1.dot(n)*u1
        u12 = m + 0.5*w/u1.dot(n)*u1
        
        # find intersection of the segment <o2> and its normal <n2> coming through the middle of <o1>
        p = intersect_line_line(o21.location, o22.location, m, m-n2)[0]
        # verts of the attached wall along <o2>
        u21 = p - 0.5*w/u2.dot(n)*u2
        u22 = p + 0.5*w/u2.dot(n)*u2
        # dot product indicates if <u1> and <u2> point in the same direction
        dot = u1.dot(u2)
        if dot<0.:
            u21, u22 = u21, u22
        verts = [
            u11, u12, u22, u21,
            u11+H, u12+H, u22+H, u21+H
        ]
        
        # <a1>, <a2> are corner EMPTYs controlling the attached segment
        # <a> is a segment EMPTY fot the attached segment
        a1, a, a2 = referenceWall.createAttachment(verts, attachLeft1, False)
        wallAttached = getWallFromEmpty(context, self.op, a)
        # set additional attribute for <a2> and its neighbor
        setCustomAttributes(a2, al=1 if attachLeft2 else 0)
        setCustomAttributes(wallAttached.getNeighbor(a2), al=1 if attachLeft2 else 0)
        
        # create drivers
        addAttachedDrivers(wallAttached, a1, a2, o11, o12, True)
        addAttachedDrivers(wallAttached, a2, a1, o21, o22, True)
        
        return a
    
    def insert(self, o, obj, constructor):
        o2 = self.getCornerEmpty(o)
        o1 = self.getPrevious(o2)
        if self.external:
            # override self.external
            self.external = False
        else:
            self.inheritLevelFrom = o
        self.parent_set(obj)
        # create an item instance with <constructor> and init the instance
        constructor(self.context, self.op).create(obj, self, o1, o2)
    
    def move_invoke(self, op, context, event, o):
        from base.mover_segment import SegmentMover
        from base.mover_along_line import AlongSegmentMover, AttachedMover
        
        op.blockAxisConstraint = True
        
        t = o["t"]
        if t == "wc" and "e" in o:
            # <o> is corner EMPTY and located at either end of the wall
            mover = AlongSegmentMover(self, o)
            op.blockAxisConstraint = False
        elif t == "ws":
            # <o> is segment EMPTY
            mover = SegmentMover(self, o)
        elif t == "wa":
            # <o> is attached to another wall part
            mover = AttachedMover(self, o)
        else:
            bpy.ops.transform.translate("INVOKE_DEFAULT")
            return {'FINISHED'}
        # keep the following variables in the operator <o>
        op.lastOperator = getLastOperator(context)
        op.mover = mover
        op.finished = False
        # The order how self.mover.start() and context.window_manager.modal_handler_add(self)
        # are called is important. If they are called in the reversed order, it won't be possible to
        # capture X, Y, Z keys
        mover.start()
        context.window_manager.modal_handler_add(op)
        return {'RUNNING_MODAL'}
    
    def move_modal(self, op, context, event, o):
        operator = getLastOperator(context)
        if op.blockAxisConstraint and event.type in {'X', 'Y', 'Z'}:
            # capture X, Y, Z keys
            return {'RUNNING_MODAL'}
        if op.finished:
            op.mover.end()
            return {'FINISHED'}
        if operator != op.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
            # let cancel event happen, i.e. don't call op.mover.end() immediately
            op.finished = True
        return {'PASS_THROUGH'}
    
    def parent_set(self, *objects):
        parent = self.getCommonParent() if self.external else self.getLevelParent()
        parent_set(parent, *objects)
        return parent
    
    def getLevelParent(self, levelOffset=0):
        # Optional levelOffset refers to GUI level index offset in the GUI list of levels
        parent = self.parent
        context = self.context
        prk = context.scene.prk
        index = self.inheritLevelFrom.parent["level"] \
            if self.inheritLevelFrom \
            else prk.levels[prk.levelIndex].index
        # levelIndex is GUI level index in the GUI list of levels
        levelIndex = prk.levelIndex
        if self.inheritLevelFrom:
            for i,l in enumerate(prk.levels):
                if l.index == index:
                    levelIndex = i
                    break
        if levelOffset:
            levelIndex += levelOffset
            index = prk.levels[levelIndex].index
        levelParent = None
        for o in parent.children:
            if "level" in o and o["level"] == index:
                levelParent = o
                break
        if not levelParent:
            # create a Blender parent object for the level
            levelParent = createEmptyObject("level "+str(index), (0., 0., getLevelZ(context, levelIndex)), True, **self.emptyPropsLevel)
            levelParent["level"] = index
            parent_set(parent, levelParent)
        return levelParent
    
    def getCommonParent(self):
        parent = self.parent
        commonParent = None
        for o in parent.children:
            if "co" in o and o["co"]:
                commonParent = o
                break
        if not commonParent:
            # create a Blender parent object for external walls
            commonParent = createEmptyObject("common", (0., 0., 0.), True, **self.emptyPropsLevel)
            commonParent["co"] = 1
            parent_set(parent, commonParent)
        return commonParent
    
    def getTotalHeightEmpty(self):
        """Get a Blender EMPTY that controls the height of the whole building"""
        parent = self.parent
        hEmpty = None
        for o in parent.children:
            if "h" in o and o["h"]:
                hEmpty = o
                break
        if not hEmpty:
            hEmpty = createEmptyObject("h", (0., 0., self.getTotalHeight()), True, **self.emptyPropsLevel)
            hEmpty["h"] = 1
            parent_set(parent, hEmpty)
        return hEmpty


pContext.register(Wall, GuiWall, "wc", "ws", "wa")
