import bpy
from base import zeroVector, zero2, pContext
from util.blender import createEmptyObject, makeActiveSelected, appendFromFile, parent_set, showWired,\
    getBmesh
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
    
    def execute(self, context):
        o = context.object
        o["t"] = Template.type
        o.name = "T_Frame"
        o.data.name = "T_Frame"
        location = o.location.copy()
        o.location = zeroVector
        o.show_wire = True
        o.show_all_edges = True
        o["id"] = 1
        # reverse the surface <s1> by default
        o["s1"] = "reversed"
        parent = createEmptyObject(self.objectNameBase, location, False, empty_draw_type='PLAIN_AXES', empty_draw_size=0.05)
        parent["t"] = context.scene.prk.workshopType
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
        return context.mode == 'OBJECT' and context.object and "t" in context.object
    
    def execute(self, context):
        if not context.scene.prk.workshopType in pContext.items:
            return {'FINISHED'}
        parent = context.object
        # reset the cache of nodes
        Template.nodeCache.reset()
        # getting the parent template (i.e. it doesn't contain the custom attribute <p>)
        for o in parent.children:
            if not "p" in o:
                self.makeParts(Template(o), context)
                makeActiveSelected(context, parent)
                break
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
        makeActiveSelected(context, childOffset)
        return {'FINISHED'}


class WorkshopSetAssetPlaceholder(bpy.types.Operator):
    bl_idname = "prk.workshop_set_asset_placeholder"
    bl_label = "Set asset placeholder"
    bl_description = "Set Blender EMPTY object as a placeholder fot the asset"
    bl_options = {"REGISTER", "UNDO"}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    
    def invoke(self, context, event):
        o = context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        assetType = context.scene.prk.item.window.assetType
        # Blender EMPTY  object as a placeholder for the offset
        a = createEmptyObject(
            o.name + "_" + assetType,
            context.scene.cursor_location - o.location,
            False,
            empty_draw_type='PLAIN_AXES',
            empty_draw_size=0.01
        )
        a["t"] = "asset"
        a["t2"] = assetType
        a.parent = o
        props = context.scene.prk.item
        # side (internal or external) for the asset
        if props.assetSideIe != 'n':
            # <sie> stands for <side internal or external>
            a["sie"] = props.assetSideIe
        
        # check if there is a selected vertex and if it defines the node's open end
        index = 0
        for v in o.data.vertices:
            if v.select:
                # iterate through vertex groups of the vertex <v>
                for g in v.groups:
                    name = o.vertex_groups[g.group].name
                    if name[:2] == "e_":
                        index = int(name[2:])
                        break
                if index:
                    break
        if index:
            # remember the index of the node's open end
            a["e"] = index
            
        
        # make <a> the active object
        o.select = False
        makeActiveSelected(context, a)
        return {'FINISHED'}


class WorkshopAssignAsset(bpy.types.Operator):
    bl_idname = "prk.workshop_assign_asset"
    bl_label = "Assign asset..."
    bl_description = "Assign asset to the template"
    bl_options = {"REGISTER", "UNDO"}
    
    filepath = bpy.props.StringProperty(
        subtype="FILE_PATH"
    )
    
    directory = bpy.props.StringProperty(
        subtype="DIR_PATH"
    )
    
    relativePosition = bpy.props.FloatProperty(
        name = "Relative position",
        description = "Relative position of the asset on the template edge",
        subtype = 'PERCENTAGE',
        min = 0.,
        max = 100.,
        default = 50.
    )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and context.object.get("t") == Template.type
    
    def invoke(self, context, event):
        # template Blender object
        o = context.object
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # check if exactly one edge is selected
        bm = getBmesh(o)
        edge = [edge for edge in bm.edges if edge.select]
        if len(edge) != 1:
            bpy.ops.object.mode_set(mode='EDIT')
            self.report({'ERROR'}, "To assign an asset select exactly 2 vertices on the same edge")
            return {'CANCELLED'}
        bm.free()
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # template Blender object
        o = context.object
        t = Template(o, skipInit = True)
        props = context.scene.prk.item
        
        # find the selected vertices
        bm = t.bm
        v = [v for v in bm.verts if v.select]
        verts = (v[0].co, v[1].co)
        # check if <verts> have the same <z>-coordinate (i.e. <verts> are located horizontally)
        if abs(verts[1].z - verts[0].z) < zero2:
            # verts[0] must be the leftmost vertex
            if verts[0].x > verts[1].x:
                verts = (verts[1], verts[0])
                v = (v[1], v[0])
        else:
            # verts[0] must be the lower vertex
            if verts[0].z > verts[1].z:
                verts = (verts[1], verts[0])
                v = (v[1], v[0])
        
        # <a> is for asset
        a = appendFromFile(context, self.filepath)
        a.location = verts[0] + self.relativePosition*(verts[1]-verts[0])/100.
        parent_set(o, a)
        a["t"] = "asset"
        a["t2"] = props.window.assetType
        # store <vids> for the tuple <v> of BMesh vertices as custom Blender object attributes
        a["vid1"] = t.getVid(v[0])
        a["vid2"] = t.getVid(v[1])
        t.bm.free()
        # side (left or right) for the asset
        if props.assetSideLr != 'n':
            # <slr> stands for <side left or right>
            a["slr"] = props.assetSideLr
        showWired(a)
        
        makeActiveSelected(context, a)
        # Without bpy.ops.transform.translate() some complex stuff (some modifiers)
        # may not be initialized correctly
        bpy.ops.transform.translate()
        return {'FINISHED'}