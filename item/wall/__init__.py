import bmesh
from base import pContext, getLevelLocation, xAxis, yAxis, zAxis, zero
from blender_util import *


def getWallFromEmpty(context, op, empty, end=False):
    # The end==True means empty must be at either open end of the wall
    # check validity of empty
    if not (empty and empty.type == "EMPTY" and (not end or "e" in empty)):
        return None
    wall = Wall(context, op)
    wall.init(empty.parent, empty)
    return wall


def addTransformsVariable(driver, name, id0, transform_type):
    v = driver.driver.variables.new()
    v.name = name
    v.type = "TRANSFORMS"
    v.targets[0].id = id0
    v.targets[0].transform_type = transform_type
    v.targets[0].transform_space = "LOCAL_SPACE"


def addSinglePropVariable(driver, name, id0, data_path):
    v = driver.driver.variables.new()
    v.name = name
    v.type = "SINGLE_PROP"
    v.targets[0].id = id0
    v.targets[0].data_path = data_path


def addLocDiffVariable(driver, name, id0, id1):
        v = driver.driver.variables.new()
        v.name = name
        v.type = "LOC_DIFF"
        v.targets[0].id = id0
        v.targets[0].transform_space = "LOCAL_SPACE"
        v.targets[1].id = id1
        v.targets[1].transform_space = "LOCAL_SPACE"


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


def addAttachedDrivers(wallAttached, o1, o2, e1, e2):
    # neighbor of <o1>
    _o1 = wallAttached.getNeighbor(o1)
    # delete corner drivers
    o1.driver_remove("location")
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
    
    #
    # <_o1>
    #
    sign = "+" if o1["l"] else "-"
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
    addSinglePropVariable(x, "w", o2, "[\"w\"]")
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
    addSinglePropVariable(y, "w", o2, "[\"w\"]")
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
    if context.window_manager.prk.widthForAllSegments:
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


class GuiWall:
    
    def draw(self, context, layout):
        layout.operator("prk.floor_make")
        layout.separator()
        layout.operator("prk.wall_flip_controls")
        o = context.scene.objects.active
        if o["t"] == "ws" or o["t"] == "wc":
            box = layout.box()
            box.prop(context.window_manager.prk, "widthForAllSegments")
            box.prop(context.window_manager.prk, "wallSegmentWidth")


