import bpy

from base import pContext
from base import getLevelLocation
from util.blender import appendFromFile, getMaterial, makeActiveSelected

from material.texture import setTextureWidth, getTextureWidth, setTextureHeight, getTextureHeight

from .levels import PLAN_UL_levels, Level, LevelBundle, AddLevel


class PanelLevels(bpy.types.Panel):
    bl_label = "Levels"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Main@Prokitektura"
    
    def draw(self, context):
        prk = context.scene.prk
        layout = self.layout
        
        box = layout.box()
        box.prop(prk, "numNewLevels")
        box.operator("prk.level_add", icon='ZOOMIN')
        layout.template_list("PLAN_UL_levels", "", prk, "levels", prk, "levelIndex", rows=3)
        if prk.levels:
            # active level
            level = prk.levels[prk.levelIndex]
            layout.prop(prk.levelBundles[level.bundle], "height")
            layout.operator("prk.level_remove", icon='ZOOMOUT')


class PanelNewWall(bpy.types.Panel):
    bl_label = "New wall"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Main@Prokitektura"
    
    @classmethod
    def poll(cls, context):
        return context.scene.prk.levels
    
    def draw(self, context):
        prk = context.scene.prk
        
        layout = self.layout
        
        box = layout.box()
        box.row().prop(prk, "newWallType", expand=True)
        # height mode FIXME
        #row = box.row() FIXME
        #row.label("Wall height:") FIXME
        #row.prop(prk, "newWallHeightMode", expand=True) FIXME
        box.prop(prk, "wallAtRight")
        box.prop(prk, "newWallWidth")


class PanelAddItem(bpy.types.Panel):
    bl_label = "Add item"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Main@Prokitektura"
    
    @classmethod
    def poll(cls, context):
        return context.scene.prk.levels
    
    def draw(self, context):
        self.layout.operator("prk.add_item")


class PanelItem(bpy.types.Panel):
    bl_label = "Selected"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Selected@Prokitektura"
    
    def draw(self, context):
        o = context.scene.objects.active
        if not (o and "t" in o):
            return
        if not o["t"] in pContext.items:
            # try the parent
            o = o.parent
            if not (o and "t" in o and o["t"] in pContext.items):
                return
        
        layout = self.layout
        guiEntry = pContext.items[o["t"]]
        layout.box().label("%s: %s" % (guiEntry[0].name, o.name))
        if guiEntry[1]:
            guiEntry[1].draw(context, layout)


class PanelMaterial(bpy.types.Panel):
    bl_label = "Prokitektura"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    @classmethod
    def poll(cls, context):
        o = context.scene.objects.active
        return o.type == "MESH" and "t" in o and o.data.materials and "t" in o.data.materials[0]
    
    def draw(self, context):
        m = getMaterial(context)
        
        guiEntry = pContext.items[m["t"]]
        guiEntry[1].draw(context, self.layout)


class AddItem(bpy.types.Operator):
    bl_idname = "prk.add_item"
    bl_label = "Add an item..."
    bl_description = "Add an item"
    bl_options = {"REGISTER", "UNDO"}
    
    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    
    def invoke(self, context, event):
        self.filepath = ""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    
    def execute(self, context):
        obj = appendFromFile(context, self.filepath)
        # mark parent object as a container
        obj["container"] = 1
        obj.location = getLevelLocation(context)
        makeActiveSelected(context, obj)
        # Without bpy.ops.transform.translate() some complex stuff (some modifiers)
        # may not be initialized correctly
        bpy.ops.transform.translate()
        return {'FINISHED'}


from item.window import setFrameWidth, getFrameWidth
class PrkWindowProperties(bpy.types.PropertyGroup):
    frame_width = bpy.props.FloatProperty(
        name = "Frame width increment",
        description = "Increment (positive or negative) of the default frame width from its default value",
        min = -0.1,
        max = 0.1,
        step = 0.001,
        unit = "LENGTH",
        default = 0.,
        set = setFrameWidth,
        get = getFrameWidth
    )
    assetType = bpy.props.EnumProperty(
        items = [
            ("handle", "handle", "handle"),
            ("hinges", "hinges", "hinges"),
            ("silling", "silling", "silling")
        ],
        name = "Asset type"
    )

