from OCP.BRepAdaptor import BRepAdaptor_Surface
from build123d import *

def classify_surface_occ(face) -> dict:
    geom_type = face.geom_type
    geom_object = {}

    occ_geom_surface = BRepAdaptor_Surface(face.wrapped)

    if geom_type == GeomType.PLANE:
        location = face.center()
        normal = face.normal_at(location)
        geom_object["type"] = "PLANE"
        geom_object["location"] = (location.X, location.Y, location.Z)
        geom_object["normal"] = (normal.X, normal.Y, normal.Z)

    elif geom_type == GeomType.CYLINDER:
        cylinder_geom = occ_geom_surface.Cylinder()
        radius = cylinder_geom.Radius()
        loc = cylinder_geom.Location()
        dir = cylinder_geom.Axis().Direction()
        geom_object["type"] = "CYLINDER"
        geom_object["radius"] = radius
        geom_object["axis_location"] = (loc.X(), loc.Y(), loc.Z())
        geom_object["axis_direction"] = (dir.X(), dir.Y(), dir.Z())

    elif geom_type == GeomType.SPHERE:
        sphere_geom = occ_geom_surface.Sphere()
        radius = sphere_geom.Radius()
        center = sphere_geom.Location()
        geom_object["type"] = "SPHERE"
        geom_object["radius"] = radius
        geom_object["center"] = (center.X(), center.Y(), center.Z())

    elif geom_type == GeomType.CONE:
        cone_geom = occ_geom_surface.Cone()
        semi_angle = cone_geom.SemiAngle()
        radius = cone_geom.RefRadius()
        geom_object["type"] = "CONE"
        geom_object["semi_angle"] = semi_angle
        geom_object["radius"] = radius

    elif geom_type == GeomType.TORUS:
        torus_geom = occ_geom_surface.Torus()
        major_R = torus_geom.MajorRadius()
        minor_r = torus_geom.MinorRadius()
        geom_object["type"] = "TORUS"
        geom_object["major_R"] = major_R
        geom_object["minor_r"] = minor_r

    elif geom_type == GeomType.BSPLINE:
        bspline = occ_geom_surface.BSpline()
        num_poles = bspline.NbPoles()
        degree_u = bspline.UDegree()
        degree_v = bspline.VDegree()
        geom_object["type"] = "BSPLINE"
        geom_object["num_poles"] = num_poles
        geom_object["degree_u"] = degree_u
        geom_object["degree_v"] = degree_v

    else:
        geom_object["type"] = "UNKNOWN"

    return geom_object

# example: classify_surface_occ(shape.faces()[0])