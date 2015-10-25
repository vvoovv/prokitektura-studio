import bpy
from mathutils import Vector

xAxis = Vector((1., 0., 0.))
yAxis = Vector((0., 1., 0.))
zAxis = Vector((0., 0., 1.))

zero = 0.000001
zero2 = 0.0005


def strf(value):
    "Returns a rounded float value as a string"
    # rounding leads to calculation errors, so skip it
    #return str(round(value, 4))
    return str(value)


def getLevelHeight(context):
    prk = context.window_manager.prk
    try:
        height = prk.levels[prk.levelIndex].z
    except:
        height = 0.
    return height


def getLevelLocation(context):
    loc = context.scene.cursor_location.copy()
    loc.z = getLevelHeight(context)
    return loc


def getItem(context, op, o):
    """
    Returns an instance of Prokitektura class related to the Blender object <o>, supplied as input parameter
    """
    item = None
    if "t" in o:
        # keep <o> and its parent
        _o = o
        parent = o.parent
        if not o["t"] in pContext.items and o.parent and "t" in parent:
            # try the parent
            o = parent
        if o["t"] in pContext.items:
            item = pContext.items[o["t"]][0](context, op)
            item.init(parent, _o)
    return item


class Context:
    
    # a registry to store references to Blender operators responsible for specific categories
    classes = {}
    
    # a registry to store data related to items
    items = {}
    
    def __init__(self):
        self.presetCollections = {}
        
    def loadPresetCollection(self, _id):
        if not _id in self.presetCollections: return
        self.presetCollections[_id]()
    
    def register(self, Cls, GuiCls):
        self.items[Cls.type] = (Cls, GuiCls())
    
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
        prk = bpy.context.window_manager.prk
        prk.levels.clear()
        # reset levelIndex (i.e. currently active level)
        prk.levelIndex = 0
        level = prk.levels.add()
        level.name = "Ground floor"
        level.z = 0.


def init():
    pContext.presetCollections[FloorPlan.id] = FloorPlan

init()

from .ops import *

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)