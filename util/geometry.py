

def projectOntoPlane(v, n):
    """
    Project vector <v> onto the plane defined by the normal <n> to the plane.
    """
    return v - v.dot(n)*n
