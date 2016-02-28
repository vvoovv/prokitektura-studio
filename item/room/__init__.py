from base import pContext
from item.area import Area


class GuiRoom:
    
    def draw(self, context, layout):
        o = context.scene.objects.active
        layout.prop(o, "name")


class Room(Area):
    type = "room"
    name = "Room"


pContext.register(Room, GuiRoom)