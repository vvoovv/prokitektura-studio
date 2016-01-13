import bpy, bmesh
from blender_util import createMeshObject, getBmesh, assignGroupToVerts, addHookModifier, parent_set
from item.wall import getWallFromEmpty
from base import zero


def getFloorObject(context):
    prk = context.window_manager.prk
    if prk.floorName and not prk.floorName in bpy.data.objects:
        prk.floorName = ""
    return bpy.data.objects[prk.floorName] if prk.floorName else None


class WalkAlongWalls:
    
    def __init__(self, parent):
        self.parent = parent
        # key: (l|r)group; value: list of entries for all walls attached to the wall with the given key
        self.attached = {}
        # key: group for an attached wall; value: entry from self.attached
        self._attached = {}
        self.wallParts = {}
        self.init()
    
    def init(self):
        # iterate through all attached EMPTYs to build a registry of attached wall parts
        for o in self.parent.children:
            if not (o.type=="EMPTY" and "t" in o and o["t"]=="wa") or o["g"] in self._attached:
                continue
            o1, o2 = self.getWallPart(o).getReferencesForAttached(o)
            # relative position of <o> on the edge defined by <o1> and <o2>
            pos = (o.location - o1.location).length/(o2.location - o1.location).length
            key = self.getKey(o2)
            if not key in self.attached:
                self.attached[key] = []
            attached = self.attached[key]
            numAttached = len(attached)
            # insert new entry to <attached>
            # all entries in <attached> are sorted by <pos>
            # implementing bisect.insort_right(..)
            lo = 0
            hi = numAttached
            while lo < hi:
                mid = (lo+hi)//2
                if pos < attached[mid][1]:
                    hi = mid
                else:
                    lo = mid+1
            # insert a list: [<o>, <pos>, <previous entry>, <next entry>]  
            entry = [o, pos, attached[lo-1] if lo else None, attached[lo] if lo<numAttached else None]
            # update the neighboring entries of <attached> for the <entry> to be inserted
            # the previous entry if available:
            if lo:
                attached[lo-1][3] = entry
            # the next entry if available:
            if lo<numAttached:
                attached[lo][2] = entry
            # finally, insert the new <entry> to self.attached
            attached.insert(lo, entry)
            # and to self._attached
            self._attached[o["g"]] = entry
    
    def walk(self, o, wall):
        # self.direction is None means we should walk along the attached wall starting
        # from its attached EMPTY
        self.direction = None
        empties = [o]
        e = o
        while True:
            e = self.getNextEmpty(e, wall)
            if not e or e == o:
                break
            wall = self.getWallPart(e)
            empties.append(e)
        return empties
    
    def getNextEmpty(self, o, wall):
        if self.direction is not None and wall.isAttached(o):
            return self.getNextForAttached(o, wall) \
                if (o["e"] and ((o["l"] and o["al"]) or (not o["l"] and not o["al"]))) or \
                    (not o["e"] and ((not o["l"] and o["al"]) or (o["l"] and not o["al"]))) \
                else self.getPreviousForAttached(o, wall)
        else:
            if self.direction is None:
                self.setDirection(o, wall)
            
            if self.direction:
                o = wall.getNext(o)
                if not o:
                    return None
            
            key = self.getKey(o)
            # check if the wall segment has attached walls
            if key in self.attached:
                # find an attached wall, both ends of which are attached
                for attached in self.attached[key] if self.direction else reversed(self.attached[key]):
                    a = attached[0]
                    # attached wall:
                    aWall = self.getWallPart(a)
                    # Check if the opposite end of attached wall <_wall> is also attached
                    if (a["e"] and aWall.isAttached(aWall.getStart(a["l"]))) or \
                      (not a["e"] and aWall.isAttached(aWall.getEnd(a["l"]))):
                        # check if we need to take the neighbor of <a>
                        if (self.direction and self.condition1(a)) or (not self.direction and self.condition0(a)):
                                a = aWall.getNeighbor(a)
                        self.direction = None
                        return a
            
            return o if self.direction else wall.getPrevious(o)
    
    def getNextForAttached(self, o, wall):
        o2 = wall.getReferencesForAttached(o)[1]
        # get entry in self._attached related to <o>
        a = self._attached[o["g"]]
        if a[3]:
            a = a[3][0]
            # check if we need to take the neighbor of <a>
            if self.condition1(a):
                a = self.getWallPart(a).getNeighbor(a)
            self.direction = None
        else:
            a = o2
            self.direction = True
        return a
    
    def getPreviousForAttached(self, o, wall):
        o1 = wall.getReferencesForAttached(o)[0]
        # get entry in self._attached related to <o>
        a = self._attached[o["g"]]
        if a[2]:
            a = a[2][0]
            # check if we need to take the neighbor of <a>
            if self.condition0(a):
                a = self.getWallPart(a).getNeighbor(a)
            self.direction = None
        else :
            a = o1
            self.direction = False
        return a

    def setDirection(self, o, wall):
        """
        Set direction of the walk along walls
        Returns:
        True if the direction is from start to end; False in the opposite case
        """
        self.direction = False if o == wall.getEnd(o["l"]) else True
    
    def getKey(self, o):
        return ("l" if o["l"] else "r") + o["g"]
    
    def getWallPart(self, o):
        parts = self.wallParts
        if not o["m"] in parts:
            parts[o["m"]] = getWallFromEmpty(None, None, o)
        return parts[o["m"]]
    
    def condition1(self, a):
        """
        A helper function used in the condition for the direct walk from the start to the end of a wall part
        """
        return (a["l"] and ((not a["al"] and not a["e"]) or (a["al"] and a["e"]))) or \
            (not a["l"] and ((not a["al"] and a["e"]) or (a["al"] and not a["e"])))
    
    def condition0(self, a):
        """
        A helper function used in the condition for the reversed walk from the end to the start of a wall part
        """
        return (a["l"] and ((not a["al"] and a["e"]) or (a["al"] and not a["e"]))) or \
            (not a["l"] and ((not a["al"] and not a["e"]) or (a["al"] and a["e"])))


