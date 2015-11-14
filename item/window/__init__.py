from base import pContext
from item.opening import Opening


class GuiWindow:
    
    def draw(self, context, layout):
        layout.label("A window")


class Window(Opening):

    type = "window"
    
    name = "Window"
    
    floorToWindow = 0.75
    
    allowZ = True


pContext.register(Window, GuiWindow)