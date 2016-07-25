from base import pContext
from item.opening import Opening
from gui.workshop import common


class GuiWindow:
    
    itemName = "window"
    
    def draw(self, context, layout):
        layout.label("A window")
    
    def draw_workshop(self, context, layout):
        common(context, layout, self)
        
        layout.separator()
        layout.label("Handle:")
        box = layout.box()
        box.label("test")


class Window(Opening):

    type = "window"
    
    name = "Window"
    
    floorToWindow = 0.75
    
    allowZ = True


pContext.register(Window, GuiWindow)