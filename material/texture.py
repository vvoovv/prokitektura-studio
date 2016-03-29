import bpy
from base import defaultUvMap, materialsPath
from util.blender import loadMaterialFromFile


materialName = "Texture"


class Texture:
    """
    A proxy for Blender material made of a diffuse texture from a file
    """
    def __init__(self, createBlenderMaterial=False, **kwargs):
        if createBlenderMaterial:
            self.m = self.create(kwargs)
    
    def create(self, kwargs):
        m = loadMaterialFromFile(materialsPath, materialName)
        nodes = m.node_tree.nodes
        nodes["Image Texture"].image = bpy.data.images.load(kwargs["texturePath"])
        n = nodes["Mapping"]
        w, h = 3., 2.7
        n.scale.x = 1/w
        n.scale.y = 1/h
        nodes["UV Map"].uv_map = defaultUvMap
        return m