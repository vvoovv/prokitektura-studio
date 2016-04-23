import bpy
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
        o.name = "Frame"
        o.data.name = "Frame"
        o.location = (0., 0., 0.)
        o.show_wire = True
        o.show_all_edges = True
        o["id"] = 1
        parent = createEmptyObject("Window", (0., 0., 0.), True, empty_draw_type='PLAIN_AXES', empty_draw_size=0.05)
        o.parent = parent
        parent["counter"] = 1
        return {'FINISHED'}


class WorkshopAddPane(bpy.types.Operator):
    bl_idname = "prk.workshop_add_pane"
    bl_label = "Panes"
    bl_description = "Add new panes from the selected faces"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        # we work in the OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        t = Template(context.object, True)
        result = t.addPanes()
        if not result:
            self.report({'ERROR'}, "To add new panes select at least one face")
            return {'CANCELLED'}
        t.complete()
        return {'FINISHED'}


class WorkshopAssignJunction(bpy.types.Operator):
    bl_idname = "prk.workshop_assign_junction"
    bl_label = "Assign junction"
    bl_description = "Assign junction for the selected vertices"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def invoke(self, context, event):
        o = context.object
        # check if have a selected element
        selected = context.selected_objects
        j = None
        if len(selected) == 1:
            if o != selected[0]:
                j = selected[0]
        elif len(selected) > 1:
            j = selected[0] if o != selected[0] else selected[1]
        if not j:
            self.report({'ERROR'}, "To assign a junction for the vertex select the Blender object for the junction")
            return {'CANCELLED'}
        
        bpy.ops.object.mode_set(mode='OBJECT')
        Template(o).assignJunction(j).complete()
        return {'FINISHED'}


class WorkshopMakeWindow(bpy.types.Operator):
    bl_idname = "prk.workshop_make_window"
    bl_label = "Make a window"
    bl_description = "Make a window out of the template"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def invoke(self, context, event):
        self.makePanes(Template(context.object).getParent(), context)
        return {'FINISHED'}
    
    def makePanes(self, template, context):
        bpy.ops.object.select_all(action='DESELECT')
        Window(context, self).make(template)
        for t in template.getChildren():
            self.makePanes(t, context)