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
        prk = bpy.context.window_manager.prk
        prk.levels.clear()
        # reset levelIndex (i.e. currently active level)
        prk.levelIndex = 0
        level = prk.levels.add()
        level.name = "Platform"
        level.z = 0.
        level = prk.levels.add()
        level.name = "Vestibule"
        level.z = 6.


pContext.presetCollections[Metro.id] = Metro
