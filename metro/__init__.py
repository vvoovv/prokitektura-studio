import bpy

from base import pContext


class Metro():
    """
    A preset collection for a metro
    """
    
    id = "metro"
    name = "metro"
    description = "A 3D plan for metro"
    
    def __init__(self):
        
        # clean up levels
        wm = bpy.context.window_manager
        wm.levels.clear()
        # reset levelIndex (i.e. currently active level)
        wm.levelIndex = 0
        level = wm.levels.add()
        level.name = "Platform"
        level.z = 0.
        level = wm.levels.add()
        level.name = "Vestibule"
        level.z = 8.


pContext.presetCollections[Metro.id] = Metro
