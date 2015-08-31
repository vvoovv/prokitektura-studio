from base import pContext
from base import getLevelLocation

import bpy

from item.wall import setWidth, getWidth


class PanelMain(bpy.types.Panel):
    bl_label = "Prokitektura"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    def draw(self, context):
        prk = context.window_manager.prk
        layout = self.layout
                
        row = self.layout.split(0.6)
        row.label("Load a preset:")
        row.operator_menu_enum("scene.load_preset", "presetCollection")
        
        layout.separator()
        layout.row().label("Levels:")
        layout.template_list("PLAN_UL_levels", "", prk, "levels", prk, "levelIndex", rows=3)
        
        layout.separator()
        layout.operator("scene.add_item")
        
        layout.separator()
        box = layout.box()
        box.label("New wall settings")
        box.prop(prk, "wallAtRight")
        box.prop(prk, "newWallWidth")
        box.prop(prk, "newWallHeight")


class PanelItem(bpy.types.Panel):
    bl_label = "Prokitektura"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    
    def draw(self, context):
        obj = context.scene.objects.active
        if not (obj and "t" in obj):
            return
        if not obj in pContext.gui:
            # try the parent
            obj = obj.parent
            if not (obj and "t" in obj and obj["t"] in pContext.gui):
                return
        
        layout = self.layout
        guiEntry = pContext.gui[obj["t"]]
        layout.box().label("%s: %s" % (guiEntry[1], obj.name))
        guiEntry[0].draw(context, layout)
        


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


class PrkStudioProperties(bpy.types.PropertyGroup):
    levels = bpy.props.CollectionProperty(type=Level)
    # the name of the Blender object for the current floor
    levelIndex = bpy.props.IntProperty()
    floorName = bpy.props.StringProperty()
    newAtActive = bpy.props.BoolProperty(
        name = "A new item at the active object",
        description = "Adds a new item at the location of the active object, otherwise the 3D cursor location is used for the new item",
        default = False
    )
    wallAtRight = bpy.props.BoolProperty(
        name = "The wall is at the right",
        description = "Defines if the wall is at the right (checked) from control points or at the left (unchecked)",
        default = True
    )
    newWallWidth = bpy.props.FloatProperty(
        name = "Width",
        description = "Width of a new wall",
        default = 0.3,
        min = 0.01,
        max = 10,
        step = 0.1,
        unit = "LENGTH"
    )
    newWallHeight = bpy.props.FloatProperty(
        name = "Height",
        description = "Height of a new wall",
        default = 2.7,
        min = 0.1,
        max = 10,
        step = 0.1,
        unit = "LENGTH"
    )
    wallSegmentWidth = bpy.props.FloatProperty(
        name = "Segment width",
        description = "Width of a wall segment",
        default = 0.3,
        min = 0.01,
        max = 10,
        step = 0.1,
        unit = "LENGTH",
        set = setWidth,
        get = getWidth
    )
    widthForAllSegments = bpy.props.BoolProperty(
        name = "Width for all segments",
        description = "Width for all segments",
        default = False
    )


def register():
    bpy.utils.register_module(__name__)
    wm = bpy.types.WindowManager
    wm.prk = bpy.props.PointerProperty(type=PrkStudioProperties)

def unregister():
    bpy.utils.unregister_module(__name__)
    wm = bpy.types.WindowManager
    del wm.prk