class Wall:
    
    type = "wall"
    
    name = "Wall"
    
    emptyPropsCorner = {'empty_draw_type':'CUBE', 'empty_draw_size':0.02}
    emptyPropsSegment = {'empty_draw_type':'SPHERE', 'empty_draw_size':0.05}
    
    def __init__(self, context, op):
        self.context = context
        self.op = op
    
    def init(self, parent, o):
        meshIndex = o["m"]
        self.parent = parent
        # getting mesh object
        for obj in parent.children:
            if obj.type == "MESH" and obj["m"] == meshIndex:
                self.mesh = obj
                break
    
    def create(self, locEnd=None):
        context = self.context
        prk = context.window_manager.prk
        op = self.op
        loc = getLevelLocation(context)
        
        h = prk.newWallHeight
        w = prk.newWallWidth
        
        # the initial wall segment is oriented along Y-axis by default
        alongX = False
        # check if the initial wall segment should be oriented along X-axis or along Y-axis
        if locEnd:
            dx = locEnd.x-loc.x
            dy = locEnd.y-loc.y
            if abs(dx) > abs(dy):
                alongX = True
                l = dx
            else:
                l = dy
        else:
            l = op.length
            
        atRight = context.window_manager.prk.wallAtRight
        
        # parent one vert mesh
        parent = createOneVertObject("Wall", loc)
        # type
        parent["t"] = Wall.type
        parent["container"] = 1
        parent.dupli_type = "VERTS"
        parent.hide_select = True
        meshIndex = 2
        parent["counter"] = meshIndex
        
        obj = createMeshObject("wall_mesh")
        obj["height"] = h
        obj["start"] = "0"
        obj["end"] = "1"
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
            v[i] = bm.verts.new(v[i])
        
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
        
        # create vertex groups for each vertical wall edge
        if atRight:
            # for the wall origin
            assignGroupToVerts(obj, layer, "l0", v[0], v[4])
            assignGroupToVerts(obj, layer, "r0", v[1], v[5])
            # for the wall end
            assignGroupToVerts(obj, layer, "l1", v[3], v[7])
            assignGroupToVerts(obj, layer, "r1", v[2], v[6])
        else:
            # for the wall origin
            assignGroupToVerts(obj, layer, "l0", v[3], v[7])
            assignGroupToVerts(obj, layer, "r0", v[0], v[4])
            # for the wall end
            assignGroupToVerts(obj, layer, "l1", v[2], v[6])
            assignGroupToVerts(obj, layer, "r1", v[1], v[5])
        
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
            l0 = self.createCornerEmptyObject("l0", (0., 0., 0.), False)
            r0 = self.createCornerEmptyObject("r0", (0., -w, 0.) if alongX else (w, 0., 0.), True)
            l1 = self.createCornerEmptyObject("l1", (l, 0., 0.) if alongX else (0., l, 0.), False)
            r1 = self.createCornerEmptyObject("r1", (l, -w, 0.) if alongX else (w, l, 0.), True)
        else:
            l0 = self.createCornerEmptyObject("l0", (0., w, 0.) if alongX else (-w, 0., 0.), True)
            r0 = self.createCornerEmptyObject("r0", (0., 0., 0.), False)
            l1 = self.createCornerEmptyObject("l1", (l, w, 0.) if alongX else (-w, l, 0.), True)
            r1 = self.createCornerEmptyObject("r1", (l, 0., 0.) if alongX else (0., l, 0.), False)
        
        setCustomAttributes(l0, l=1, e=0, g="0", w=w, n="1", m=meshIndex)
        setCustomAttributes(r0, l=0, e=0, g="0", w=w, n="1", m=meshIndex)
        setCustomAttributes(l1, l=1, e=1, g="1", w=w, p="0", m=meshIndex)
        setCustomAttributes(r1, l=0, e=1, g="1", w=w, p="0", m=meshIndex)
        
        # without scene.update() parenting and hook modifiers will not work correctly
        context.scene.update()
        
        # perform parenting
        parent_set((obj, l0, r0, l1, r1), parent)
        
        # without scene.update() parenting and hook modifiers will not work correctly
        # this step is probably optional here, however it's required in self.extend(..)
        context.scene.update()
        
        # add hook modifiers
        addHookModifier(obj, "l0", l0, "l0")
        addHookModifier(obj, "r0", r0, "r0")
        addHookModifier(obj, "l1", l1, "l1")
        addHookModifier(obj, "r1", r1, "r1")
        
        # add drivers
        if atRight:
            self.addEndEdgeDrivers(r0, l0, l1, False, atRight)
            self.addEndEdgeDrivers(r1, l0, l1, True, atRight)
        else:
            self.addEndEdgeDrivers(l0, r0, r1, False, atRight)
            self.addEndEdgeDrivers(l1, r0, r1, True, atRight)
            
        # create Blender EMPTY objects for the initial wall segment:
        _l = self.createSegmentEmptyObject(l0, l1, parent, False if atRight else True)
        _r = self.createSegmentEmptyObject(r0, r1, parent, True if atRight else False)
        setCustomAttributes(_l, l=1, m=meshIndex)
        setCustomAttributes(_r, l=0, m=meshIndex)
        
        bpy.ops.object.select_all(action="DESELECT")
        if atRight:
            l1.select = True
        else:
            r1.select = True
        context.scene.objects.active = l1 if atRight else r1
        
        return (alongX, not alongX, False)
    
    def extend(self, empty1, locEnd = None):
        
        parent = self.parent
        
        if locEnd:
            # convert the end location to the coordinate system of the wall
            locEnd = parent.matrix_world.inverted() * locEnd
        
        empty2 = self.getNeighbor(empty1)
        context = self.context
        op = self.op
        mesh = self.mesh
        meshIndex = mesh["m"]
        counter = parent["counter"] + 1
        group = str(counter)
        # are we at the end (1) or at the start (0)
        end = empty1["e"]
        h = mesh["height"]
        # the width of the new wall segment
        w = empty1["w"]
        
        bm = getBmesh(mesh)
        # All vertex groups are in the deform layer.
        # There can be only one deform layer
        layer = bm.verts.layers.deform[0]
        
        # Will the wall be extended the left side (True) or on the right one (False)
        # relative to the original wall segment? This is defined by relative position of the mouse
        # and the original wall segment.
        _v = (self.getPrevious(empty1) if end else empty1).location
        v = (empty1 if end else self.getNext(empty1)).location
        # vector along the current wall segment
        u = (v - _v).normalized()
        extendLeft = True if u.cross(locEnd - _v)[2]>=0 else False
        
        left = empty1["l"]
        prefix1 = "l" if left else "r"
        group1 = prefix1 + group
        # prefix for the neighbor verts located to the left or to the right
        prefix2 = "r" if left else "l"
        group2 = prefix2 + group
        # delete the face at the open end of the wall, defined by the related vertex groups
        verts1 = self.getVertsForVertexGroup(bm, prefix1+empty1["g"])
        verts2 = self.getVertsForVertexGroup(bm, prefix2+empty1["g"])
        bmesh.ops.delete(
            bm,
            geom=(getFaceFortVerts(verts1, verts2),),
            context=3
        )
        
        # normal to the current wall segment in the direction of the new wall segement to be extended
        n = ( zAxis.cross(u) if extendLeft else u.cross(zAxis) ).normalized()
        # Normal with the length equal to the length of the new wall segment to be extended
        # The length is defined by locEnd
        N = (n.dot(locEnd-_v) if locEnd else op.length)*n
        # continuation of the vertex controlled by empty1, a Blender empty object
        # normal to the open edge ending by empty1
        n = (
                empty1.location - self.getPrevious(empty1).location if end else self.getNext(empty1).location - empty1.location
            ).cross(zAxis).normalized()
        
        loc = empty1.location + N
        e1 = self.createCornerEmptyObject(group1, loc, False)
        setCustomAttributes(e1, l=1 if left else 0, e=end, g=group, w=w, m=meshIndex)
        if end:
            setCustomAttributes(e1, p=empty1["g"])
            setCustomAttributes(empty1, n=group)
        else:
            setCustomAttributes(e1, n=empty1["g"])
            setCustomAttributes(empty1, p=group)
        del empty1["e"]
        # create also the accompanying verts
        v1_1 = bm.verts.new(e1.location)
        v1_2 = bm.verts.new(v1_1.co + h*zAxis)
        # neighbor of e1
        # normal to the line between empty1.location and e1.location
        n = n.cross(zAxis)
        if not end:
            n = -n
        e2 = self.createCornerEmptyObject(group2, loc + w*n, True)
        setCustomAttributes(e2, l=0 if left else 1, e=end, g=group, w=w, m=meshIndex)
        if end:
            setCustomAttributes(e2, p=empty1["g"])
            setCustomAttributes(empty2, n=group)
        else:
            setCustomAttributes(e2, n=empty1["g"])
            setCustomAttributes(empty2, p=group)
        del empty2["e"]
        # create also the accompanying verts
        v2_1 = bm.verts.new(e2.location)
        v2_2 = bm.verts.new(v2_1.co + h*zAxis)
        
        if end:
            self.addInternalEdgeDrivers(empty2, self.getPrevious(empty1), empty1, e1, 1, left)
        else:
            self.addInternalEdgeDrivers(empty2, e1, empty1, self.getNext(empty1), 0, left)
        
        # create all necessary faces
        condition = (left and end) or (not left and not end)
        bm.faces.new( (verts1[0], verts1[1], v1_2, v1_1) if condition else (v1_1, v1_2, verts1[1], verts1[0]) )
        bm.faces.new( (v1_1, v1_2, v2_2, v2_1) if condition else (v2_1, v2_2, v1_2, v1_1) )
        bm.faces.new((v2_1, v2_2, verts2[1], verts2[0]) if condition else (verts2[0], verts2[1], v2_2, v2_1) )
        bm.faces.new((verts1[1], verts2[1], v2_2, v1_2) if condition else (v1_2, v2_2, verts2[1], verts1[1]) )
        bm.faces.new((v1_1, v2_1, verts2[0], verts1[0]) if condition else (verts1[0], verts2[0], v2_1, v1_1) )
        
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
        parent_set((e1, e2), parent)
        
        # without scene.update() parenting and hook modifiers will not work correctly
        context.scene.update()
        
        # add hook modifiers
        addHookModifier(mesh, group1, e1, group1)
        addHookModifier(mesh, group2, e2, group2)
        
        # add drivers
        if end:
            self.addEndEdgeDrivers(e2, empty1, e1, True, left)
        else:
            self.addEndEdgeDrivers(e2, e1, empty1, False, left)

        # create Blender EMPTY objects for the just created wall segment:
        if end:
            s1 = self.createSegmentEmptyObject(empty1, e1, self.parent, False)
            s2 = self.createSegmentEmptyObject(empty2, e2, self.parent, True)
        else:
            s1 = self.createSegmentEmptyObject(e1, empty1, self.parent, False)
            s2 = self.createSegmentEmptyObject(e2, empty2, self.parent, True)
        setCustomAttributes(s1, m=meshIndex)
        setCustomAttributes(s2, m=meshIndex)
        
        return e1
    
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

        # create Blender EMPTY objects for the just created wall segment:
        s1 = self.createSegmentEmptyObject(end, start, self.parent, start.hide)
        s2 = self.createSegmentEmptyObject(self.getNeighbor(end), self.getNeighbor(start), self.parent, not start.hide)
        setCustomAttributes(s1, m=meshIndex)
        setCustomAttributes(s2, m=meshIndex)
    
    def flipControls(self, o):
        left = o["l"]
        prefix1 = "l" if left else "r"
        # prefix for the neighbor verts located to the left or to the right
        prefix2 = "r" if left else "l"
        
        # keep reference to the input EMPTY object
        _o = o 
        
        closed = self.isClosed()
        
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
            start = self.getStart(left)
            hide_select(start, True)
            end = self.getEnd(left)
            hide_select(end, True)
            m0 = self.getNeighbor(start)
            m1 = self.getNext(m0)
            m2 = self.getNext(m1)
            
            left = not left
            # start
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
            self.addEndEdgeDrivers(end, m1, m2, True, left)
            hide_select(m2, False)
        
        # 2) deal with segment empties
        o = _o
        neighbor = None
        for obj in self.parent.children:
            if obj.type == "EMPTY" and "t" in obj and obj["t"]=="ws":
                hide_select(obj, False if obj["l"]==left else True)
                # find the neighbor of <o> if <o> is a segment EMPTY 
                if o["t"] == "ws" and not neighbor and obj["g"] == o["g"] and o!=obj:
                    neighbor = obj
        
        # select the neighbor of <o>
        o = neighbor if neighbor else self.getNeighbor(o)
        o.select = True
        self.context.scene.objects.active = o       
            
    def getNeighbor(self, o):
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
    
    def getStart(self, left):
        return None if self.isClosed() else self.getEmpty(self.mesh["start"], left)
        
    def getEnd(self, left):
        return None if self.isClosed() else self.getEmpty(self.mesh["end"], left)
    
    def getEmpty(self, group, left):
        prefix = "l" if left else "r"
        return self.mesh.modifiers[prefix+group].object
    
    def getCornerEmpty(self, o):
        if o["t"] == "ws":
            # get corner EMPTY object if the input was a segment EMPTY object
            o = self.getEmpty(o["g"], o["l"])
        return o
    
    def isClosed(self):
        return not "end" in self.mesh
    
    def getWidth(self, o):
        return self.getCornerEmpty(o)["w"]
    
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
        parent_set(empty, parent)
        
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
        parent = self.parent
        o = self.getCornerEmpty(o)
        
        locEnd.z = 0.
        # convert the end location to the coordinate system of the wall
        locEnd = parent.matrix_world.inverted() * locEnd
        _v = self.getPrevious(o).location
        v = o.location
        # vector along the current wall segment
        u = (v - _v).normalized()
        # Will the attached wall be located on the left side (True) or on the right one (False)
        # relative to the original wall segment? This is defined by relative position of the mouse
        # and the original wall segment.
        attachLeft = True if u.cross(locEnd - _v)[2]>=0 else False
        
        if (attachLeft and not o["l"]) or (not attachLeft and o["l"]):
            # the attached wall to be created can't cross the current wall segment!
            o = self.getNeighbor(o)
            _v = self.getPrevious(o).location
            v = o.location
        
        context = self.context
        prk = context.window_manager.prk
        atRight = prk.wallAtRight
        w = prk.newWallWidth
        h = prk.newWallHeight
        H = h*zAxis
        
        # normal to the current wall segment in the direction of the attached wall to be created
        n = ( zAxis.cross(u) if attachLeft else u.cross(zAxis) ).normalized()
        # normal with the length equal to the length of the attached wall defined by locEnd
        N = n.dot(locEnd-_v)*n
        # verts of the attached wall along the current wall segment
        _u = 0.5*(v+_v) - 0.5*w*u
        u = 0.5*(v+_v) + 0.5*w*u
        verts = [
            _u, u, u+N, _u+N,
            _u+H, u+H, u+N+H, _u+N+H 
        ]
        
        counter = parent["counter"] + 1
        group0 = str(counter)
        group1 = str(counter+1)
        
        obj = createMeshObject("wall_mesh")
        meshIndex = counter+2
        obj["m"] = meshIndex
        obj["height"] = h
        obj["start"] = group0
        obj["end"] = group1
        obj.hide_select = True
        bm = getBmesh(obj)
        # vertex groups are in the deform layer, create one before any operation with bmesh:
        layer = bm.verts.layers.deform.new()
        
        l0 = self.createAttachedEmptyObject("l"+group0, verts[0] if attachLeft else verts[1], False if atRight else True)
        r0 = self.createAttachedEmptyObject("r"+group0, verts[1] if attachLeft else verts[0], True if atRight else False)
        l1 = self.createCornerEmptyObject("l"+group1, verts[3] if attachLeft else verts[2], False if atRight else True)
        r1 = self.createCornerEmptyObject("r"+group1, verts[2] if attachLeft else verts[3], True if atRight else False)
        
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
        
        # create vertex groups for each vertical wall edge
        # for the wall origin
        assignGroupToVerts(obj, layer, "l"+group0, *((verts[0], verts[4]) if attachLeft else (verts[1], verts[5])) )
        assignGroupToVerts(obj, layer, "r"+group0, *((verts[1], verts[5]) if attachLeft else (verts[0], verts[4])) )
        # for the wall end
        assignGroupToVerts(obj, layer, "l"+group1, *((verts[3], verts[7]) if attachLeft else (verts[2], verts[6])) )
        assignGroupToVerts(obj, layer, "r"+group1, *((verts[2], verts[6]) if attachLeft else (verts[3], verts[7])) )
        
        parent["counter"] = counter+2

        bm.to_mesh(obj.data)
        bm.free()
        
        context.scene.update()
        # perform parenting
        parent_set((obj, l0, r0, l1, r1), parent)
        context.scene.update()
        
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
            
        # create Blender EMPTY objects for the attached wall segment:
        lEmpty = self.createSegmentEmptyObject(l0, l1, parent, False if atRight else True)
        rEmpty = self.createSegmentEmptyObject(r0, r1, parent, True if atRight else False)
        setCustomAttributes(lEmpty, m=meshIndex)
        setCustomAttributes(rEmpty, m=meshIndex)
        
        return lEmpty if atRight else rEmpty
    
    def move_invoke(self, op, context, event, o):
        from base.mover_segment import SegmentMover
        from base.mover_along_line import AlongLineMover
        
        t = o["t"]
        if t == "wc" and "e" in o:
            # <o> is corner EMPTY and located at either end of the wall
            mover = AlongLineMover(self, o)
        elif t == "ws":
            mover = SegmentMover(self, o)
        elif t == "wa":
            # <o> is attached to another wall part
            pass
        else:
            bpy.ops.transform.translate("INVOKE_DEFAULT")
            return {'FINISHED'}
        # keep the following variables in the operator <o>
        op.state = None
        op.lastOperator = getLastOperator(context)
        op.mover = mover
        op.finished = False
        mover.start()
        context.window_manager.modal_handler_add(op)
        return {'RUNNING_MODAL'}
    
    def move_modal(self, op, context, event, o):
        operator = getLastOperator(context)
        if op.finished:
            op.mover.end()
            return {'FINISHED'}
        if operator != op.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
            # let cancel event happen, i.e. don't call op.mover.end() immediately
            op.finished = True
        return {'PASS_THROUGH'}


pContext.register(Wall, GuiWall)
