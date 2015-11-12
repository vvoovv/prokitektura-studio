import bpy

class Mover:
    
    def __init__(self, item):
        self.item = item
        item.obj.driver_remove("location")
    
    def start(self):
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(True, False, False), constraint_orientation='LOCAL')
    
    def end(self):
        self.item.keepRatioCenter()