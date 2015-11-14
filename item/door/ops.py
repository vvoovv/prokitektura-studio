import bpy

from base import appendFromFile
from . import Door
from item.wall import getWallFromEmpty


class AddDoor(bpy.types.Operator):
    bl_idname = "prk.add_door"
    bl_label = "Add a door..."
    bl_description = "Add a door"
    bl_options = {"REGISTER", "UNDO"}
    
    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    
    directory = bpy.props.StringProperty(
        subtype="DIR_PATH"
    )
    
    def invoke(self, context, event):
        o = context.object
        wall = getWallFromEmpty(context, self, o)
        if not wall:
            self.report({"ERROR"}, "To insert a door, select an EMPTY object located at a segment of the wall")
        self.o = o
        self.wall = wall
        
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    
    def execute(self, context):
        obj = appendFromFile(context, self.filepath)
        self.wall.insert(self.o, obj, Door)
        
        bpy.context.scene.objects.active = obj
        obj.select = True
        # Without bpy.ops.transform.translate() some complex stuff (some modifiers)
        # may not be initialized correctly
        bpy.ops.transform.translate()
        return {'FINISHED'}