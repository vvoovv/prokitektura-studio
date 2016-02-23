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
        if update and l.index in levels:
            levels[l.index].location.z = h
        else:
            update = True
        h += prk.levelBundles[l.bundle].height
    totalHeight.location.z = h


def toggleLayerVisibility(level, context):
    hide = not level.visible
    parent = getModelParent(context)
    if not parent:
        return
    # find the related level parent Blender object
    for o in parent.children:
        if "level" in o and o["level"] == level.index:
            toggleObjectVisibility(o, hide)


def toggleObjectVisibility(o, hide):
    if hide:
        if o.hide:
            # Mark it that is shouldn't appear visible,
            # when we set the level visibility to "visible"
            o["_"] = 1
        else:
            o.hide = True
    else:
        if "_" in o:
            del o["_"]
        else:
            o.hide = False
    for _o in o.children:
        toggleObjectVisibility(_o, hide)


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
        default=True,
        update=toggleLayerVisibility
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


# a symbol is used to mark a LevelBundle
bundleSymbols = "ABCDEFGHIJ"

class AddLevel(bpy.types.Operator):
    bl_idname = "prk.level_add"
    bl_label = "Add level(s)"
    bl_description = "Add the specified number of levels"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        prk = context.scene.prk
        levels = prk.levels
        bundles = prk.levelBundles
        # create a new LevelBundle
        bundleIndex = len(bundles)
        bundle = bundles.add()
        bundle.symbol = bundleSymbols[bundleIndex % len(bundleSymbols)]
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


class RemoveLevel(bpy.types.Operator):
    bl_idname = "prk.level_remove"
    bl_label = "Remove level"
    bl_description = "Remove the active level"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        prk = context.scene.prk
        levelIndex = prk.levelIndex
        levels = prk.levels
        level = prk.levels[levelIndex]
        bundle = level.bundle
        
        levels.remove(levelIndex)
        bundles = prk.levelBundles
        if levels:
            # check if we need to remove the bundle, i.e. <level> is the last one in the bundle
            removeBundle = False
            if levelIndex == 0:
                if levels[0].bundle != bundle:
                    removeBundle = True
            elif levelIndex == len(levels):
                if levels[-1].bundle != bundle:
                    removeBundle = True
            elif levels[levelIndex-1].bundle != bundle and levels[levelIndex].bundle != bundle:
                removeBundle = True
            if removeBundle:
                bundles.remove(bundle)
                if bundle < len(bundles):
                    # we need to update symbols for the bundles to ensure consistency
                    for bundleIndex in range(bundle, len(bundles)):
                        bundles[bundleIndex].symbol = bundleSymbols[bundleIndex % len(bundleSymbols)]
                    # we need to update bundle index for the levels to ensure consistency
                    for level in levels:
                        if level.bundle > bundle:
                            level.bundle -= 1
        else:
            bundles.clear()
        return {'FINISHED'}