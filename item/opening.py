from base.item import Item
from base.mover_along_wall import AlongWallMover
from base.mover_size import SizeMover
from blender_util import addBooleanModifier, getLastOperator
from item.wall import addTransformsVariable, addLocDiffVariable, addSinglePropVariable


class Opening(Item):
    
    allowZ = False
    
    def init(self, obj):
        if obj["t"] == self.type:
            self.obj = obj
            # obj.animation_data.drivers[0] is for rotation, ther order of <o1> and <o2> depends on <left>,
            # that's why we use obj.animation_data.drivers[1]
            variables = obj.animation_data.drivers[1].driver.variables
            self.o1 = variables[0].targets[0].id
            self.o2 = variables[1].targets[0].id
            self.lookup()
    
    def create(self, obj, wall, o1, o2):
        self.obj = obj
        self.o1 = o1
        self.o2 = o2
        self.lookup()
        
        left = o1["l"]
        # set the initial locaton of the object at the middle of the wall segment
        sign = 1. if left else -1.
        obj.location = (o1.location + o2.location + sign*self.width.location.x*(o2.location-o1.location).normalized())/2.
        obj.location.z = self.floorToWindow
        
        # set drivers for EMPTYs controlling interior and exterior parts of the window
        # the interior part
        i = self.int.driver_add("location", 1)
        addSinglePropVariable(i, "w", o2, "[\"w\"]")
        i.driver.expression = "-w/2."
        # the exterior part
        e = self.ext.driver_add("location", 1)
        addSinglePropVariable(e, "w", o2, "[\"w\"]")
        e.driver.expression = "w/2."
        
        addBooleanModifier(wall.mesh, o2["g"], self.envelope)
        
        rz = obj.driver_add("rotation_euler", 2)
        addTransformsVariable(rz, "x1", o2 if left else o1, "LOC_X")
        addTransformsVariable(rz, "x2", o1 if left else o2, "LOC_X")
        addTransformsVariable(rz, "y1", o2 if left else o1, "LOC_Y")
        addTransformsVariable(rz, "y2", o1 if left else o2, "LOC_Y")
        rz.driver.expression = "atan2(y2-y1,x2-x1)"
        
        self.keepRatioCenter()
    
    def lookup(self):
        lookups = {
            'env': 'envelope',
            'width': 'width',
            'int': 'int',
            'ext': 'ext'
        }
        for o in self.obj.children:
            if "t" in o and o["t"] in lookups:
                setattr(self, lookups[o["t"]], o)
                del lookups[o["t"]]
                if not len(lookups):
                    # everything is found
                    break
    
    def keepRatioCenter(self):
        o1 = self.o1
        o2 = self.o2
        left = o1["l"]
        # calculate the ratio
        l = self.o2.location - self.o1.location
        k = (self.obj.location - self.o1.location).dot(l)
        l = l.length
        k = k/l
        # half width of the item
        w = self.width.location.x/2.
        k = ( (k-w) if left else (k+w) ) / l
        sign1 = "+" if left else "-"
        sign2 = "-" if left else "+"
        
        x = self.obj.driver_add("location", 0)
        addTransformsVariable(x, "x1", o1, "LOC_X")
        addTransformsVariable(x, "x2", o2, "LOC_X")
        addTransformsVariable(x, "y1", o1, "LOC_Y")
        addTransformsVariable(x, "y2", o2, "LOC_Y")
        addLocDiffVariable(x, "d", o1, o2)
        # the width of the window
        addTransformsVariable(x, "wi", self.width, "LOC_X")
        # the width of the wall
        addSinglePropVariable(x, "wa", o2, "[\"w\"]")
        x.driver.expression = "x1+(x2-x1)*("+str(k)+sign1+"wi/2/d)"+sign1+"(y2-y1)*wa/2/d"
        
        y = self.obj.driver_add("location", 1)
        addTransformsVariable(y, "y1", o1, "LOC_Y")
        addTransformsVariable(y, "y2", o2, "LOC_Y")
        addTransformsVariable(y, "x1", o1, "LOC_X")
        addTransformsVariable(y, "x2", o2, "LOC_X")
        addLocDiffVariable(y, "d", o1, o2)
        # the width of the window
        addTransformsVariable(y, "wi", self.width, "LOC_X")
        # the width of the wall
        addSinglePropVariable(y, "wa", o2, "[\"w\"]")
        y.driver.expression = "y1+(y2-y1)*("+str(k)+sign1+"wi/2/d)"+sign2+"(x2-x1)*wa/2/d"
    
    def move_invoke(self, op, context, event, o):
        op.allowZ = False
        if o["t"] == self.type:
            mover = AlongWallMover(self)
            op.allowZ = self.allowZ
        elif o["t"] == "width":
            mover = SizeMover(self, o)
        elif o["t"] == "height":
            mover = SizeMover(self, o)
        # keep the following variables in the operator <o>
        op.state = None
        op.lastOperator = getLastOperator(context)
        op.mover = mover
        op.finished = False
        # The order how self.mover.start() and context.window_manager.modal_handler_add(self)
        # are called is important. If they are called in the reversed order, it won't be possible to
        # capture X, Y, Z keys
        mover.start()
        context.window_manager.modal_handler_add(op)
        return {'RUNNING_MODAL'}
    
    def move_modal(self, op, context, event, o):
        operator = getLastOperator(context)
        if op.allowZ and event.type == "Z":
            op.allowZ = False
            return {'PASS_THROUGH'}
        elif event.type in {'X', 'Y', 'Z'}:
            # capture X, Y, Z keys
            return {'RUNNING_MODAL'}
        if op.finished:
            op.mover.end()
            return {'FINISHED'}
        if operator != op.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
            # let cancel event happen, i.e. don't call op.mover.end() immediately
            op.finished = True
        return {'PASS_THROUGH'}