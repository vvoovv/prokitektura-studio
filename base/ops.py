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


class CustomizeGui(bpy.types.Operator):
    bl_idname = "prk.customize"
    bl_label = "Customize Blender GUI"
    bl_description = "Customize default Blender GUI: keep only GUI for Prokitektura"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        un = bpy.utils.unregister_class
        # Tools panel
        un(bpy.types.VIEW3D_PT_tools_transform)
        un(bpy.types.VIEW3D_PT_tools_object)
        un(bpy.types.VIEW3D_PT_tools_history)
        # Create panel
        un(bpy.types.VIEW3D_PT_tools_add_object)
        # Relations panel
        un(bpy.types.VIEW3D_PT_tools_relations)
        # Animation panel
        un(bpy.types.VIEW3D_PT_tools_animation)
        # Physics panel
        un(bpy.types.VIEW3D_PT_tools_rigid_body)
        # Grease Pencil
        un(bpy.types.VIEW3D_PT_tools_grease_pencil_draw)
        return {'FINISHED'}