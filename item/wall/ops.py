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
    bl_label = "Extend the wall or start an attached wall"
    bl_description = "Extend the wall or start a wall attached to the selected wall segment"
    bl_options = {"REGISTER", "UNDO"}
    
    # states
    set_location = (1,)
    set_location_finished = (1,)
    set_length = (1,)
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
        
        if state is self.set_location:
            # capture X, Y, Z keys for attached walls
            if self.attached and event.type in {'X', 'Y', 'Z'}:
                return {'RUNNING_MODAL'}
            operator = getLastOperator(context)
            if operator != self.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
                # let cancel event happen, i.e. don't call op.mover.end() immediately
                self.state = self.set_location_finished if self.attached else self.finished
                self.lastOperator = operator
        elif state is self.set_location_finished:
            # this state is for attached walls only!
            mover.end()
            self.state = self.set_length
            # starting AlongLineMover
            mover = AlongSegmentMover(mover.wallAttached, mover.o2)
            self.mover = mover
            mover.start()
        elif state is self.set_length:
            # this state is for attached walls only!
            operator = getLastOperator(context)
            # The condition operator != self.lastOperator means,
            # that the modal operator started by mover.start() finished its work
            if operator != self.lastOperator or event.type in {'RIGHTMOUSE', 'ESC'}:
                # let cancel event happen, i.e. don't call mover.end() immediately
                self.state = self.finished
        elif state is self.finished:
            mover.end()
            return {'FINISHED'}
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        e = context.object
        locEnd = cursor_2d_to_location_3d(context, event)
        # try to get a wall instance assuming <e> is a corner EMPTY located at either free end of the wall
        wall = getWallFromEmpty(context, self, e, True)
        if wall:
            o = wall.extend(e, locEnd)
            bpy.ops.object.select_all(action="DESELECT")
            self.mover = AlongSegmentMover(wall, o)
            # set mode of operation
            self.attached = False
        else:
            # try to get a wall instance assuming <empty> is a segment EMPTY
            if "t" in e and e["t"]=="ws":
                wall = getWallFromEmpty(context, self, e, False)
                if wall:
                    # wall.startAttachedWall(empty, locEnd) returns segment EMPTY
                    o = wall.startAttachedWall(e, locEnd)
                    self.mover = AttachedSegmentMover(getWallFromEmpty(context, self, o), o, wall, e)
                    # set mode of operation
                    self.attached = True
            if not wall:
                self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either free end of the wall")
                return {'FINISHED'}
        self.state = self.set_location
        self.lastOperator = getLastOperator(context)
        # The order how self.mover.start() and context.window_manager.modal_handler_add(self)
        # are called is important. If they are called in the reversed order, it won't be possible to
        # capture X, Y, Z keys
        self.mover.start()
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
            self.report({"ERROR"}, "To extend the wall, select an EMPTY object at either free end of the wall")
            return {'FINISHED'}
        wall.extend(empty)
        return {'FINISHED'}


class WallComplete(bpy.types.Operator):
    bl_idname = "prk.wall_complete"
    bl_label = "Complete or attach the wall"
    bl_description = "Complete the wall or attach its free end to the selected wall segment"
    bl_options = {"REGISTER", "UNDO"}
    
    def completeAttachedWall(self, wall, o, targetWall, target):
        # get reference corner EMPTYs for the target wall
        e2 = targetWall.getCornerEmpty(target)
        e1 = targetWall.getPrevious(e2)
        # Check if the wall segment defined by <e1> and <e2> and
        # the wall segment defined by <o> and its previous EMPTY
        # are NOT perpedndicular, otherwise it won't be possible to attach <wall>
        # perpendicular to <targetWall>
        if abs( (e2.location-e1.location).dot(o.location-wall.getPrevious(o).location) ) < zero2:
            self.report({"ERROR"}, "Unable to attach the wall perpendicular to the target one!")
        else:
            wall.completeAttachedWall(o, targetWall, target)
    
    def execute(self, context):
        # check if we need to attach the wall to another wall
        selected = context.selected_objects
        if len(selected) == 2:
            o1 = selected[0]
            o2 = selected[1]
            wall1 = getWallFromEmpty(context, self, o1)
            wall2 = getWallFromEmpty(context, self, o2)
            left1 = o1["l"]
            left2 = o2["l"]
            if wall1 and wall2:
                if o1["t"]=="ws" and o2["t"]=="ws":
                    # The special case:
                    # create a wall segment connecting two wall segments defined by <o1> and <o2>
                    
                    return {"FINISHED"}
                startAttached1 = wall1.isAttached(wall1.getStart(left1))
                end1 = wall1.getEnd(left1)
                endAttached1 = wall1.isAttached(end1)
                startAttached2 = wall2.isAttached(wall2.getStart(left2))
                end2 = wall2.getEnd(left2)
                endAttached2 = wall2.isAttached(end2)
                finished = True
                if startAttached1 and not endAttached1 and o1==end1 and o2["t"]=="ws":
                    # wall1 is the wall to be attached and wall2 is the target one
                    self.completeAttachedWall(wall1, o1, wall2, o2)
                elif startAttached2 and not endAttached2 and o2==end2 and o1["t"]=="ws":
                    # wall2 is the wall to be attached and wall1 is the target one
                    self.completeAttachedWall(wall2, o2, wall1, o1)
                elif startAttached1 or startAttached2:
                    if o1["m"] != o2["m"]:
                        self.report({"ERROR"}, "To attach the wall select the free end of the wall and a target wall segment!")
                    else:
                        self.report({"ERROR"}, "Unable to attach the wall to itself!")
                else:
                    finished = False
                if finished:
                    return {'FINISHED'}
        
        # complete the wall defined be the active EMPTY
        o = context.scene.objects.active
        wall = getWallFromEmpty(context, self, o)
        if not wall:
            self.report({"ERROR"}, "To complete the wall, select an EMPTY object belonging to the wall")
        elif wall.isClosed():
            self.report({"ERROR"}, "The wall has been already completed!")
        elif wall.isAttached(wall.getStart()):
            self.report({"ERROR"}, "Unable to complete an attached wall!")
        else:
            wall.complete(o["l"])
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
