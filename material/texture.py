import bpy
from base import pContext, defaultUvMap, materialsPath
from util.blender import loadMaterialFromFile
from material.base import getMaterialNodes


materialName = "Texture"


def getTextureWidth(self):
    n = getMaterialNodes(bpy.context)["Mapping"]
    return 1./n.scale.x

def setTextureWidth(self, value):
    n = getMaterialNodes(bpy.context)["Mapping"]
    n.scale.x = 1./value

def getTextureHeight(self):
    n = getMaterialNodes(bpy.context)["Mapping"]
    return 1./n.scale.y

def setTextureHeight(self, value):
    n = getMaterialNodes(bpy.context)["Mapping"]
    n.scale.y = 1./value
    

class GuiTexture:
    
    def draw(self, context, layout):
        n = getMaterialNodes(context)
        split = layout.split(percentage=0.25)
        split.label("Texture:")
        split.template_ID(n["Image Texture"], "image", open="image.open")
        prk = context.scene.prk
        layout.prop(prk, "textureWidth")
        layout.prop(prk, "textureHeight")
        


class Texture:
    """
    A proxy for Blender material made of a diffuse texture from a file
    """
    
    type = "texture"
    
    def __init__(self, createBlenderMaterial=False, **kwargs):
        if createBlenderMaterial:
            self.m = self.create(kwargs)
    
    def create(self, kwargs):
        m = loadMaterialFromFile(materialsPath, materialName)
        nodes = m.node_tree.nodes
        nodes["Image Texture"].image = bpy.data.images.load(kwargs["texturePath"])
        if "w" in kwargs and "h" in kwargs:
            n = nodes["Mapping"]
            n.scale.x = 1./kwargs["w"]
            n.scale.y = 1./kwargs["h"]
        nodes["UV Map"].uv_map = defaultUvMap
        return m


pContext.register(Texture, GuiTexture)