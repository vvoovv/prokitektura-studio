import bpy

from blender_util import cursor_2d_to_location_3d, getLastOperator
from . import Wall, getWallFromEmpty
from base import zero2
from base.mover_segment import AttachedSegmentMover
from base.mover_along_line import AlongSegmentMover


class WallEditAdd(bpy.types.Operator):
    bl_idname = "prk.wall_edit_add"
    bl_label = "Add a new wall"
    bl_description = "Adds a new wall"
    bl_options = {"REGISTER", "UNDO"}
    
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    
    def invoke(self, context, event):
        locEnd = cursor_2d_to_location_3d(context, event)
        wall = Wall(context, self)
        constraint_axis = wall.create(locEnd)
        bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=constraint_axis, constraint_orientation='LOCAL')
        return {'FINISHED'}
    

class WallEditExtend(bpy.types.Operator):
    bl_idname = "prk.wall_edit_extend"
    bl_label = "Extend the wall"
    bl_description = "Extends the wall"
    bl_options = {"REGISTER", "UNDO"}
    
    # states
    set_location = (1,)
    finished = (1,)
    
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    
    def modal(self, context, event):
        state = self.state
        mover = self.mover
        if state is None:
            self.state = self.set_location
            mover.start()
        elif state is self.set_location:
            operator = getLastOperator(context)
            if operator != self.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
                # let cancel event happen, i.e. don't call op.mover.end() immediately
                self.state = self.finished
        elif state is self.finished:
            mover.end()
            return {'FINISHED'}
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        empty = context.object
        locEnd = cursor_2d_to_location_3d(context, event)
        wall = getWallFromEmpty(context, self, empty, True)
        if not wall:
            self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either open end of the wall")
            return {'FINISHED'}
        o = wall.extend(empty, locEnd)
        bpy.ops.object.select_all(action="DESELECT")
        self.mover = AlongSegmentMover(wall, o)
        self.state = None
        self.lastOperator = getLastOperator(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class WallAdd(bpy.types.Operator):
    bl_idname = "prk.wall_add"
    bl_label = "Add a new wall"
    bl_description = "Adds a new wall"
    bl_options = {"REGISTER", "UNDO"}
    
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    
    def execute(self, context):
        Wall(context, self).create()
        return {'FINISHED'}


class WallExtend(bpy.types.Operator):
    bl_idname = "prk.wall_extend"
    bl_label = "Extend the wall"
    bl_description = "Extends the wall"
    bl_options = {"REGISTER", "UNDO"}
    
    length = bpy.props.FloatProperty(
        name = "Length",
        description = "The length of the wall segment",
        default = 2,
        min = 0.1,
        max = 100,
        unit = "LENGTH"
    )
    
    def execute(self, context):
        empty = context.scene.objects.active
        wall = getWallFromEmpty(context, self, empty, True)
        if not wall:
            self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either open end of the wall")
            return {'FINISHED'}
        wall.extend(empty)
        return {'FINISHED'}


class WallComplete(bpy.types.Operator):
    bl_idname = "prk.wall_complete"
    bl_label = "Complete or attach the wall"
    bl_description = "Complete the wall or attach its free end to the selected wall segment"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        o = context.scene.objects.active
        wall = getWallFromEmpty(context, self, o)
        if not wall:
            self.report({"ERROR"}, "To complete the wall, select an EMPTY object belonging to the wall")
            return {'FINISHED'}
        if wall.isClosed():
            self.report({"ERROR"}, "The wall has been already completed!")
            return {'FINISHED'}
        
        left = o["l"]
        
        start = wall.getStart(left)
        if wall.isAttached(start):
            end = wall.getEnd(left)
            if wall.isAttached(end):
                self.report({"ERROR"}, "The wall has been already attached!")
                return {'FINISHED'}
            
            selected = context.selected_objects
            hasError = True
            if o == end and len(selected) == 2:
                target = selected[0] if selected[1] == o else selected[1]
                if target["t"] == "ws" and o["m"] != target["m"]:
                    hasError = False
                    targetWall = getWallFromEmpty(context, self, target)
                    # get reference corner EMPTYs for the targer wall
                    e2 = targetWall.getCornerEmpty(target)
                    e1 = targetWall.getPrevious(e2)
                    # Check if the wall segment defined by <e1> and <e2> and
                    # the wall segment defined by <o> and its previous EMPTY
                    # are NOT perpedndicular, otherwise it won't be possible to attach <wall>
                    # perpendicular to <targetWall>
                    if abs( (e2.location-e1.location).dot(o.location-wall.getPrevious(o).location) ) < zero2:
                        self.report({"ERROR"}, "Unable to attach the wall perpendicular to the target one!")
                        return {'FINISHED'}
                    
                    wall.completeAttachedWall(o, targetWall, target)
                    
            if hasError:
                self.report({"ERROR"}, "To attach the wall select a target wall segment first and then the free end of the wall!")
                return {'FINISHED'}
        else:
            wall.complete(left)
        return {'FINISHED'}


class WallFlipControls(bpy.types.Operator):
    bl_idname = "prk.wall_flip_controls"
    bl_label = "Flip control points for the wall"
    bl_description = "Flips control points for the wall"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):
        empty = context.scene.objects.active
        wall = getWallFromEmpty(context, self, empty)
        if not wall:
            self.report({"ERROR"}, "To flip control points for the wall, select an EMPTY object belonging to the wall")
        wall.flipControls(empty)
        return {'FINISHED'}


