import bpy
from base import zeroVector
from util.blender import createEmptyObject
from .template import Template
from item.window import Window


class WorkshopStartWindow(bpy.types.Operator):
    bl_idname = "prk.workshop_start_window"
    bl_label = "Start a window"
    bl_description = "Start a window"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def invoke(self, context, event):
        o = context.object
        o.name = "T_Frame"
        o.data.name = "T_Frame"
        location = o.location.copy()
        o.location = zeroVector
        o.show_wire = True
        o.show_all_edges = True
        o["id"] = 1
        # reverse the surface <s1> by default
        o["s1"] = "reversed"
        parent = createEmptyObject("Window", location, True, empty_draw_type='PLAIN_AXES', empty_draw_size=0.05)
        o.parent = parent
        parent["pane_counter"] = 2
        parent["vert_counter"] = 1
        return {'FINISHED'}


class WorkshopAddPane(bpy.types.Operator):
    bl_idname = "prk.workshop_add_pane"
    bl_label = "Panes"
    bl_description = "Add new panes from the selected faces"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        # we work in the OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        t = Template(context.object)
        result = t.addPanes()
        if not result:
            self.report({'ERROR'}, "To add new panes select at least one face")
            return {'CANCELLED'}
        t.complete()
        return {'FINISHED'}


class WorkshopAssignNode(bpy.types.Operator):
    bl_idname = "prk.workshop_assign_node"
    bl_label = "Assign node"
    bl_description = "Assign node for the selected vertices"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def invoke(self, context, event):
        o = context.object
        # check if we have a selected element
        selected = context.selected_objects
        n = None
        if len(selected) == 1:
            if o != selected[0]:
                n = selected[0]
        elif len(selected) > 1:
            n = selected[0] if o != selected[0] else selected[1]
        if not n:
            self.report({'ERROR'}, "To assign a node for the vertex select the Blender object for the node")
            return {'CANCELLED'}
        
        bpy.ops.object.mode_set(mode='OBJECT')
        Template(o, skipInit=True).assignNode(n).complete()
        return {'FINISHED'}


class WorkshopMakeWindow(bpy.types.Operator):
    bl_idname = "prk.workshop_make_window"
    bl_label = "Make a window"
    bl_description = "Make a window out of the template"
    bl_options = {"REGISTER", "UNDO"}
    
    addEdgeSplitModifier = bpy.props.BoolProperty(
        name = "Add Edge Split modifier",
        description = "Add Edge Split modifier to the Blender object of the window",
        default = True
    )
    
    dissolveEndEdges = bpy.props.BoolProperty(
        name = "Dissolve end edges",
        description = "Dissolve edges that define the ends of each node used to make the window",
        default = True
    )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        self.makePanes(Template(context.object).getTopParent(), context)
        return {'FINISHED'}
    
    def makePanes(self, template, context):
        bpy.ops.object.select_all(action='DESELECT')
        Window(context, self).make(
            template,
            addEdgeSplitModifier = self.addEdgeSplitModifier,
            dissolveEndEdges = self.dissolveEndEdges
        )
        for t in template.getChildren():
            self.makePanes(t, context)


class WorkshopSetChildOffset(bpy.types.Operator):
    bl_idname = "prk.workshop_set_child_offset"
    bl_label = "Set offset for a child item"
    bl_description = "Set offset for a child item"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def invoke(self, context, event):
        o = context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        childOffset = createEmptyObject(
            "offset_" + o.name,
            context.scene.cursor_location - o.location,
            False,
            empty_draw_type='PLAIN_AXES',
            empty_draw_size=0.01
        )
        childOffset["t"] = "offset"
        childOffset.parent = o
        
        # make <childOffset> the active object
        o.select = False
        childOffset.select = True
        context.scene.objects.active = childOffset
        return {'FINISHED'}