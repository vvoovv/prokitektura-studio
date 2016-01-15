import bpy
from base import pContext, getModelParent


def updateHeight(bundle, context):
    # update height and position for all levels
    prk = context.scene.prk
    # build a dictionary of all level parents up
    levels = {}
    parent = getModelParent(context)
    for o in parent.children:
        if "level" in o:
            levels[o["level"]] = o
        elif "h" in o:
            totalHeight = o
    h = 0.
    update = False
    for l in prk.levels:
        if update:
            levels[l.index].location.z = h
        else:
            update = True
        h += prk.levelBundles[l.bundle].height
    totalHeight.location.z = h


class PLAN_UL_levels(bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_property):
        bundle = context.scene.prk.levelBundles[item.bundle]
        
        split = layout.split(percentage=0.8)
        split.prop(item, "name", text="", emboss=False, icon="RENDERLAYERS")
        row = split.row()
        row.label(bundle.symbol)
        icon = 'VISIBLE_IPO_ON' if item.visible else 'VISIBLE_IPO_OFF'
        row.prop(item, "visible", text="", emboss=False, icon=icon)


class Level(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(
        description="Level index"
    )
    name = bpy.props.StringProperty(
        description="Level name"
    )
    bundle = bpy.props.IntProperty(
        subtype='UNSIGNED',
        description="Index of a level bundle (see LevelBundle)"
    )
    visible = bpy.props.BoolProperty(
        description="",
        default=True
    )


class LevelBundle(bpy.types.PropertyGroup):
    symbol = bpy.props.StringProperty(
        name = "",
        description="Symbol used to identify the bundle in the GUI"
    )
    height = bpy.props.FloatProperty(
        name = "Height",
        description = "Level height",
        min = 0.1,
        max = 10,
        step = 0.1,
        unit = "LENGTH",
        update = updateHeight
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


class AddLevel(bpy.types.Operator):
    bl_idname = "prk.level_add"
    bl_label = "Add level(s)"
    bl_description = "Add the specified number of levels"
    bl_options = {"REGISTER", "UNDO"}
    
    # a symbol is used to mark a LevelBundle
    symbols = "ABCDEFGHIJ"
    
    def invoke(self, context, event):
        prk = context.scene.prk
        levels = prk.levels
        bundles = prk.levelBundles
        # create a new LevelBundle
        bundleIndex = len(bundles)
        bundle = bundles.add()
        bundle.symbol = self.symbols[bundleIndex % len(self.symbols)]
        bundle.height = prk.newLevelHeight
        # create level(s) for the just created LevelBundle
        levelIndex = len(levels)
        for _ in range(prk.numNewLevels):
            level = levels.add()
            level.index = levelIndex
            level.name = "Level "+str(levelIndex)
            level.bundle = bundleIndex
            levelIndex += 1
        return {'FINISHED'}