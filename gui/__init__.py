import bpy

from blender_util import modifier_apply_all

from base import pContext
from base import getLevelLocation, appendFromFile

from item.wall import setWidth, getWidth


class PanelMain(bpy.types.Panel):
    bl_label = "Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Prokitektura"
    
    def draw(self, context):
        prk = context.window_manager.prk
        layout = self.layout
                
        #row = self.layout.split(0.6)
        #row.label("Load a preset:")
        #row.operator_menu_enum("scene.load_preset", "presetCollection")
        
        #layout.separator()
        #layout.row().label("Levels:")
        #layout.template_list("PLAN_UL_levels", "", prk, "levels", prk, "levelIndex", rows=3)
        
        #layout.separator()
        layout.operator("prk.add_item")
        
        layout.separator()
        box = layout.box()
        box.label("New wall settings")
        box.prop(prk, "wallAtRight")
        box.prop(prk, "newWallWidth")
        box.prop(prk, "newWallHeight")
        
        # a kind of test that Blend4Web is installed
        if hasattr(context.scene, "b4w_export_path_html"):
            layout.separator()
            layout.operator("export_scene.prk_b4w_html")


class PanelItem(bpy.types.Panel):
    bl_label = "Selected"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Prokitektura"
    
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
        guiEntry[1].draw(context, layout)
        


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
        bpy.context.scene.objects.active = obj
        obj.select = True
        # Without bpy.ops.transform.translate() some complex stuff (some modifiers)
        # may not be initialized correctly
        bpy.ops.transform.translate()
        return {'FINISHED'}


class ExportB4wHtml(bpy.types.Operator):
    bl_idname = "export_scene.prk_b4w_html"
    bl_label = "Export the scene for Blend4Web (.html)"
    bl_description = "Export the scene for Blend4Web (.html)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        
        def processHierarchy(o, dupliObjects, dupliObject):
            if o.hide and o.type=="MESH":
                o.b4w_do_not_export = True
            # dupliObject is the top dupli object in the current hierarchy
            # dupliObject doesn't have any dupli object as an ancestor
            if not dupliObject and o.dupli_type != "NONE" and not "container" in o:
                dupliObject = o
                dupliObjects.append(o)
            # if there is a dupli object in the current hierarchy, apply all modifiers to the object <o>
            if dupliObject and o.modifiers:
                modifier_apply_all(o)
                if o.b4w_apply_modifiers:
                    o.b4w_apply_modifiers = False
            for _o in o.children:
                processHierarchy(_o, dupliObjects, dupliObject)
        
        def invert_selection(_o):
            for o in _o.children:
                if not o.select and o.hide_select:
                    o.hide_select = False
                o.select = not o.select
                invert_selection(o)
        
        def shared_mesh_and_vertex_groups(_o):
            # Treat the case if a MESH object has shared MESH data and vertex groups
            # Blend4Web fails to perform export in that case
            for o in _o.children:
                if o.type == "MESH" and o.data.users > 1 and o.vertex_groups:
                    # delete vertex groups
                    o.vertex_groups.clear()
                shared_mesh_and_vertex_groups(o)
        
        bpy.ops.object.select_all(action="DESELECT")
        
        dupliObjects = []
        # prepare the active scene for export
        for o in context.scene.objects:
            # find top level parent objects
            if not o.parent and o.children:
                processHierarchy(o, dupliObjects, None)
            o.select = False
            if o.modifiers:
                o.b4w_apply_modifiers = True
        
        for o in dupliObjects:
            # make duplicates real for the whole hierarchy
            o.hide_select = False
            o.select = True
            bpy.ops.object.duplicates_make_real(use_base_parent=True)
            # delete original children of _obj to avoid duplication of objects
            o.select = False
            invert_selection(o)
            bpy.ops.object.delete()
            
            shared_mesh_and_vertex_groups(o)
        
        bpy.ops.export_scene.b4w_html("INVOKE_DEFAULT", do_autosave=False)
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