

def projectOntoPlane(v, n):
    """
    Project vector <v> onto the plane defined by the normal <n> to the plane.
    """
    return v - v.dot(n)*n


def projectOntoLine(v, e):
    """
    Project vector <v> onto the line defined by the unit vector <l>.
    """
    return v.dot(e) * e


def isVectorBetweenVectors(vec, vec1, vec2):
    """
    Checks if the vector <vec> lies between vectors <vec1> and <vec2>,
    provided all three vectors share the same origin
    """
    cross1 = vec.cross(vec1)
    cross2 = vec.cross(vec2)
    # cross1 and cross2 must point in the opposite directions
    # at least one angle must be less than 90 degrees
    return cross1.dot(cross2) < 0. and (vec.dot(vec1)>0. or vec.dot(vec2)>0.)
