from base import pContext
from item.opening import Opening
from gui.workshop import common


class GuiDoor:
    
    itemName = "door"
    
    def draw(self, context, layout):
        layout.label("A door")
        
    def draw_workshop(self, context, layout):
        common(context, layout, self)
        
        layout.separator()
        layout.label("Handle:")
        box = layout.box()
        box.label("test")


class Door(Opening):

    type = "door"
    
    name = "Door"
    
    floorToWindow = 0.


pContext.register(Door, GuiDoor)