class Floor:
    
    type = "floor"
    
    name = "Floor"
    
    def __init__(self, context, op, empty=None):
        self.context = context
        self.op = op
        if empty:
            self.create(empty)

    def make(self, o, wall):
        o = wall.getCornerEmpty(o)
        # go through all EMPTYs and create a floor from them
        self.makeFromEmpties( WalkAlongWalls(o.parent).walk(o, wall) )
    
    def makeFromEmpties(self, empties):
        context = self.context
        parent = empties[0].parent
        
        obj = createMeshObject("Floor")
        obj.hide_select = True
        # type
        obj["t"] = Floor.type
        
        bm = getBmesh(obj)
        # create a deform layer to store vertex groups
        layer = bm.verts.layers.deform.new()
        
        vertIndex = 0
        for e in empties:
            vert = bm.verts.new(self.getLocation(e))
            assignGroupToVerts(obj, layer, str(vertIndex), vert)
            vertIndex += 1
        
        # the face
        face = bm.faces.new(bm.verts)
        
        bm.to_mesh(obj.data)
        if obj.data.polygons[0].normal[2]<-zero:
            bmesh.ops.reverse_faces(bm, faces = (face,))
            bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        # perform parenting
        parent_set(parent, obj)
        # one more update
        context.scene.update()
        
        # add hook modifiers
        vertIndex = 0
        for e in empties:
            group = str(vertIndex)
            addHookModifier(obj, group, e, group)
            vertIndex += 1
    
    def create(self, empty):
        context = self.context
        parent = empty.parent
        
        obj = createMeshObject("Floor")
        obj.hide_select = True
        context.window_manager.prk.floorName = obj.name
        obj["t"] = "floor"
        obj["counter"] = 0
        group = "0"
        bm = getBmesh(obj)
        # create a deform layer to store vertex groups
        layer = bm.verts.layers.deform.new()
        vert = bm.verts.new(self.getLocation(empty))
        
        assignGroupToVerts(obj, layer, group, vert)
        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        # perform parenting
        parent_set(parent, obj)
        # one more update
        context.scene.update()
        
        addHookModifier(obj, group, empty, group)
    
    def extend(self, empty):
        context = self.context
        
        # get Blender object for the floor
        obj = getFloorObject(self.context)
        bm = getBmesh(obj)
        bm.verts.ensure_lookup_table()
        _vert = bm.verts[-1]
        
        # find the Blender object for the empty that controls the last created floor vertex
        counter = obj["counter"]
        prevEmpty = obj.modifiers[counter].object
        
        # If empty and prevEmpty belong to the same wall,
        # check if we need to create in-between verts for the floor,
        # i.e. empty and prevEmpty aren't adjacent
        inbetweens = []
        if empty.parent == prevEmpty.parent and empty["m"] == prevEmpty["m"]:
            wall = getWallFromEmpty(context, self.op, empty)
            if not (wall.getNext(empty) == prevEmpty or wall.getPrevious(empty) == prevEmpty):
                # find Blender empty objects for <wall>, located between empty and prevEmpty
                empties = []
                # first searching in the forward direction
                e = prevEmpty
                while True:
                    e = wall.getNext(e)
                    if e == empty or not e:
                        break
                    empties.append(e)
                
                isClosed = wall.isClosed()
                if isClosed:
                    # keep list of empties
                    _empties = empties
                
                if not e or isClosed:
                    # now try in the backward direction
                    empties = []
                    e = prevEmpty
                    while True:
                        e = wall.getPrevious(e)
                        if e == empty:
                            break
                        empties.append(e)
                # for the closed wall check whick path is shorter, in the forward or backward directions
                if isClosed and len(empties) > len(_empties): 
                    empties = _empties
                # finally, create floor verts for empties
                for e in empties:
                    counter +=1
                    group = str(counter)
                    vert = bm.verts.new(self.getLocation(e))
                    assignGroupToVerts(obj, bm.verts.layers.deform[0], group, vert)
                    _vert = vert
                    inbetweens.append((e, group))
                
        counter += 1
        obj["counter"] = counter
        group = str(counter)
        vert = bm.verts.new(self.getLocation(empty))
        assignGroupToVerts(obj, bm.verts.layers.deform[0], group, vert)
        
        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        # this step is probably optional here, however it's required in FloorBegin.execute()
        context.scene.update()
        if inbetweens:
            for e,g in inbetweens:
                addHookModifier(obj, g, e, g)
        addHookModifier(obj, group, empty, group)
    
    def finish(self):
        obj = getFloorObject(self.context)
        bm = getBmesh(obj)
        bm.verts.ensure_lookup_table()
        face = bm.faces.new(bm.verts)
        bm.to_mesh(obj.data)
        if obj.data.polygons[0].normal[2]<-zero:
            bmesh.ops.reverse_faces(bm, faces = (face,))
            bm.to_mesh(obj.data)
        bm.free()
        self.context.window_manager.prk.floorName = ""
        
    def getLocation(self, empty):
        return empty.matrix_parent_inverse * empty.location