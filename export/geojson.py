import math, json
import bpy, mathutils

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty


class TransverseMercator:
    radius = 6378137

    def __init__(self, **kwargs):
        # setting default values
        self.lat = 0 # in degrees
        self.lon = 0 # in degrees
        self.k = 1 # scale factor
        
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
        self.latInRadians = math.radians(self.lat)

    def fromGeographic(self, lat, lon):
        lat = math.radians(lat)
        lon = math.radians(lon-self.lon)
        B = math.sin(lon) * math.cos(lat)
        x = 0.5 * self.k * self.radius * math.log((1+B)/(1-B))
        y = self.k * self.radius * ( math.atan(math.tan(lat)/math.cos(lon)) - self.latInRadians )
        return (x,y)

    def toGeographic(self, x, y):
        x = x/(self.k * self.radius)
        y = y/(self.k * self.radius)
        D = y + self.latInRadians
        lon = math.atan(math.sinh(x)/math.cos(D))
        lat = math.asin(math.sin(D)/math.cosh(x))

        lon = self.lon + math.degrees(lon)
        lat = math.degrees(lat)
        return (lat, lon)


class GeoJson(bpy.types.Operator, ExportHelper):
    bl_idname = "prk.export_geojson"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export GeoJSON"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob = StringProperty(default="*.json", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting = BoolProperty(
            name="Example Boolean",
            description="Example Tooltip",
            default=True,
            )

    type = EnumProperty(
            name="Example Enum",
            description="Choose between two items",
            items=(('OPT_A', "First Option", "Description one"),
                   ('OPT_B', "Second Option", "Description two")),
            default='OPT_A',
            )

    def execute(self, context):
        features = []
        data = {
            "type": "FeatureCollection",
            "features": features
        }
        rotationMatrix = mathutils.Matrix.Rotation(math.radians(context.scene["heading"]), 4, "Z")
        projection = TransverseMercator(lat=context.scene["latitude"], lon=context.scene["longitude"])
        # iterate over all floors
        for o in context.scene.objects:
            if not ("t" in o and o["t"] == "floor"):
                continue
            coords = []
            # iterate through EMPTYs that control the vertices of polygon of the floor
            for m in o.modifiers:
                e = m.object
                p = rotationMatrix * e.parent.matrix_world * e.location
                p = projection.toGeographic(p.x, p.y)
                coords.append( (p[1], p[0]) )
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": (coords,)
                },
                "properties": {
                    "name": o.name
                }
            })
        f = open(self.filepath, 'w', encoding="utf-8")
        f.write(json.dumps(data))
        f.close()
    
        return {'FINISHED'}
