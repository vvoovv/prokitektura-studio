import bpy

from . import getItem

class Move(bpy.types.Operator):
    bl_idname = "prk.move"
    bl_label = "Move an object"
    bl_description = "Move an object"
    bl_options = {"REGISTER", "UNDO"}
    
    def modal(self, context, event):
        return self.move_modal(self, context, event)
    
    def invoke(self, context, event):
        if len(context.selected_objects) == 1:
            item = getItem(context, self, context.selected_objects[0])
            if not item:
                return {'FINISHED'}
            self.item = item
            return item.move_invoke(self, context, event)
        else:
            # make standard Blender translation
            bpy.ops.transform.translate("INVOKE_DEFAULT")
            return {'FINISHED'}