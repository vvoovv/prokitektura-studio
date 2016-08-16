import bpy
from base import pContext
from item.opening import Opening
from gui.workshop import common

from workshop.node import shapeKeyOffset


class GuiWindow:
    
    itemName = "window"
    
    def draw(self, context, layout):
        layout.label("A window")
    
    def draw_workshop(self, context, layout):
        common(context, layout, self)
        
        layout.separator()
        layout.prop(context.scene.prk.item.window, "frame_width")
        layout.label("Handle:")
        box = layout.box()
        box.label("test")


class Window(Opening):

    type = "window"
    
    name = "Window"
    
    floorToWindow = 0.75
    
    allowZ = True


def setFrameWidth(self, value):
    o = bpy.context.object
    if not (o and o.get("t") == Window.type):
        return
    def lookup(parent):
        for o in parent.children:
            if o.type == "MESH" and o.data.shape_keys:
                keyBlock = o.data.shape_keys.key_blocks.get("frame_width")
                if keyBlock:
                    keyBlock.value = value/shapeKeyOffset
            if o.children:
                lookup(o) 
    # perform lookup starting from <o>
    lookup(o)


pContext.register(Window, GuiWindow)