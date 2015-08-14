import bpy
from mathutils import Vector

xAxis = Vector((1., 0., 0.))
yAxis = Vector((0., 1., 0.))
zAxis = Vector((0., 0., 1.))

zero = 0.000001


def getLevelHeight(context):
    wm = context.window_manager
    try:
        height = wm.levels[wm.levelIndex].z
    except:
        height = 0.
    return height


def getLevelLocation(context):
    loc = context.scene.cursor_location.copy()
    loc.z = getLevelHeight(context)
    return loc


def getItem():
    return context.plan.presets[context.blenderContext.window_manager.sequencePreset][0]


def getPresetAttr(attr):
    preset = context.plan.presets[context.blenderContext.window_manager.sequencePreset]
    # preset is actually a tuple
    if preset[0].hasPresets:
        obj = preset[2] if hasattr(preset[2], attr) else preset[0]
    else:
        obj = preset[0]
    return getattr(obj, attr, None)
        

class Context:
    
    # a registry to store references to Blender operators responsible for specific categories
    classes = {}
    
    def __init__(self):
        self.presetCollections = {}
        
    def loadPresetCollection(self, _id):
        if not _id in self.presetCollections: return
        self.presetCollections[_id]()
    
    def register_class(self, _id, cl):
        if not _id in self.classes:
            bpy.utils.register_class(cl)
            self.classes[_id] = cl

pContext = Context()


class FloorPlan():
    """
    A preset collection for a basic floor plan
    """
    
    id = "base"
    name = "basic floor plan"
    description = "A basic floor plan"
    
    def __init__(self):
        # clean up levels
        wm = bpy.context.window_manager
        wm.levels.clear()
        # reset levelIndex (i.e. currently active level)
        wm.levelIndex = 0
        level = wm.levels.add()
        level.name = "Ground floor"
        level.z = 0.


def init():
    pContext.presetCollections[FloorPlan.id] = FloorPlan

init()