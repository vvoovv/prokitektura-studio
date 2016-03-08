import bpy
from mathutils import Vector

xAxis = Vector((1., 0., 0.))
yAxis = Vector((0., 1., 0.))
zAxis = Vector((0., 0., 1.))

zero = 0.000001
zero2 = 0.0001


def strf(value):
    "Returns a rounded float value as a string"
    # rounding leads to calculation errors, so skip it
    #return str(round(value, 4))
    return str(value)


def appendFromFile(context, filepath):
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.objects = data_from.objects
    # append all objects and find their parent
    parent = None
    for obj in data_to.objects:
        if not parent and not obj.parent:
            parent = obj
        bpy.context.scene.objects.link(obj)
    # perform cleanup
    bpy.ops.object.select_all(action="DESELECT")
    # return the parent object
    return parent


def getLevelZ(context, levelIndex):
    prk = context.scene.prk
    z = 0.
    for i in range(levelIndex):
        z += prk.levelBundles[prk.levels[i].bundle].height
    return z


def getLevelLocation(context):
    loc = context.scene.cursor_location.copy()
    loc.z = 0
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
            item.init(_o)
    return item


def getModelParent(context):
    """Returns the parent model for the whole model or None"""
    parent = None
    for o in context.scene.objects:
        if not o.parent and "t" in o and o["t"] == "model":
            parent = o
            break
    return parent


class Context:
    
    # a registry to store references to Blender operators responsible for specific categories
    classes = {}
    
    # a registry to store data related to items
    items = {}
    
    def register(self, Cls, GuiCls, *extraTypes):
        gui = GuiCls() if GuiCls else None
        self.items[Cls.type] = (Cls, gui)
        for t in extraTypes:
            self.items[t] = (Cls, gui)
    
    def register_class(self, _id, cl):
        if not _id in self.classes:
            bpy.utils.register_class(cl)
            self.classes[_id] = cl

pContext = Context()


def init():
    pass

init()

from .ops import *

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)