class WallAttachedStart(bpy.types.Operator):
    bl_idname = "prk.wall_attached_start"
    bl_label = "Start an attached wall"
    bl_description = "Start a wall attached to the selected wall segment"
    bl_options = {"REGISTER", "UNDO"}
    
    # states
    set_location = (1,)
    set_location_finished = (1,)
    set_length = (1,)
    finished = (1,)
    
    def modal(self, context, event):
        state = self.state
        mover = self.mover
        if state is self.set_location:
            # capture X, Y, Z keys
            if event.type in {'X', 'Y', 'Z'}:
                return {'RUNNING_MODAL'}
            operator = getLastOperator(context)
            # The condition operator != self.lastOperator means,
            # that the modal operator started by mover.start() finished its work
            if operator != self.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
                # let cancel event happen, i.e. don't call mover.end() immediately
                self.state = self.set_location_finished
                self.lastOperator = operator
        elif state is self.set_location_finished:
            mover.end()
            self.state = self.set_length
            # starting AlongLineMover
            mover = AlongSegmentMover(mover.wallAttached, mover.o2)
            self.mover = mover
            mover.start()
        elif state is self.set_length:
            operator = getLastOperator(context)
            if operator != self.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
                # let cancel event happen, i.e. don't call mover.end() immediately
                self.state = self.finished
        elif state is self.finished:
            mover.end()
            return {'FINISHED'}
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        e = context.scene.objects.active
        wall = getWallFromEmpty(context, self, e)
        if not wall:
            self.report({"ERROR"}, "Select two consequent EMPTY objects belonging to the wall")
        wall.resetHookModifiers()
        locEnd = cursor_2d_to_location_3d(context, event)
        # treat the case if <e> is at the starting open end of the wall
        e = wall.getNext(e) if "e" in e and not e["e"] else wall.getCornerEmpty(e)
        # wall.startAttachedWall(empty, locEnd) returns segment EMPTY
        o = wall.startAttachedWall(e, locEnd)
        self.mover = AttachedSegmentMover(getWallFromEmpty(context, self, o), o, wall, e)
        self.state = self.set_location
        self.lastOperator = getLastOperator(context)
        # The order how self.mover.start() and context.window_manager.modal_handler_add(self)
        # are called is important. If they are called in the reversed order, it won't be possible to
        # capture X, Y, Z keys
        self.mover.start()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}