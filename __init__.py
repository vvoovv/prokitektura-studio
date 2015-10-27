bl_info = {
    "name": "Prokitektura Studio",
    "author": "Vladimir Elistratov <vladimir.elistratov@gmail.com>",
    "version": (0, 0, 0),
    "blender": (2, 7, 5),
    "location": "View3D > Tool Shelf",
    "description": "Flexible architecture",
    "warning": "",
    "wiki_url": "https://github.com/vvoovv/prokitektura-studio/wiki/",
    "tracker_url": "https://github.com/vvoovv/prokitektura-studio/issues",
    "support": "COMMUNITY",
    "category": "Prokitektura"
}

import sys, os, math
def _checkPath():
    path = os.path.dirname(__file__)
    if path not in sys.path:
        sys.path.append(path)
_checkPath()

import base, gui, item, item.wall
import metro
if "bpy" in locals():
    import imp
    imp.reload(base)
    imp.reload(gui)
    imp.reload(item)
    imp.reload(metro)
    imp.reload(item.wall)

import bpy

# a reference to keyboardshortcuts
keymap = None


def register():
    base.register()
    gui.register()
    item.register()
    # register keyboard shortcuts
    wm = bpy.context.window_manager
    global keymap
    if keymap:
        wm.keyconfigs.addon.keymaps.remove(keymap)
    km = wm.keyconfigs.addon.keymaps.new(name="Object Mode")
    # overriding standart Blender shortcut for moving
    km.keymap_items.new("prk.move", "G", "PRESS")
    # shortcut for adding a new wall
    km.keymap_items.new("prk.wall_edit_add", "E", "PRESS", ctrl=True)
    # shortcut for extending the wall
    km.keymap_items.new("prk.wall_edit_extend", "E", "PRESS")
    # shortcut for completing the wall
    km.keymap_items.new("prk.wall_complete", "Q", "PRESS")
    # shortcut to make a floor
    km.keymap_items.new("prk.floor_make", "F", "PRESS", ctrl=True)
    # shortcut to work on a floor
    km.keymap_items.new("prk.floor_work", "F", "PRESS")
    # shortcut to create an adjoing wall
    km.keymap_items.new("prk.wall_attached_start", "D", "PRESS", ctrl=True)
    #kmi.properties.name = ""
    keymap = km


def unregister():
    base.unregister()
    gui.unregister()
    item.unregister()
    # delete shortcuts
    global keymap
    bpy.context.window_manager.keyconfigs.addon.keymaps.remove(keymap)