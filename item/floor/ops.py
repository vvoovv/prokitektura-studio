import bpy, bgl

from . import Floor, getFloorObject


class FloorMake(bpy.types.Operator):
    bl_idname = "prk.floor_make"
    bl_label = "Make a floor for the wall"
    bl_description = "Makes a floor for the wall defined by the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        empty = context.scene.objects.active
        if not (empty and empty.type=="EMPTY" and empty.parent):
            self.report({"ERROR"}, "To begin a floor, select an EMPTY object belonging to the wall")
            return {'CANCELLED'}
        floor = Floor(context, self)
        floor.make(empty)
        
        return {'FINISHED'}
    

def draw_callback_floor(op, context):
    floor = getFloorObject(context)
    if not floor:
        # stop drawing
        bpy.types.SpaceView3D.draw_handler_remove(op._handle, "WINDOW")
        op._handle = None
        return
    bgl.glColor4f(0., 0., 1.0, 1.0)
    bgl.glLineWidth(4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for v in floor.data.vertices:
        bgl.glVertex3f(*(floor.matrix_world*v.co))
    bgl.glEnd()
    


def floor_begin(context, op):
    empty = context.object
    if not (empty and empty.type=="EMPTY" and empty.parent):
        op.report({'ERROR'}, "To begin a floor, select an EMPTY object belonging to the wall")
        return {'CANCELLED'}
    Floor(context, op, empty)
    

def floor_continue(context, op, considerFinish):
    empty = context.object
    if not (empty and empty.type=="EMPTY" and empty.parent):
        op.report({'ERROR'}, "To continue the floor, select an EMPTY object belonging to the wall")
        return {'CANCELLED'}
    # get Blender floor object
    floorObj = getFloorObject(context)
    # check we if empty has been already used for the floor
    for m in floorObj.modifiers:
        if m.type == "HOOK" and m.object == empty:
            used = True
            break
    else:
        used = False
    if used:
        if not considerFinish or len(floorObj.data.vertices)<3:
            op.report({'ERROR'}, "The floor already has a vertex here, select another EMPTY object")
            return {'CANCELLED'}
        if considerFinish:
            floor_finish(context, op)
    else:
        floor = Floor(context, op)
        floor.extend(empty)
        context.scene.objects.active = empty
        if not op._handle:
            # start drawing
            op._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_floor, (op, context), "WINDOW", "POST_VIEW")


def floor_finish(context, op):
    floor = Floor(context, op)
    floor.finish()


class FloorWork(bpy.types.Operator):
    bl_idname = "prk.floor_work"
    bl_label = "Work on a floor"
    bl_description = "Universal operator to begin, continue and finish a floor"
    bl_options = {"REGISTER", "UNDO"}
    
    _handle = None
    
    def execute(self, context):
        floor = getFloorObject(context)
        if floor:
            floor_continue(context, self, True)
        else:
            floor_begin(context, self)
        
        return {'FINISHED'}


class FloorBegin(bpy.types.Operator):
    bl_idname = "prk.floor_begin"
    bl_label = "Begin a floor"
    bl_description = "Begins a floor from the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_begin(context, self)
        return {'FINISHED'}


class FloorContinue(bpy.types.Operator):
    bl_idname = "prk.floor_continue"
    bl_label = "Continue the floor"
    bl_description = "Continues the floor with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_continue(context, self, False)
        return {'FINISHED'}


class FloorFinish(bpy.types.Operator):
    bl_idname = "prk.floor_finish"
    bl_label = "Finish the floor"
    bl_description = "Finishes the floor with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_finish(context, self)
        return {'FINISHED'}