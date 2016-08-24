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
        props = context.scene.prk.item
        common(context, layout, self)
        
        box = layout.box()
        column = box.column(align=True)
        column.label("Asset type:")
        column.row().prop(props.window, "assetType", text = "")
        column.label("Side (left or right):")
        column.row().prop(props, "assetSideLr", text = "")
        column.label("Side (internal or external):")
        column.row().prop(props, "assetSideIe", text = "")
        box.operator("prk.workshop_set_asset_placeholder")
        box.operator("prk.workshop_assign_asset")
        
        layout.separator()
        if context.object and context.object.get("t") in pContext.items:
            layout.prop(props.window, "frame_width")


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


def getFrameWidth(self):
    keyBlock = None
    def lookup(parent):
        for o in parent.children:
            if o.type == "MESH" and o.data.shape_keys:
                keyBlock = o.data.shape_keys.key_blocks.get("frame_width")
                if keyBlock:
                    return keyBlock
            if o.children:
                return lookup(o) 
    # Get the first encountered Blender MESH with the shape key <frame_width>,
    # perform lookup starting from <o> for that
    keyBlock = lookup(bpy.context.object)
    return shapeKeyOffset * keyBlock.value if keyBlock else 0.


pContext.register(Window, GuiWindow)