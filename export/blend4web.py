import bpy
from util.blender import modifier_apply_all


class ExportB4wHtml(bpy.types.Operator):
    bl_idname = "export_scene.prk_b4w_html"
    bl_label = "Export the scene for Blend4Web (.html)"
    bl_description = "Export the scene for Blend4Web (.html)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        
        def processHierarchy(o, dupliObjects, dupliObject):
            if o.hide and o.type=="MESH":
                o.b4w_do_not_export = True
            # dupliObject is the top dupli object in the current hierarchy
            # dupliObject doesn't have any dupli object as an ancestor
            if not dupliObject and o.dupli_type != "NONE" and not "container" in o:
                dupliObject = o
                dupliObjects.append(o)
            # if there is a dupli object in the current hierarchy, apply all modifiers to the object <o>
            if dupliObject and o.modifiers:
                modifier_apply_all(o)
                if o.b4w_apply_modifiers:
                    o.b4w_apply_modifiers = False
            for _o in o.children:
                processHierarchy(_o, dupliObjects, dupliObject)
        
        def invert_selection(_o):
            for o in _o.children:
                if not o.select and o.hide_select:
                    o.hide_select = False
                o.select = not o.select
                invert_selection(o)
        
        def shared_mesh_and_vertex_groups(_o):
            # Treat the case if a MESH object has shared MESH data and vertex groups
            # Blend4Web fails to perform export in that case
            for o in _o.children:
                if o.type == "MESH" and o.data.users > 1 and o.vertex_groups:
                    # delete vertex groups
                    o.vertex_groups.clear()
                shared_mesh_and_vertex_groups(o)
        
        bpy.ops.object.select_all(action="DESELECT")
        
        dupliObjects = []
        # prepare the active scene for export
        for o in context.scene.objects:
            # find top level parent objects
            if not o.parent and o.children:
                processHierarchy(o, dupliObjects, None)
            o.select = False
            if o.modifiers:
                o.b4w_apply_modifiers = True
        
        for o in dupliObjects:
            # make duplicates real for the whole hierarchy
            o.hide_select = False
            o.select = True
            bpy.ops.object.duplicates_make_real(use_base_parent=True)
            # delete original children of _obj to avoid duplication of objects
            o.select = False
            invert_selection(o)
            bpy.ops.object.delete()
            
            shared_mesh_and_vertex_groups(o)
        
        bpy.ops.export_scene.b4w_html("INVOKE_DEFAULT", do_autosave=False)
        return {'FINISHED'}