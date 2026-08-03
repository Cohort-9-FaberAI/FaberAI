from __future__ import annotations

import io
import logging
import os
from typing import Any

import numpy as np
import requests
import trimesh
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


COLOR_MAP: dict[str, tuple[int, int, int]] = {
    "red": (239, 83, 80),        # #ef5350
    "high": (239, 83, 80),
    "blocker": (239, 83, 80),
    "orange": (255, 183, 77),    # #ffb74d
    "medium": (255, 183, 77),
    "major": (255, 183, 77),
    "yellow": (255, 213, 79),    # #ffd54f
    "low": (255, 213, 79),
    "minor": (255, 213, 79),
    "green": (102, 187, 106),    # #66bb6a
    "pro": (102, 187, 106),
}


def _parse_color(color_str: str, default_severity: str = "medium") -> tuple[int, int, int]:
    val = str(color_str).lower().strip()
    if val in COLOR_MAP:
        return COLOR_MAP[val]
    if val.startswith("#") and len(val) >= 7:
        try:
            return (int(val[1:3], 16), int(val[3:5], 16), int(val[5:7], 16))
        except Exception:
            pass
    return COLOR_MAP.get(default_severity.lower(), (255, 183, 77))


def extract_issue_markers(analysis: dict[str, Any], mesh_verts: np.ndarray) -> list[tuple[int, tuple[int, int, int]]]:
    """Extracts issue centroids from analysis, snaps them to the nearest mesh vertex, and pairs them with RGB color."""
    if len(mesh_verts) == 0:
        return []

    raw_markers: list[tuple[np.ndarray, str]] = []

    issues = analysis.get("issues") or []
    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            severity = str(issue.get("severity", "medium")).lower()
            if severity not in ("blocker", "major", "minor", "high", "medium", "low"):
                continue

            point = None
            for key in ("centroid", "three_js_highlight", "geometry_ref"):
                val = issue.get(key)
                if isinstance(val, dict):
                    if "center" in val and isinstance(val["center"], (list, dict)):
                        val = val["center"]
                    elif "centroid" in val and isinstance(val["centroid"], (list, dict)):
                        val = val["centroid"]
                    if isinstance(val, dict) and all(k in val for k in ("x", "y", "z")):
                        point = [float(val["x"]), float(val["y"]), float(val["z"])]
                        break
                    elif isinstance(val, list) and len(val) >= 3:
                        point = [float(val[0]), float(val[1]), float(val[2])]
                        break
                elif isinstance(val, list) and len(val) >= 3:
                    point = [float(val[0]), float(val[1]), float(val[2])]
                    break

            if point is not None:
                col_str = severity
                if isinstance(issue.get("three_js_highlight"), dict) and issue["three_js_highlight"].get("color"):
                    col_str = str(issue["three_js_highlight"]["color"])
                raw_markers.append((np.array(point, dtype=np.float64), col_str))

    if not raw_markers and isinstance(analysis.get("dfm_report"), dict):
        report = analysis["dfm_report"]
        for proc in report.get("processes", []):
            if not isinstance(proc, dict):
                continue
            for rule in proc.get("rule_results", []):
                if not isinstance(rule, dict):
                    continue
                status = str(rule.get("status", "")).lower()
                if status not in ("failed", "warning", "fail"):
                    continue
                severity = str(rule.get("severity", "medium")).lower()
                for finding in rule.get("findings", []):
                    if not isinstance(finding, dict):
                        continue
                    ref = finding.get("geometry_ref", {})
                    if isinstance(ref, dict) and "centroid" in ref:
                        c = ref["centroid"]
                        if isinstance(c, dict) and all(k in c for k in ("x", "y", "z")):
                            raw_markers.append((np.array([float(c["x"]), float(c["y"]), float(c["z"])], dtype=np.float64), severity))
                        elif isinstance(c, list) and len(c) >= 3:
                            raw_markers.append((np.array([float(c[0]), float(c[1]), float(c[2])], dtype=np.float64), severity))

    snapped: list[tuple[int, tuple[int, int, int]]] = []
    for pt, col_str in raw_markers:
        dists_sq = np.sum((mesh_verts - pt) ** 2, axis=1)
        best_idx = int(np.argmin(dists_sq))
        snapped.append((best_idx, _parse_color(col_str, col_str)))

    return snapped


