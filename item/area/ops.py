import bpy, bgl
from base import pContext, getItem
from util.blender import makeActiveSelectedfrom . import getAreaObject
from item.wall import getWallFromEmpty
from item.finish.flat import FinFlat

def getAreaInstance(context, op, o=None):
    return pContext.items[context.scene.prk.areaType][0](context, op, o)


class AreaMake(bpy.types.Operator):
    bl_idname = "prk.area_make"
    bl_label = "Make an area"
    bl_description = "Make an area surrounded by walls"
    bl_options = {"REGISTER", "UNDO"}
    
    createWalls = bpy.props.BoolProperty(
        name = "Create walls",
        description = "Create internal surfaces for the walls surrounding the area",
        default = True
    )
    assignUv = bpy.props.BoolProperty(
        name = "Assign UV",
        description = "Assign UV coordinates for the walls",
        default = True
    )
    
    def execute(self, context):
        o = context.scene.objects.active
        area = None
        wall = getWallFromEmpty(context, self, o)
        if not wall:
            self.report({"ERROR"}, "To begin an area, select an EMPTY object belonging to the wall")
            return {'CANCELLED'}
        o = getAreaInstance(context, self).make(o, wall)
        if self.assignUv:
            area = getItem(context, self, o)
            area.assignUv()
        
        if self.createWalls:
            if not area:
                area = getItem(context, self, o)
            finish = FinFlat(context, self)
            finish.createFromArea(area)
            if self.assignUv:
                finish.assignUv()
        
        bpy.ops.object.select_all(action="DESELECT")
        makeActiveSelected(context, o)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "createWalls")
        if self.createWalls:
            layout.prop(self, "assignUv")
    

def draw_callback_area(op, context):
    area = getAreaObject(context)
    if not area:
        # stop drawing
        bpy.types.SpaceView3D.draw_handler_remove(op._handle, "WINDOW")
        op._handle = None
        return
    bgl.glColor4f(0., 0., 1.0, 1.0)
    bgl.glLineWidth(4)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for v in area.data.vertices:
        bgl.glVertex3f(*(area.matrix_world*v.co))
    bgl.glEnd()
    

def area_begin(context, op):
    o = context.object
    if not getWallFromEmpty(context, op, o):
        op.report({'ERROR'}, "To begin an area, select an EMPTY object belonging to the wall")
        return {'CANCELLED'}
    # an area Blender object will be created in the following call
    getAreaInstance(context, op, o)
    context.scene.objects.active = o
    

def area_continue(context, op, considerFinish):
    o = context.object
    if not getWallFromEmpty(context, op, o):
        op.report({'ERROR'}, "To continue the area, select an EMPTY object belonging to the wall")
        return {'CANCELLED'}
    # get Blender area object
    areaObj = getAreaObject(context)
    # check we if empty has been already used for the area
    for m in areaObj.modifiers:
        if m.type == "HOOK" and m.object == o:
            used = True
            break
    else:
        used = False
    if used:
        if not considerFinish or len(areaObj.data.vertices)<3:
            op.report({'ERROR'}, "The area already has a vertex here, select another EMPTY object")
            return {'CANCELLED'}
        if considerFinish:
            area_finish(context, op)
    else:
        getAreaInstance(context, op).extend(o)
        context.scene.objects.active = o
        if not op._handle:
            # start drawing
            op._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_area, (op, context), "WINDOW", "POST_VIEW")


def area_finish(context, op):
    o = getAreaInstance(context, op).finish()
    bpy.ops.object.select_all(action="DESELECT")
    makeActiveSelected(context, o)


class AreaWork(bpy.types.Operator):
    bl_idname = "prk.area_work"
    bl_label = "Work on an area"
    bl_description = "Universal operator to begin, continue and finish an area"
    bl_options = {"REGISTER", "UNDO"}
    
    _handle = None
    
    def execute(self, context):
        area = getAreaObject(context)
        if area:
            area_continue(context, self, True)
        else:
            area_begin(context, self)
        
        return {'FINISHED'}


class AreaBegin(bpy.types.Operator):
    bl_idname = "prk.area_begin"
    bl_label = "Begin an area"
    bl_description = "Begins an area from the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        area_begin(context, self)
        return {'FINISHED'}


class AreaContinue(bpy.types.Operator):
    bl_idname = "prk.area_continue"
    bl_label = "Continue the area"
    bl_description = "Continues the area with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        area_continue(context, self, False)
        return {'FINISHED'}


class AreaFinish(bpy.types.Operator):
    bl_idname = "prk.area_finish"
    bl_label = "Finish the area"
    bl_description = "Finishes the area with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        area_finish(context, self)
        return {'FINISHED'}


class ExtrudedAdd(bpy.types.Operator):
    bl_idname = "prk.extruded_add"
    bl_label = "Add an extruded object"
    bl_description = "Adds a extruded object (baseboard, ledge) for the border of the area"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        from item.extruded import Extruded
        
        o = context.scene.objects.active
        selected = context.selected_objects
        if len(selected)==2:
            profile = selected[0] if selected[1]==o else selected[1]
        else:
            self.report({'ERROR'}, "To create an extruded object first select a profile object then a room object")
            return {'FINISHED'}
        
        area = getItem(context, self, o)
        
        Extruded(context, self).create(area.getControls(), o.parent, profile)
        return {'FINISHED'}