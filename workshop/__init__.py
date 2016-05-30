import bpy
from .ops import *


class PanelWorkshop(bpy.types.Panel):
    bl_label = "Workshop"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "mesh_edit" # objectmode
    bl_category = "Workshop@Prokitektura"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("prk.workshop_start_window")
        layout.operator("prk.workshop_add_pane")
        layout.operator("prk.workshop_assign_node")
        layout.operator("prk.workshop_set_child_offset")
        layout.operator("prk.workshop_make_window")


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)