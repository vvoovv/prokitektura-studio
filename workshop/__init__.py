import bpy
from base import pContext
from .ops import *


class PanelWorkshop(bpy.types.Panel):
    bl_label = "Workshop"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "mesh_edit" # objectmode
    bl_category = "Workshop@Prokitektura"
    
    def draw(self, context):
        layout = self.layout
        prk = context.scene.prk
        
        layout.prop(prk, "workshopType")
        layout.separator()
        
        if not prk.workshopType in pContext.items:
            return
        
        pContext.items[prk.workshopType][1].draw_workshop(context, layout)
        


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)