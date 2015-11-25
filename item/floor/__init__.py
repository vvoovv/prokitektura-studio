import bpy, bmesh
from blender_util import createMeshObject, getBmesh, assignGroupToVerts, addHookModifier
from item.wall import getWallFromEmpty
from base import zero


def getFloorObject(context):
    prk = context.window_manager.prk
    if prk.floorName and not prk.floorName in bpy.data.objects:
        prk.floorName = ""
    return bpy.data.objects[prk.floorName] if prk.floorName else None


class Floor:
    
    type = "floor"
    
    name = "Floor"
    
    def __init__(self, context, op, empty=None):
        self.context = context
        self.op = op
        if empty:
            self.create(empty)
    
    def make(self, empty):
        context = self.context
        wall = getWallFromEmpty(context, self.op, empty)
        empty = wall.getCornerEmpty(empty)
        left = empty["l"]
        closed = wall.isClosed()
        origin = empty if closed else wall.getStart(left)

        obj = createMeshObject("Floor", self.getLocation(origin))
        obj.hide_select = True
        # type
        obj["t"] = Floor.type
        # without scene.update() obj.matrix_world.inverted() won't give the correct result 
        context.scene.update()
        objMatrixInverted = obj.matrix_world.inverted()
        
        bm = getBmesh(obj)
        # create a deform layer to store vertex groups
        layer = bm.verts.layers.deform.new()
        
        vert = bm.verts.new((0., 0., 0.))
        vert0 = vert
        vertIndex = 0
        assignGroupToVerts(obj, layer, str(vertIndex), vert)
        
        empty = origin
        while True:
            empty = wall.getNext(empty)
            if empty == origin or not empty:
                break
            vertIndex += 1
            _vert = vert
            vert = bm.verts.new(objMatrixInverted * self.getLocation(empty))
            assignGroupToVerts(obj, layer, str(vertIndex), vert)
        
        # the closing edge
        # the face
        face = bm.faces.new(bm.verts)
        
        bm.to_mesh(obj.data)
        if obj.data.polygons[0].normal[2]<-zero:
            bmesh.ops.reverse_faces(bm, faces = (face,))
            bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
        context.scene.update()
        
        # add hook modifiers
        vertIndex = 0
        empty = origin
        while True:
            group = str(vertIndex)
            addHookModifier(obj, group, empty, group)
            empty = wall.getNext(empty)
            vertIndex += 1
            if empty == origin or not empty:
                break
    
    def create(self, empty):
        context = self.context
        
        obj = createMeshObject("Floor", self.getLocation(empty))
        #obj.hide_select = True
        context.window_manager.prk.floorName = obj.name
        obj["t"] = "floor"
        obj["counter"] = 0
        group = "0"
        bm = getBmesh(obj)
        # create a deform layer to store vertex groups
        layer = bm.verts.layers.deform.new()
        vert = bm.verts.new((0., 0., 0.))
        
        assignGroupToVerts(obj, layer, group, vert)
        bm.to_mesh(obj.data)
        bm.free()
        
        # without scene.update() hook modifiers will not work correctly
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
                    vert = bm.verts.new(obj.matrix_world.inverted() * self.getLocation(e))
                    assignGroupToVerts(obj, bm.verts.layers.deform[0], group, vert)
                    _vert = vert
                    inbetweens.append((e, group))
                
        counter += 1
        obj["counter"] = counter
        group = str(counter)
        vert = bm.verts.new(obj.matrix_world.inverted() * self.getLocation(empty))
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
        return empty.parent.matrix_world * empty.matrix_parent_inverse * empty.location