def render_mesh_snapshot(
    mesh: trimesh.Trimesh,
    azimuth: float,
    elevation: float,
    markers: list[tuple[int, tuple[int, int, int]]] | None = None,
    width: int = 496,
    height: int = 312,
    bg_color: tuple[int, int, int] = (247, 250, 254),
    ssaa_factor: int = 2,
) -> io.BytesIO:
    """Renders an anti-aliased Z-buffered 3D snapshot using Lanczos super-sampling (SSAA)."""
    if markers is None:
        markers = []

    verts = mesh.vertices.copy()
    faces = mesh.faces
    raw_normals = mesh.face_normals

    # Center vertices around origin
    center = (verts.min(axis=0) + verts.max(axis=0)) / 2.0
    verts -= center

    bound_radius = float(np.linalg.norm(verts, axis=1).max()) if len(verts) > 0 else 1.0
    bound_radius = max(bound_radius, 1e-5)

    theta = np.radians(azimuth)

    # In mechanical engineering CAD, Z is vertical height. Rotate azimuth around Z axis (turntable yaw)
    R_z = np.array([
        [np.cos(theta), -np.sin(theta), 0.0],
        [np.sin(theta),  np.cos(theta), 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float64)

    # Tilt around X axis by (90° - elevation) so +Z tilts up onto screen +Y
    tilt = np.radians(90.0 - elevation)
    R_x = np.array([
        [1.0, 0.0, 0.0],
        [0.0, np.cos(tilt), -np.sin(tilt)],
        [0.0, np.sin(tilt),  np.cos(tilt)],
    ], dtype=np.float64)

    R = R_x @ R_z
    v_rot = verts @ R.T
    rot_normals = raw_normals @ R.T

    cam_dist = bound_radius * 7.5
    denom = np.maximum(cam_dist - v_rot[:, 2], 1e-3)
    persp_factor = cam_dist / denom

    xs = v_rot[:, 0] * persp_factor
    ys = v_rot[:, 1] * persp_factor
    zs = v_rot[:, 2]

    # SSAA virtual resolution scaling
    rw = width * ssaa_factor
    rh = height * ssaa_factor

    # Master scale fixed across all angles based on bounding sphere radius so part size stays stable
    scale = 0.45 * min(rw, rh) / bound_radius

    # Centered directly in frame canvas
    scr_x = (rw / 2.0) + xs * scale
    scr_y = (rh / 2.0) - ys * scale

    # Initialize Z-buffer and image buffer for pixel-accurate hardware-style rasterization
    z_buffer = np.full((rh, rw), -1e9, dtype=np.float32)
    img_buffer = np.full((rh, rw, 3), bg_color, dtype=np.uint8)
    y_grid, x_grid = np.mgrid[0:rh, 0:rw]

    # 3-Point studio lighting setup matching Three.js scene brightness and depth
    l_key = np.array([0.52, 0.75, 0.41], dtype=np.float64)
    l_key /= np.linalg.norm(l_key)

    l_fill = np.array([-0.55, 0.25, 0.35], dtype=np.float64)
    l_fill /= np.linalg.norm(l_fill)

    l_rim = np.array([0.0, -0.45, -0.75], dtype=np.float64)
    l_rim /= np.linalg.norm(l_rim)

    d_key = np.clip(np.dot(rot_normals, l_key), 0.0, 1.0)
    d_fill = np.clip(np.dot(rot_normals, l_fill), 0.0, 1.0)
    d_rim = np.clip(np.dot(rot_normals, l_rim), 0.0, 1.0)

    intensity = 0.45 + 0.42 * d_key + 0.09 * d_fill + 0.04 * d_rim

    # Faber Blue Accent (PRIMARY #0858f4): RGB (8, 88, 244)
    r_vals = np.clip(8 * intensity, 0, 255).astype(np.uint8)
    g_vals = np.clip(88 * intensity, 0, 255).astype(np.uint8)
    b_vals = np.clip(244 * intensity, 0, 255).astype(np.uint8)

    # Filter to front-facing visible triangles (normal pointing out of screen towards viewer, +Z)
    vis_mask = rot_normals[:, 2] > -0.05
    vis_faces = faces[vis_mask]
    vis_r = r_vals[vis_mask]
    vis_g = g_vals[vis_mask]
    vis_b = b_vals[vis_mask]

    if len(vis_faces) > 0:
        f_x0 = scr_x[vis_faces[:, 0]]
        f_y0 = scr_y[vis_faces[:, 0]]
        f_z0 = zs[vis_faces[:, 0]]

        f_x1 = scr_x[vis_faces[:, 1]]
        f_y1 = scr_y[vis_faces[:, 1]]
        f_z1 = zs[vis_faces[:, 1]]

        f_x2 = scr_x[vis_faces[:, 2]]
        f_y2 = scr_y[vis_faces[:, 2]]
        f_z2 = zs[vis_faces[:, 2]]

        # Compute twice-area determinant for barycentric coordinate transformation
        area = f_x0 * (f_y1 - f_y2) + f_x1 * (f_y2 - f_y0) + f_x2 * (f_y0 - f_y1)
        valid = np.abs(area) > 1e-4

        for i in np.where(valid)[0]:
            x0, y0, z0 = f_x0[i], f_y0[i], f_z0[i]
            x1, y1, z1 = f_x1[i], f_y1[i], f_z1[i]
            x2, y2, z2 = f_x2[i], f_y2[i], f_z2[i]
            a = area[i]

            xmin = max(int(min(x0, x1, x2)), 0)
            xmax = min(int(max(x0, x1, x2)) + 1, rw)
            ymin = max(int(min(y0, y1, y2)), 0)
            ymax = min(int(max(y0, y1, y2)) + 1, rh)

            if xmin >= xmax or ymin >= ymax:
                continue

            Y, X = y_grid[ymin:ymax, xmin:xmax], x_grid[ymin:ymax, xmin:xmax]
            w0 = ((x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)) / a
            w1 = ((x0 - x2) * (Y - y2) - (y0 - y2) * (X - x2)) / a
            w2 = 1.0 - w0 - w1

            # Micro-margin (-0.005) eradicates single-pixel seams between adjacent faces
            mask = (w0 >= -0.005) & (w1 >= -0.005) & (w2 >= -0.005)
            if not np.any(mask):
                continue

            z_pix = w0 * z0 + w1 * z1 + w2 * z2
            closer = mask & (z_pix > z_buffer[ymin:ymax, xmin:xmax])
            if np.any(closer):
                z_buffer[ymin:ymax, xmin:xmax][closer] = z_pix[closer]
                img_buffer[ymin:ymax, xmin:xmax][closer] = [vis_r[i], vis_g[i], vis_b[i]]

    img = Image.fromarray(img_buffer, "RGB")
    draw = ImageDraw.Draw(img)

    for vert_idx, col_rgb in markers:
        if vert_idx >= len(v_rot):
            continue
        mx, my = float(scr_x[vert_idx]), float(scr_y[vert_idx])
        mz = float(zs[vert_idx])

        imx, imy = int(round(mx)), int(round(my))
        if 0 <= imx < rw and 0 <= imy < rh:
            curr_z = z_buffer[imy, imx]
            if mz < curr_z - (0.01 * bound_radius):
                continue

        r = 4.5 * ssaa_factor
        w = 1 * ssaa_factor
        draw.ellipse([mx - r, my - r, mx + r, my + r], fill=col_rgb, outline=(255, 255, 255), width=w)

    # Downsample super-sampled image back to standard resolution using high-quality Lanczos filter for perfectly smooth anti-aliasing
    if ssaa_factor > 1:
        img = img.resize((width, height), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


def _load_mesh_from_source(file_url: str) -> trimesh.Trimesh | None:
    try:
        if os.path.exists(file_url):
            mesh = trimesh.load(file_url, force="mesh")
        elif file_url.startswith("http://") or file_url.startswith("https://"):
            logger.info("Downloading mesh from %s for PDF snapshot generation", file_url)
            response = requests.get(file_url, timeout=20)
            if response.status_code != 200:
                logger.warning("Failed to download mesh from %s (status %d)", file_url, response.status_code)
                return None
            file_obj = io.BytesIO(response.content)
            file_obj.name = "model.stl"
            mesh = trimesh.load(file_obj, file_type="stl", force="mesh")
        else:
            logger.warning("Unrecognized file URL or path for PDF snapshots: %s", file_url)
            return None

        if isinstance(mesh, trimesh.Scene):
            if not mesh.geometry:
                return None
            mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
        if isinstance(mesh, trimesh.Trimesh) and len(mesh.faces) > 0:
            return mesh
    except Exception as exc:
        logger.warning("Error loading mesh for PDF snapshot rendering: %s", exc)
    return None


def generate_mesh_snapshots(analysis: dict[str, Any]) -> list[io.BytesIO]:
    """Generates 4 studio-grade Z-buffered CAD snapshots with issue markers from standard isometric viewing angles."""
    file_url = analysis.get("file_url") or analysis.get("source_file_url")
    if not file_url or not isinstance(file_url, str):
        return []

    mesh = _load_mesh_from_source(file_url)
    if mesh is None:
        return []

    markers = extract_issue_markers(analysis, mesh.vertices)

    # 4 standard engineering isometric rotations around Z axis at consistent 30-degree elevation
    angles = [
        (45.0, 30.0),    # View 1: Front-Right isometric
        (135.0, 30.0),   # View 2: Back-Right isometric
        (225.0, 30.0),   # View 3: Back-Left isometric
        (315.0, 30.0),   # View 4: Front-Left isometric
    ]

    snapshots: list[io.BytesIO] = []
    for azimuth, elevation in angles:
        try:
            snap = render_mesh_snapshot(mesh, azimuth, elevation, markers=markers)
            snapshots.append(snap)
        except Exception as exc:
            logger.warning("Failed to render snapshot at (%s, %s): %s", azimuth, elevation, exc)
    return snapshots
