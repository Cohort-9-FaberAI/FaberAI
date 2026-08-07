# OCP (OpenCASCADE) and build123d are imported inside classify_surface_occ
# rather than at module scope. They are optional STEP-only dependencies, and
# importing them here would make this module — and everything that imports it,
# including face_graph — unimportable on installs without them.


def _safe_bspline_properties(bspline) -> dict:
    props = {}
    for attr in ("NbPoles", "NbUPoles", "NbVPoles", "UDegree", "VDegree"):
        if hasattr(bspline, attr):
            try:
                props[attr] = getattr(bspline, attr)()
            except Exception:
                props[attr] = None
    return props


def classify_surface_occ(face) -> dict:
    geom_type = face.geom_type
    geom_object = {}

    try:
        from build123d import GeomType
        from OCP.BRepAdaptor import BRepAdaptor_Surface

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
            bspline_props = _safe_bspline_properties(bspline)
            num_poles = bspline_props.get("NbPoles")
            if num_poles is None:
                u_poles = bspline_props.get("NbUPoles")
                v_poles = bspline_props.get("NbVPoles")
                if u_poles is not None and v_poles is not None:
                    num_poles = u_poles * v_poles
            geom_object["type"] = "BSPLINE"
            if num_poles is not None:
                geom_object["num_poles"] = num_poles
            if bspline_props.get("UDegree") is not None:
                geom_object["degree_u"] = bspline_props.get("UDegree")
            if bspline_props.get("VDegree") is not None:
                geom_object["degree_v"] = bspline_props.get("VDegree")

        else:
            geom_object["type"] = "UNKNOWN"
    except Exception:
        geom_object = {"type": "UNKNOWN"}

    return geom_object

# example: classify_surface_occ(shape.faces()[0])