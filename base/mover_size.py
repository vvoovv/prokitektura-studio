import bpy

class SizeMover:
    """
    A mover to set the size (width or height) of the item
    """ 
    def __init__(self, item, o):
        pass
    
    def start(self):
        bpy.ops.transform.translate('INVOKE_DEFAULT')
    
    def end(self):
        pass