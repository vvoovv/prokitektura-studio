from item.wall.ops import *
from item.window.ops import *
from item.floor.ops import *

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)