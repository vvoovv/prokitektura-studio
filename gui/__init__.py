from base import pContext
from base import getLevelLocation

import bpy
from blender_util import cursor_2d_to_location_3d

from item.wall import Wall, getWallFromEmpty
from item.floor import Floor, getFloorObject

class MainPanel(bpy.types.Panel):
    bl_label = "Prokitektura"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Prokitektura"
    
    def draw(self, context):
        wm = context.window_manager
        layout = self.layout
        
        #layout.prop(wm, "newAtActive")
        #layout.operator("object.wall_add")
        #layout.operator("object.wall_extend")
        #layout.operator("object.wall_complete")
        #layout.separator()
        layout.operator("object.floor_make")
        #layout.operator("object.floor_begin")
        #if wm.floorName:
        #    layout.operator("object.floor_continue")
        #    layout.operator("object.floor_finish")
        
        row = self.layout.split(0.6)
        row.label("Load a preset:")
        row.operator_menu_enum("scene.load_preset", "presetCollection")
        
        layout.separator()
        layout.row().label("Levels:")
        layout.template_list("PLAN_UL_levels", "", wm, "levels", wm, "levelIndex")
        
        layout.separator()
        layout.operator("scene.add_item")


class PLAN_UL_levels(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property):
        layout.prop(item, "name", text="", emboss=False, icon="RENDERLAYERS")
        icon = 'VISIBLE_IPO_ON' if item.visible else 'VISIBLE_IPO_OFF'
        layout.prop(item, "visible", text="", emboss=False, icon=icon)


class Level(bpy.types.PropertyGroup):
    z = bpy.props.FloatProperty(
        name="height", min=0., max=100., default=2.7, precision=3,
        description="Floor height"
    )
    visible = bpy.props.BoolProperty(
        name="visibility",
        description="",
        default=True
    )


def getPresetCollections(self, context):
    items = []
    for entry in pContext.presetCollections:
        entry = pContext.presetCollections[entry]
        items.append((entry.id, entry.name, entry.description))
    return items

class LoadPreset(bpy.types.Operator):
    bl_idname = "scene.load_preset"
    bl_label = "preset"
    bl_description = "Load a preset"
    bl_options = {"REGISTER"}
    
    presetCollection = bpy.props.EnumProperty(items=getPresetCollections)

    def invoke(self, context, event):
        pContext.loadPresetCollection(self.presetCollection)
        return {'FINISHED'}


class WallEditAdd(bpy.types.Operator):
    bl_idname = "object.wall_edit_add"
    bl_label = "Add a new wall"
    bl_description = "Adds a new wall"
    bl_options = {"REGISTER", "UNDO"}

    width = bpy.props.FloatProperty(
        name = "Width",
        description = "The width of the wall segment",
        default = 0.3,
        min = 0.01,
        max = 10,
        unit = "LENGTH"
    )
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    height = bpy.props.FloatProperty(
        name = "Heigth",
        description = "The height of the wall",
        default = 2.7,
        min = 0.1,
        max = 10,
        unit = "LENGTH"
    )
    
    def invoke(self, context, event):
        locEnd = cursor_2d_to_location_3d(context, event)
        wall = Wall(context, self, False)
        constraint_axis = wall.create(locEnd)
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=constraint_axis, constraint_orientation='LOCAL')
        return {'FINISHED'}
    

class WallEditExtend(bpy.types.Operator):
    bl_idname = "object.wall_edit_extend"
    bl_label = "Extend the wall"
    bl_description = "Extends the wall"
    bl_options = {"REGISTER", "UNDO"}

    width = bpy.props.FloatProperty(
        name = "Width",
        description = "The width of the wall segment",
        default = 0.3,
        min = 0.01,
        max = 10,
        unit = "LENGTH"
    )
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    height = bpy.props.FloatProperty(
        name = "Heigth",
        description = "The height of the wall",
        default = 2.7,
        min = 0.1,
        max = 10,
        unit = "LENGTH"
    )
    
    def invoke(self, context, event):
        empty = context.object
        locEnd = cursor_2d_to_location_3d(context, event)
        wall = getWallFromEmpty(context, self, empty, True)
        if not wall:
            self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either open end of the wall")
            return {'FINISHED'}
        constraint_axis = wall.extend(empty, locEnd)
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=constraint_axis, constraint_orientation='LOCAL')
        return {'FINISHED'}


class WallAdd(bpy.types.Operator):
    bl_idname = "object.wall_add"
    bl_label = "Add a new wall"
    bl_description = "Adds a new wall"
    bl_options = {"REGISTER", "UNDO"}
    
    width = bpy.props.FloatProperty(
        name = "Width",
        description = "The width of the wall segment",
        default = 0.3,
        min = 0.01,
        max = 10,
        unit = "LENGTH"
    )
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    height = bpy.props.FloatProperty(
        name = "Heigth",
        description = "The height of the wall",
        default = 2.7,
        min = 0.1,
        max = 10,
        unit = "LENGTH"
    )
    
    def execute(self, context):
        Wall(context, self, True)
        return {'FINISHED'}


