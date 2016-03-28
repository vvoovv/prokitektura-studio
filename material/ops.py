import bpy
from util.blender import setMaterial
from .texture import Texture


class MaterialFromTexture(bpy.types.Operator):
    bl_idname = "prk.set_material_from_texture"
    bl_label = "Set texture..."
    bl_description = "Set a Blender material from the selected texture"
    bl_options = {"REGISTER", "UNDO"}
    
    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    
    def execute(self, context):
        material = Texture(True, texturePath=self.filepath)
        setMaterial(context.object, material.m)
        return {'FINISHED'}