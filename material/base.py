from util.blender import getMaterial


def getMaterialNodes(context):
    """
    Returns the material nodes for the active Blender object
    """
    m = getMaterial(context)
    return m.node_tree.nodes if m else None


class Material:
    """
    A parent class for all classes representing Blender materials
    """
    def __init__(self):
        pass