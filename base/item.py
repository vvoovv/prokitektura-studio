

class Item:
    
    def __init__(self, context, op):
        self.context = context
        self.op = op
    
    def init(self, o):
        return

    def move_invoke(self, op, context, event, o):
        return {'FINISHED'}
    
    def move_modal(self, op, context, event, o):
        return {'FINISHED'}