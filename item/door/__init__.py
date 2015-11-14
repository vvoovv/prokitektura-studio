from base import pContext
from item.opening import Opening


class GuiDoor:
    
    def draw(self, context, layout):
        layout.label("A door")


class Door(Opening):

    type = "door"
    
    name = "Door"
    
    floorToWindow = 0.


pContext.register(Door, GuiDoor)