class WallExtend(bpy.types.Operator):
    bl_idname = "object.wall_extend"
    bl_label = "Extend the wall"
    bl_description = "Extends the wall"
    bl_options = {"REGISTER", "UNDO"}
    
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    
    def execute(self, context):
        empty = context.object
        wall = getWallFromEmpty(context, self, empty, True)
        if not wall:
            self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either open end of the wall")
            return {'FINISHED'}
        wall.extend(empty)
        return {'FINISHED'}


class WallComplete(bpy.types.Operator):
    bl_idname = "object.wall_complete"
    bl_label = "Complete the wall"
    bl_description = "Completes the wall"
    bl_options = {"REGISTER", "UNDO"}

    
    def execute(self, context):
        empty = context.object
        wall = getWallFromEmpty(context, self, empty)
        if not wall:
            self.report({"ERROR"}, "To complete the wall, select an EMPTY object belonging to the wall")
        wall.complete(empty["l"])
        return {'FINISHED'}


class AddItem(bpy.types.Operator):
    bl_idname = "scene.add_item"
    bl_label = "Add an item..."
    bl_description = "Adds an item"
    bl_options = {"REGISTER", "UNDO"}
    
    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH",
    )
    
    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    
    def execute(self, context):
        # deselect everything, so we can identify the newly appended objects
        bpy.ops.object.select_all(action="DESELECT")
        files = []
        with bpy.data.libraries.load(self.filepath) as (data_from, data_to):
            for name in data_from.objects:
                files.append({'name': name})
        
        bpy.ops.wm.append(directory=self.filepath+"/Object/", files=files)
        # finding the parent object
        for obj in context.selected_objects:
            if not obj.parent:
                break
        # perform cleanup
        bpy.ops.object.select_all(action="DESELECT")
        obj.location = getLevelLocation(context)
        bpy.context.scene.objects.active = obj
        obj.select = True
        # Without bpy.ops.transform.translate() some complex stuff (some modifiers)
        # may not be initialized correctly
        bpy.ops.transform.translate()
        return {'FINISHED'}
    
    
class FloorMake(bpy.types.Operator):
    bl_idname = "object.floor_make"
    bl_label = "Make a floor for the wall"
    bl_description = "Makes a floor for the wall defined by the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        empty = context.object
        if not (empty and empty.type=="EMPTY" and empty.parent):
            self.report({"ERROR"}, "To begin a floor, select an EMPTY object belonging to the wall")
            return {'CANCELLED'}
        floor = Floor(context, self)
        floor.make(empty)
        
        return {'FINISHED'}
    

##################################
### Floor stuff
##################################

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
    floor = getFloorObject(context)
    # check we if empty has been already used for the floor
    for m in floor.modifiers:
        if m.type == "HOOK" and m.object == empty:
            used = True
            break
    else:
        used = False
    if used:
        if not considerFinish or len(floor.data.vertices)<3:
            op.report({'ERROR'}, "The floor already has a vertex here, select another EMPTY object")
            return {'CANCELLED'}
        if considerFinish:
            floor_finish(context, op)
    else:
        floor = Floor(context, op)
        floor.extend(empty)


def floor_finish(context, op):
    floor = Floor(context, op)
    floor.finish()


class FloorWork(bpy.types.Operator):
    bl_idname = "object.floor_work"
    bl_label = "Work on a floor"
    bl_description = "Universal operator to begin, continue and finish a floor"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor = getFloorObject(context)
        if floor:
            floor_continue(context, self, True)
        else:
            floor_begin(context, self)
        
        return {'FINISHED'}


class FloorBegin(bpy.types.Operator):
    bl_idname = "object.floor_begin"
    bl_label = "Begin a floor"
    bl_description = "Begins a floor from the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_begin(context, self)
        return {'FINISHED'}


class FloorContinue(bpy.types.Operator):
    bl_idname = "object.floor_continue"
    bl_label = "Continue the floor"
    bl_description = "Continues the floor with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_continue(context, self, False)
        return {'FINISHED'}


class FloorFinish(bpy.types.Operator):
    bl_idname = "object.floor_finish"
    bl_label = "Finish the floor"
    bl_description = "Finishes the floor with the selected point"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        floor_finish(context, self)
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)
    wm = bpy.types.WindowManager
    wm.levels = bpy.props.CollectionProperty(type=Level)
    wm.levelIndex = bpy.props.IntProperty()
    # the name of the Blender object for the current floor
    wm.floorName = bpy.props.StringProperty()
    wm.newAtActive = bpy.props.BoolProperty(
        name = "A new item at the active object",
        description = "Adds a new item at the location of the active object, otherwise the 3D cursor location is used for the new item",
        default = False
    )

def unregister():
    bpy.utils.unregister_module(__name__)
    wm = bpy.types.WindowManager
    del wm.levels
    del wm.levelIndex
    del wm.floorName
    del wm.newAtActive