import bpy
from base import zeroVector, pContext
from util.blender import createEmptyObject
from .template import Template


class WorkshopStartTemplate(bpy.types.Operator):
    bl_idname = "prk.workshop_start_template"
    bl_label = "Start a template"
    bl_description = "Initialize a template"
    bl_options = {"REGISTER", "UNDO"}
    
    objectNameBase = bpy.props.StringProperty(
        description = "A base for the name of the Blender object"
    )
    
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
        parent = createEmptyObject(self.objectNameBase, location, True, empty_draw_type='PLAIN_AXES', empty_draw_size=0.05)
        o.parent = parent
        parent["part_counter"] = 2
        parent["vert_counter"] = 1
        return {'FINISHED'}


class WorkshopAddPart(bpy.types.Operator):
    bl_idname = "prk.workshop_add_part"
    bl_label = "Parts"
    bl_description = "Add new parts from the selected faces"
    bl_options = {"REGISTER", "UNDO"}
    
    def invoke(self, context, event):
        # we work in the OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        t = Template(context.object)
        result = t.addParts()
        if not result:
            self.report({'ERROR'}, "To add new parts select at least one face")
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


class WorkshopMakeItem(bpy.types.Operator):
    bl_idname = "prk.workshop_make_item"
    bl_label = "Make an item"
    bl_description = "Make an item out of the template"
    bl_options = {"REGISTER", "UNDO"}
    
    addEdgeSplitModifier = bpy.props.BoolProperty(
        name = "Add Edge Split modifier",
        description = "Add Edge Split modifier to the Blender object of the item",
        default = True
    )
    
    dissolveEndEdges = bpy.props.BoolProperty(
        name = "Dissolve end edges",
        description = "Dissolve edges that define the ends of each node used to make the item",
        default = True
    )
    
    hooksForNodes = bpy.props.BoolProperty(
        name = "Add HOOK modifier for nodes",
        description = "Add a HOOK modifier for the vertices of each Blender object used as a node",
        default = True
    )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        if not context.scene.prk.workshopType in pContext.items:
            return {'FINISHED'}
        self.makeParts(Template(context.object).getTopParent(), context)
        return {'FINISHED'}
    
    def makeParts(self, template, context):
        bpy.ops.object.select_all(action='DESELECT')
        # a class for the item in question
        Item = pContext.items[context.scene.prk.workshopType][0]
        Item(context, self).make(
            template,
            addEdgeSplitModifier = self.addEdgeSplitModifier,
            dissolveEndEdges = self.dissolveEndEdges,
            hooksForNodes = self.hooksForNodes
        )
        for t in template.getChildren():
            self.makeParts(t, context)
        template.bm.free()


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