class PrkItemProperties(bpy.types.PropertyGroup):
    window = bpy.props.PointerProperty(type=PrkWindowProperties)
    # Lr means left or right
    assetSideLr = bpy.props.EnumProperty(
        items = [
            ("l", "left", "left"),
            ("r", "right", "right"),
            ("n", "none", "none")
        ],
        name = "Asset side (left or right)"
    )
    # Ie means internal or external
    assetSideIe = bpy.props.EnumProperty(
        items = [
            ("i", "internal", "internal"),
            ("e", "external", "external"),
            ("n", "none", "none")
        ],
        name = "Asset side (internal or external)",
        default = "n"
    )

from item.wall import setWidth, getWidth, setLength, getLength
class PrkStudioProperties(bpy.types.PropertyGroup):
    workshopType = bpy.props.EnumProperty(
        items = [
            ("window", "window", "Window"),
            ("door", "door", "Door")
        ],
        name = "Workshop type",
        description = "Workshop type (e.g. window, door, ...)",
        default = "window"                
    )
    item = bpy.props.PointerProperty(type=PrkItemProperties)
    levelBundles = bpy.props.CollectionProperty(type=LevelBundle)
    levels = bpy.props.CollectionProperty(type=Level)
    levelIndex = bpy.props.IntProperty(
        description = "Index of the active level"
    )
    areaType = bpy.props.EnumProperty(
        items = [
            ("room", "room", "Create a room"),
            ("floor", "floor", "Create a floor")
        ],
        description = "The type of the area (room or floor) to be created",
        default = "room"
    )
    areaName = bpy.props.StringProperty(
        description = "The name of the Blender object for the current area"
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
        max = 10.,
        step = 0.1,
        unit = "LENGTH"
    )
    wallSegmentWidth = bpy.props.FloatProperty(
        name = "Segment width",
        description = "Width of a wall segment",
        min = 0.01,
        max = 1000.,
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
    wallSegmentLength = bpy.props.FloatProperty(
        name = "Segment length",
        description = "Length of a wall segment",
        min = 0.01,
        max = 1000.,
        step = 0.1,
        unit = "LENGTH",
        set = setLength,
        get = getLength
    )
    newWallType = bpy.props.EnumProperty(
        items = [
            ("external", "external", "Create an external wall"),
            ("internal", "internal", "Create an internal wall")
        ]
    )
    #newWallHeightMode = bpy.props.EnumProperty( FIXME
    #    items = [ FIXME
    #        ("whole", "whole building", "Total height of all levels"), FIXME
    #        ("custom", "custom", "Custom height defined by the specified levels") FIXME
    #    ]
    #) FIXME
    newLevelHeight = bpy.props.FloatProperty(
        name = "Height",
        description = "Height of a new level",
        default = 2.7,
        min = 0.1,
        max = 10.,
        step = 0.1,
        unit = "LENGTH"
    )
    numNewLevels = bpy.props.IntProperty(
        name = "Number of levels",
        subtype = 'UNSIGNED',
        min = 1,
        max = 200,
        default = 1,
        description="Number of levels to be created. The levels will belong to the same level bundle."
    )
    textureWidth = bpy.props.FloatProperty(
        name = "Texture width",
        description = "Texture width in meters",
        default = 1.,
        min = 0.1,
        max = 10.,
        step = 0.1,
        unit = "LENGTH",
        set = setTextureWidth,
        get = getTextureWidth
    )
    textureHeight = bpy.props.FloatProperty(
        name = "Texture height",
        description = "Texture height in meters",
        default = 1.,
        min = 0.1,
        max = 10.,
        step = 0.1,
        unit = "LENGTH",
        set = setTextureHeight,
        get = getTextureHeight
    )


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.prk = bpy.props.PointerProperty(type=PrkStudioProperties)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.prk