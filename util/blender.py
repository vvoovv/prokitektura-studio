import bpy, bmesh


def makeActiveSelected(context, o):
    o.select = True
    context.scene.objects.active = o
    

def showWired(o, wired=True):
    if o.type == 'MESH':
        o.draw_type = 'WIRE' if wired else bpy.ops.wm.call_menu(name="CONSOLE_MT_console")
    for o in o.children:
        showWired(o, wired)


def appendFromFile(context, filepath):
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.objects = data_from.objects
    # append all objects and find their parent
    parent = None
    for obj in data_to.objects:
        if not parent and not obj.parent:
            parent = obj
        bpy.context.scene.objects.link(obj)
    # perform cleanup
    bpy.ops.object.select_all(action="DESELECT")
    # return the parent object
    return parent


def setMaterial(obj, material):
    materials = obj.data.materials
    if materials:
        materials[0] = material
    else:
        materials.append(material)


def getMaterial(context):
    """
    Returns the material for the active Blender object
    """
    o = context.scene.objects.active
    return o.data.materials[0] if o.data.materials else None

 
def loadMaterialFromFile(filepath, name):
    """
    Loads a material with the given <name> from the .blend with the given <filepath>
    """
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.materials = [name]
    return data_to.materials[0]


def setCustomAttributes(obj, **kwargs):
    for key in kwargs:
        obj[key] = kwargs[key]


def createMeshObject(name, location=(0., 0., 0.), mesh=None):
    if not mesh:
        mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.scene.objects.link(obj)
    return obj


def createOneVertObject(name, location=(0., 0., 0.)):
    obj = createMeshObject(name, location)
    mesh = obj.data
    mesh.from_pydata([(0., 0., 0.)], [], [])
    mesh.update()
    return obj


def createEmptyObject(name, location, hide=False, **kwargs):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.hide = hide
    obj.hide_select = hide
    obj.hide_render = True
    if kwargs:
        for key in kwargs:
            setattr(obj, key, kwargs[key])
    bpy.context.scene.objects.link(obj)
    return obj


def getBmesh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    return bm


def setBmesh(obj, bm):
    bm.to_mesh(obj.data)
    bm.free()


def addHookModifier(obj, name, hookObj, vertexGroup):
    m = obj.modifiers.new(name=name, type='HOOK')
    m.vertex_group = vertexGroup
    m.object = hookObj
    # starting from 2.76 we have to execute the following lines to get the correct offset of vertices
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.object.hook_reset(modifier=name)
    bpy.ops.object.mode_set(mode="OBJECT")
    return m


def addBooleanModifier(obj, name, operand, operation="DIFFERENCE"):
    m = obj.modifiers.new(name=name, type='BOOLEAN')
    m.operation = operation
    m.object = operand
    return m


def addModifier(modifierType, obj, name, **kwargs):
    m = obj.modifiers.new(name=name, type=modifierType)
    for k in kwargs:
        setattr(m, k, kwargs[k])


def addSolidifyModifier(obj, name, **kwargs):
    addModifier('SOLIDIFY', obj, name, **kwargs)
        

def addEdgeSplitModifier(obj, name, **kwargs):
    addModifier('EDGE_SPLIT', obj, name, **kwargs)
    

def createPolyCurve(name, location, points):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '2D'
    
    spline = curve.splines.new('POLY')
    numPoints = len(points)
    spline.points.add(numPoints-1)
    for i in range(numPoints):
        p = points[i] - location
        spline.points[i].co = (p[0], p[1], p[2], 1)
    
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    bpy.context.scene.objects.link(obj)
    return obj


def assignGroupToVerts(obj, layer, groupName, *verts):
    """
    Creates a new vertex group with the name groupName if it doesn't exist
    and assigns verts from the <verts> tuple to the group
    """
    groups = obj.vertex_groups
    
    groupIndex = groups[groupName].index if groupName in groups else groups.new(groupName).index
    for v in verts:
        v[layer][groupIndex] = 1.0
    return groupIndex


def getVertsForVertexGroup(obj, bm, group):
    verts = []
    # All vertex groups are in the deform layer.
    # There can be only one deform layer
    layer = bm.verts.layers.deform[0]
    for v in bm.verts:
        if obj.vertex_groups[group].index in v[layer]:
            verts.append(v)
    return verts


def setVertexGroupName(o, groupIndex, name):
    o.vertex_groups[groupIndex].name = name


def parent_set(parent, *objects):
    for obj in objects:
        obj.parent = parent


def cursor_2d_to_location_3d(context, event):
    from bpy_extras.view3d_utils import region_2d_to_vector_3d, region_2d_to_location_3d
    
    coords = event.mouse_region_x, event.mouse_region_y
    region = context.region
    rv3d = context.space_data.region_3d
    return region_2d_to_location_3d(region, rv3d, coords, region_2d_to_vector_3d(region, rv3d, coords))


def hide_select(o, value):
    o.hide = value
    o.hide_select = value


def modifier_apply(o, modifierName):
    bpy.context.scene.objects.active = o
    bpy.ops.object.modifier_apply(modifier=modifierName)


def modifier_apply_all(o):
    bpy.context.scene.objects.active = o
    if o.data.users > 1:
        o.hide_select = False
        o.select = True
        bpy.ops.object.make_single_user(obdata=True)
        o.select = False
    for m in o.modifiers:
        #try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        #except RuntimeError:
        #    pass


def getLastOperator(context=None):
    """
    Returns the last operator from context.window_manager.operators or None if no operator is available
    """
    if not context:
        context = bpy.context
    wm = context.window_manager
    return wm.operators[-1] if len(wm.operators) else None


################################################
# Utility functions to set variables for drivers
################################################
def addTransformsVariable(driver, name, id0, transform_type):
    v = driver.driver.variables.new()
    v.name = name
    v.type = "TRANSFORMS"
    v.targets[0].id = id0
    v.targets[0].transform_type = transform_type
    v.targets[0].transform_space = "LOCAL_SPACE"


def addSinglePropVariable(driver, name, id0, data_path):
    v = driver.driver.variables.new()
    v.name = name
    v.type = "SINGLE_PROP"
    v.targets[0].id = id0
    v.targets[0].data_path = data_path


def addLocDiffVariable(driver, name, id0, id1):
        v = driver.driver.variables.new()
        v.name = name
        v.type = "LOC_DIFF"
        v.targets[0].id = id0
        v.targets[0].transform_space = "LOCAL_SPACE"
        v.targets[1].id = id1
        v.targets[1].transform_space = "LOCAL_SPACE"


#############
# BMesh stuff
#############
def getOuterEdges(v):
    """
    Get outer <BMEdge>s for the <BMVert> <v>
    
    Returns:
        A tuple of outer <BMEdge>
    """
    _e, e = None, None
    for e in v.link_edges:
        if len(e.link_faces) == 1:
            if _e:
                # the second edge is simply <e>
                break
            else:
                # the first edge is found
                _e = e
    return _e, e