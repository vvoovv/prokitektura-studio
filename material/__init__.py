"""
The package contains the code to deal with Blender materials
"""

import bpy
from .ops import *


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)