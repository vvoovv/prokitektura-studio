import bpy

from . import getItem

class Move(bpy.types.Operator):
    bl_idname = "prk.move"
    bl_label = "Move an object"
    bl_description = "Move an object"
    bl_options = {"REGISTER", "UNDO"}
    
    def modal(self, context, event):
        return self.item.move_modal(self, context, event, context.scene.objects.active)
    
    def invoke(self, context, event):
        if len(context.selected_objects) == 1:
            o = context.selected_objects[0]
            item = getItem(context, self, o)
            if not item or item.moveFreely:
                # perform standard Blender translation
                bpy.ops.transform.translate("INVOKE_DEFAULT")
                return {'FINISHED'}
            self.item = item
            return item.move_invoke(self, context, event, o)
        else:
            # perform standard Blender translation
            bpy.ops.transform.translate("INVOKE_DEFAULT")
            return {'FINISHED'}