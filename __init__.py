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

import base, gui
import metro
if "bpy" in locals():
    import imp
    imp.reload(base)
    imp.reload(gui)
    imp.reload(metro)

import bpy

# a reference to keyboardshortcuts
keymap = None


def register():
    gui.register()
    # register keyboard shortcuts
    wm = bpy.context.window_manager
    global keymap
    if keymap:
        wm.keyconfigs.addon.keymaps.remove(keymap)
    km = wm.keyconfigs.addon.keymaps.new(name="Object Mode")
    # shortcut for adding a new wall
    km.keymap_items.new("object.wall_edit_add", "E", "PRESS")
    # shortcut for extending the wall
    km.keymap_items.new("object.wall_edit_extend", "D", "PRESS")
    # shortcut for completing the wall
    km.keymap_items.new("object.wall_complete", "Q", "PRESS")
    # shortcut to work on a floor
    km.keymap_items.new("object.floor_work", "F", "PRESS")
    #kmi.properties.name = ""
    keymap = km
        

def unregister():
    gui.unregister()
    # delete shortcuts
    global keymap
    bpy.context.window_manager.keyconfigs.addon.keymaps.remove(keymap)