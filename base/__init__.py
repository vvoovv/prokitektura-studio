import os
import bpy
from mathutils import Vector

xAxis = Vector((1., 0., 0.))
yAxis = Vector((0., 1., 0.))
zAxis = Vector((0., 0., 1.))

zeroVector = Vector((0., 0., 0.))

zero = 0.000001
zero2 = 0.0001

defaultUvMap = "UVMap"


def strf(value):
    "Returns a rounded float value as a string"
    # rounding leads to calculation errors, so skip it
    #return str(round(value, 4))
    return str(value)


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


def getLevelHeight(context, o):
    """Returns the height of the levels where the Blender object <o> is located"""
    prk = context.scene.prk
    levelIndex = o.parent["level"]
    for i,l in enumerate(prk.levels):
        if l.index == levelIndex:
            levelIndex = i
            break
    return prk.levelBundles[prk.levels[levelIndex].bundle].height


def getNextLevelParent(context, o):
    """Returns the parent for the level located on top of level of the Blender object <o>"""
    # Optional levelOffset refers to GUI level index offset in the GUI list of levels
    prk = context.scene.prk
    index = o.parent["level"]
    # check if <o> is located in the last level
    if index == prk.levels[-1].index:
        # return EMPTY controlling the total height of the building
        result = getTotalHeightEmpty(context, o)
    else:
        # Iterate through the GUI list of levels to find the level
        # on top of the level with the index equal to <index>
        for i,l in enumerate(prk.levels):
            if l.index == index:
                break
        index = prk.levels[i+1].index
        for l in o.parent.parent.children:
            if "level" in l and l["level"] == index:
                result = l
                break
    return result


def getTotalHeightEmpty(context, o):
    """
    Returns EMPTY object controlling the total height of the building
    in one level of which the Blender object <o> is located
    """ 
    for l in o.parent.parent.children:
        if "h" in l and l["h"]:
            return l

 
def getReferencesForAttached(o):
    """
    Get reference EMPTYs for the wall segment to which <o> is attached.
    """
    variables = o.animation_data.drivers[0].driver.variables
    # <variableIndex> depends on the role of <o> (active or passive)
    variableIndex = 0 if len(variables)==3 else 5
    return variables[variableIndex].targets[0].id, variables[variableIndex+1].targets[0].id


def getControlEmptyFromLoop(loop, layer, obj):
    """
    Get EMPTY controlling the vertex via a HOOK modifier given the related loop
    
    Args:
        loop (bmesh.types.BMLoop): the loop related to the vertex in question
        layer (bmesh.types.BMLayerItem): the related layer
        obj: the Blender object containing the vertex in question
    """
    # the variable below is actually a group index
    g = loop.vert[layer].keys()[0]
    g = obj.vertex_groups[g].name
    return obj.modifiers[g].object


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
assetsPath = ""
materialsPath = ""

def init():
    global assetsPath, materialsPath
    # find the path to the assets
    # first, the path to the module's directory
    p = os.path.dirname(os.path.realpath(__file__))
    # second, the path to the whole distribution
    p = os.path.join(p, os.pardir)
    # finally, the path to the assets
    assetsPath = os.path.join(p, "assets")
    materialsPath = os.path.join(assetsPath, "materials.blend")

init()

from .ops import *

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)