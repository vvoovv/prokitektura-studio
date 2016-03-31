from base import pContext
from . import Area


class GuiRoom:
    
    def draw(self, context, layout):
        o = context.scene.objects.active
        layout.prop(o, "name")
        layout.operator("prk.set_material_from_texture")
        layout.operator("prk.extruded_add")


class Room(Area):
    type = "room"
    name = "Room"


pContext.register(Room, GuiRoom)