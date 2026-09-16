"""Procedurally rebuild the campus in a brand-new Blender scene.

This script intentionally contains only measured anchors and design primitives.
It never opens, imports, or copies geometry from the locked SketchUp reference.
Run with Blender 5.x in background mode:

    blender --background --python tools/build_campus_recreated.py
"""

from __future__ import annotations

from math import atan2, cos, exp, pi, sin, sqrt
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submissions" / "codex" / "campus_recreated.blend"
QA_DIR = Path(r"E:/codex/tmp_campus_inspect")


# The source model is expressed in a different horizontal convention.  The
# reconstruction uses Blender's conventional X/Y/Z: X east-west, Y elevation,
# Z north-south.  These numbers are measured layout anchors, not source mesh
# data.  The campus envelope is approximately 673 m x 402 m.


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def terrain_height(x: float, z: float) -> float:
    """Low-frequency hilly ground, with terraces placed above this surface."""
    h = 2.0
    h += 0.000035 * (x - 260.0) ** 2
    h += 0.000028 * (z + 235.0) ** 2
    h += 0.8 * sin(x / 58.0) + 0.55 * cos(z / 47.0)
    h += 4.2 * exp(-(((x - 335.0) / 105.0) ** 2 + ((z + 70.0) / 78.0) ** 2))
    h += 2.0 * exp(-(((x - 135.0) / 72.0) ** 2 + ((z + 195.0) / 92.0) ** 2))
    h -= 2.0 * exp(-(((x - 315.0) / 115.0) ** 2 + ((z + 330.0) / 52.0) ** 2))
    return clamp(h, -0.2, 15.0)


COLLECTIONS: dict[str, bpy.types.Collection] = {}
MATS: dict[str, bpy.types.Material] = {}


def make_material(name, color, roughness=0.72, metallic=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Transmission Weight" in bsdf.inputs and alpha < 1.0:
            bsdf.inputs["Transmission Weight"].default_value = 0.35
    if alpha < 1.0:
        try:
            mat.surface_render_method = "DITHERED"
        except Exception:
            pass
    return mat


def setup_materials():
    colors = {
        "terrain": ((0.19, 0.30, 0.14), 0.95, 0.0, 1.0),
        "terrain_side": ((0.12, 0.18, 0.10), 1.0, 0.0, 1.0),
        "grass": ((0.20, 0.43, 0.18), 0.92, 0.0, 1.0),
        "grass_light": ((0.34, 0.58, 0.23), 0.85, 0.0, 1.0),
        "track_red": ((0.63, 0.07, 0.045), 0.76, 0.0, 1.0),
        "track_lane": ((0.93, 0.67, 0.43), 0.70, 0.0, 1.0),
        "asphalt": ((0.055, 0.070, 0.085), 0.88, 0.0, 1.0),
        "road_mark": ((0.89, 0.79, 0.49), 0.7, 0.0, 1.0),
        "concrete": ((0.52, 0.54, 0.52), 0.87, 0.0, 1.0),
        "paving": ((0.63, 0.59, 0.51), 0.8, 0.0, 1.0),
        "paving_light": ((0.76, 0.72, 0.62), 0.78, 0.0, 1.0),
        "brick": ((0.70, 0.31, 0.18), 0.78, 0.0, 1.0),
        "brick_light": ((0.86, 0.56, 0.34), 0.75, 0.0, 1.0),
        "cream": ((0.82, 0.75, 0.61), 0.82, 0.0, 1.0),
        "blue": ((0.08, 0.22, 0.52), 0.78, 0.1, 1.0),
        "blue_light": ((0.24, 0.48, 0.72), 0.62, 0.05, 1.0),
        "roof": ((0.12, 0.14, 0.16), 0.72, 0.1, 1.0),
        "roof_rust": ((0.36, 0.12, 0.08), 0.72, 0.0, 1.0),
        "glass": ((0.18, 0.54, 0.67), 0.18, 0.15, 0.40),
        "steel": ((0.28, 0.31, 0.34), 0.34, 0.65, 1.0),
        "white": ((0.94, 0.92, 0.84), 0.75, 0.0, 1.0),
        "line": ((0.96, 0.92, 0.70), 0.62, 0.0, 1.0),
        "water": ((0.10, 0.39, 0.55), 0.18, 0.15, 0.72),
        "trunk": ((0.20, 0.10, 0.045), 1.0, 0.0, 1.0),
        "canopy": ((0.08, 0.26, 0.10), 0.95, 0.0, 1.0),
        "canopy_light": ((0.25, 0.43, 0.12), 0.9, 0.0, 1.0),
        "court_blue": ((0.10, 0.38, 0.63), 0.84, 0.0, 1.0),
        "court_green": ((0.16, 0.48, 0.28), 0.84, 0.0, 1.0),
        "court_red": ((0.55, 0.13, 0.09), 0.84, 0.0, 1.0),
        "source_cyan": ((0.36, 0.78, 0.86), 0.45, 0.05, 1.0),
        "source_yellow": ((0.88, 0.72, 0.08), 0.65, 0.0, 1.0),
        "source_rose": ((0.78, 0.34, 0.48), 0.76, 0.0, 1.0),
        "source_orange": ((0.88, 0.37, 0.07), 0.76, 0.0, 1.0),
        "wood": ((0.35, 0.18, 0.08), 0.9, 0.0, 1.0),
    }
    for name, (color, roughness, metallic, alpha) in colors.items():
        MATS[name] = make_material(name, color, roughness, metallic, alpha)


def setup_collections():
    root = bpy.data.collections.new("Campus_Recreated")
    bpy.context.scene.collection.children.link(root)
    for name in (
        "Terrain",
        "Roads",
        "Platforms",
        "Bridges",
        "Buildings",
        "Sports",
        "Stairs",
        "Details",
    ):
        col = bpy.data.collections.new(name)
        root.children.link(col)
        COLLECTIONS[name] = col


def link_object(obj, collection_name):
    target = COLLECTIONS[collection_name]
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    target.objects.link(obj)


def set_props(obj, role, basis="measured anchor; procedural reconstruction"):
    obj["campus_role"] = role
    obj["reconstruction_basis"] = basis
    obj["source_geometry_copied"] = False


def mesh_object(name, verts, faces, material, collection_name, role):
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    COLLECTIONS[collection_name].objects.link(obj)
    if material:
        obj.data.materials.append(MATS[material] if isinstance(material, str) else material)
    set_props(obj, role)
    return obj


def rotate_xz(x, z, angle):
    c, s = cos(angle), sin(angle)
    return c * x - s * z, s * x + c * z


def add_box(name, center, size, material, collection_name, role="massing", angle=0.0, bevel=0.0):
    cx, cy, cz = center
    sx, sy, sz = (v * 0.5 for v in size)
    verts = []
    for yy in (-sy, sy):
        for zz in (-sz, sz):
            for xx in (-sx, sx):
                rx, rz = rotate_xz(xx, zz, angle)
                verts.append((cx + rx, cy + yy, cz + rz))
    # index: bottom front-left/front-right/back-left/back-right, then top
    faces = [
        (0, 1, 3, 2),
        (4, 6, 7, 5),
        (0, 4, 5, 1),
        (2, 3, 7, 6),
        (0, 2, 6, 4),
        (1, 5, 7, 3),
    ]
    obj = mesh_object(name, verts, faces, material, collection_name, role)
    if bevel:
        mod = obj.modifiers.new("Soft architectural edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def add_prism(name, footprint, bottom, top, material, collection_name, role="platform"):
    n = len(footprint)
    verts = [(x, bottom, z) for x, z in footprint] + [(x, top, z) for x, z in footprint]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_cylinder(name, center, radius, depth, material, collection_name, role="detail", sides=12):
    cx, cy, cz = center
    verts = []
    for y in (cy - depth * 0.5, cy + depth * 0.5):
        for i in range(sides):
            a = 2 * pi * i / sides
            verts.append((cx + radius * cos(a), y, cz + radius * sin(a)))
    faces = [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_cone(name, center, radius, depth, material, collection_name, role="detail", sides=10):
    cx, cy, cz = center
    verts = [(cx, cy + depth * 0.5, cz)]
    for i in range(sides):
        a = 2 * pi * i / sides
        verts.append((cx + radius * cos(a), cy - depth * 0.5, cz + radius * sin(a)))
    faces = []
    for i in range(sides):
        faces.append((0, 1 + i, 1 + ((i + 1) % sides)))
    faces.append(tuple(range(sides, 0, -1)))
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_uv_dome(name, center, radius, material, collection_name, role="landscape", rings=5, segments=10):
    cx, cy, cz = center
    verts = [(cx, cy + radius, cz)]
    for r in range(1, rings + 1):
        phi = (pi * 0.5) * r / rings
        rr = radius * sin(phi)
        yy = cy + radius * cos(phi)
        for i in range(segments):
            a = 2 * pi * i / segments
            verts.append((cx + rr * cos(a), yy, cz + rr * sin(a)))
    faces = []
    for i in range(segments):
        faces.append((0, 1 + i, 1 + ((i + 1) % segments)))
    for r in range(rings - 1):
        start_a = 1 + r * segments
        start_b = start_a + segments
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((start_a + i, start_b + i, start_b + j, start_a + j))
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_terrain():
    nx, nz = 38, 28
    xmin, xmax = -32.0, 690.0
    zmin, zmax = -432.0, 32.0
    verts = []
    for iz in range(nz + 1):
        z = zmin + (zmax - zmin) * iz / nz
        for ix in range(nx + 1):
            x = xmin + (xmax - xmin) * ix / nx
            verts.append((x, terrain_height(x, z), z))
    faces = []
    for iz in range(nz):
        for ix in range(nx):
            a = iz * (nx + 1) + ix
            b = a + 1
            c = a + nx + 2
            d = a + nx + 1
            faces.append((a, b, c, d))
    # Give the site a visible cut edge rather than a paper-thin plane.
    top_count = len(verts)
    for v in verts[:top_count]:
        verts.append((v[0], -8.0, v[2]))
    for iz in range(nz):
        a = iz * (nx + 1)
        b = (iz + 1) * (nx + 1) - 1
        faces.append((a, b, b + top_count, a + top_count))
        a = iz * (nx + 1) + nx
        b = (iz + 1) * (nx + 1) + nx
        faces.append((a, a + top_count, b + top_count, b))
    a = 0
    b = nx
    c = nx + 1
    d = 1
    faces.append((a, a + top_count, b + top_count, b))
    a = nz * (nx + 1)
    b = a + nx
    faces.append((a, b, b + top_count, a + top_count))
    ground = mesh_object(
        "Terrain_Hillside",
        verts,
        faces,
        "terrain",
        "Terrain",
        "terrain envelope",
    )
    for poly in ground.data.polygons[: nx * nz]:
        poly.use_smooth = True
    ground.data.materials.append(MATS["terrain_side"])
    # Low retaining bands help read the terraced topography in the oblique view.
    for x, z, w, d, y in (
        (265, -303, 120, 3, 8.2),
        (360, -208, 112, 3, 20.0),
        (403, -276, 70, 3, 22.5),
    ):
        add_box(f"Retaining_Wall_{x}_{z}", (x, y - 1.0, z), (w, 2.0, d), "terrain_side", "Terrain", "retaining wall")


def add_corridor(name, points, width, y, material="asphalt", collection_name="Roads", role="road"):
    """Create a clean, independently selectable polygonal strip."""
    left, right = [], []
    for i, (x, z) in enumerate(points):
        if i == 0:
            dx, dz = points[1][0] - x, points[1][1] - z
        elif i == len(points) - 1:
            dx, dz = x - points[i - 1][0], z - points[i - 1][1]
        else:
            dx, dz = points[i + 1][0] - points[i - 1][0], points[i + 1][1] - points[i - 1][1]
        length = max(0.01, sqrt(dx * dx + dz * dz))
        nx, nz = -dz / length * width * 0.5, dx / length * width * 0.5
        left.append((x + nx, z + nz))
        right.append((x - nx, z - nz))
    footprint = left + list(reversed(right))
    return add_prism(name, footprint, y - 0.16, y, material, collection_name, role)


def add_path_segments(name, points, width, heights, material="paving", collection_name="Roads"):
    for i in range(len(points) - 1):
        (x1, z1), (x2, z2) = points[i], points[i + 1]
        length = sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)
        angle = atan2(x2 - x1, z2 - z1)  # local Z-aligned segment
        y = (heights[i] + heights[i + 1]) * 0.5
        add_box(
            f"{name}_{i+1:02d}",
            ((x1 + x2) * 0.5, y, (z1 + z2) * 0.5),
            (width, 0.22, length),
            material,
            collection_name,
            "pedestrian path",
            angle=-angle,
        )


def add_roads_and_plazas():
    # The main perimeter roads establish the full campus extent.
    add_corridor("South_Perimeter_Road", [(-20, -416), (228, -416), (460, -410), (690, -393)], 19, 1.1)
    add_corridor("West_Perimeter_Road", [(34, -400), (48, -270), (67, -140), (90, -28)], 15, 1.3)
    add_corridor("East_Perimeter_Road", [(618, -401), (642, -300), (648, -177), (647, -36)], 16, 1.5)
    # The diagonal spine and cross avenue follow the measured campus skeleton.
    add_corridor(
        "Central_Diagonal_Avenue",
        [(208, -375), (248, -340), (273, -300), (304, -264), (331, -227), (353, -185), (373, -142), (395, -105), (409, -57)],
        12,
        12.0,
    )
    add_corridor(
        "Middle_Cross_Avenue",
        [(178, -249), (251, -243), (323, -244), (404, -256), (500, -283), (620, -318)],
        11,
        10.5,
    )
    add_corridor("North_Avenue", [(215, -73), (303, -69), (403, -73), (495, -92)], 10, 15.0)
    add_corridor("South_Campus_Avenue", [(194, -382), (283, -372), (382, -374), (503, -363), (625, -346)], 10, 6.0)
    # Courtyards / broad inter-building decks.
    add_prism("West_Courtyard_Plaza", [(226, -284), (286, -284), (291, -219), (235, -219)], 12.2, 13.0, "paving", "Platforms", "courtyard plaza")
    add_prism("Central_Library_Terrace", [(277, -300), (356, -300), (372, -236), (319, -210), (273, -241)], 18.0, 18.8, "paving_light", "Platforms", "terraced plaza")
    add_prism("Upper_Research_Terrace", [(302, -185), (414, -185), (426, -115), (310, -113)], 29.4, 30.1, "concrete", "Platforms", "upper platform")
    add_prism("East_Complex_Terrace", [(378, -283), (444, -283), (445, -215), (381, -211)], 22.5, 23.3, "paving", "Platforms", "upper platform")
    add_prism("South_Sports_Platform", [(274, -363), (365, -363), (365, -290), (274, -290)], 8.8, 9.5, "concrete", "Platforms", "sports platform")
    add_prism("West_Field_Plaza", [(74, -249), (213, -249), (213, -38), (75, -38)], 5.0, 5.35, "paving", "Platforms", "athletics precinct")
    # Lane separators and pedestrian crossings keep the road network readable
    # at the same scale as the supplied aerial reference.
    for i, (x, z) in enumerate(((226, -415), (302, -413), (379, -411), (457, -407), (534, -400))):
        add_box(f"South_Road_Marking_{i+1:02d}", (x, 1.30, z), (5.2, 0.05, 0.28), "road_mark", "Roads", "road lane marking")
    for i, (x, z) in enumerate(((256, -321), (276, -292), (298, -263), (320, -231), (340, -198), (359, -164))):
        add_box(f"Spine_Crosswalk_{i+1:02d}", (x, 12.24, z), (7.5, 0.05, 1.0), "road_mark", "Roads", "pedestrian crossing", angle=-0.55)
    for i, (x, z) in enumerate(((248, -243), (310, -245), (374, -250), (442, -266), (514, -289))):
        add_box(f"Middle_Avenue_Marking_{i+1:02d}", (x, 10.74, z), (4.0, 0.05, 0.25), "road_mark", "Roads", "road lane marking", angle=0.18)


def facade_bands(name, x, z, width, depth, base, height, floors, body, angle=0.0):
    """A restrained set of facade bands that reads at campus scale."""
    for floor in range(floors):
        yy = base + 2.2 + floor * (height / max(1, floors))
        for side in (-1, 1):
            ox, oz = rotate_xz(0.0, side * (depth * 0.5 + 0.045), angle)
            add_box(
                f"{name}_FacadeBand_{floor+1}_{'N' if side < 0 else 'S'}",
                (x + ox, yy, z + oz),
                (max(2.0, width - 1.5), 0.82, 0.08),
                "blue_light" if body not in ("blue", "blue_light") else "glass",
                "Buildings",
                "window band",
                angle=angle,
            )


def local_box_point(x, z, ox, oz, angle):
    rx, rz = rotate_xz(ox, oz, angle)
    return x + rx, z + rz


def facade_windows_and_pilasters(name, x, z, width, depth, base, height, floors, angle=0.0, balconies=False):
    """Reconstruct repeated facade rhythm without flattening buildings to boxes."""
    floor_h = height / max(1, floors)
    window_h = clamp(floor_h * 0.46, 1.05, 1.8)
    for floor in range(floors):
        yy = base + floor_h * (floor + 0.56)
        count = max(2, min(15, int(width / 4.0)))
        span = max(2.0, width - 2.4)
        gap = span / count
        panel_w = max(0.65, gap * 0.56)
        for side in (-1, 1):
            facade_z = side * (depth * 0.5 + 0.055)
            for j in range(count):
                ox = -span * 0.5 + gap * (j + 0.5)
                px, pz = local_box_point(x, z, ox, facade_z, angle)
                add_box(
                    f"{name}_Window_{floor+1:02d}_{'F' if side < 0 else 'B'}_{j+1:02d}",
                    (px, yy, pz),
                    (panel_w, window_h, 0.10),
                    "glass",
                    "Buildings",
                    "reconstructed window panel",
                    angle=angle,
                )
            # Structural piers keep the facade legible between window modules.
            for j in range(count + 1):
                ox = -span * 0.5 + gap * j
                px, pz = local_box_point(x, z, ox, facade_z - side * 0.02, angle)
                add_box(
                    f"{name}_Pier_{floor+1:02d}_{'F' if side < 0 else 'B'}_{j+1:02d}",
                    (px, yy, pz),
                    (0.12, window_h + 0.36, 0.14),
                    "cream" if floor % 2 else "concrete",
                    "Buildings",
                    "facade vertical pier",
                    angle=angle,
                )
        side_count = max(2, min(5, int(depth / 3.7)))
        side_span = max(2.0, depth - 2.0)
        side_gap = side_span / side_count
        side_panel = max(0.65, side_gap * 0.50)
        for side in (-1, 1):
            facade_x = side * (width * 0.5 + 0.055)
            for j in range(side_count):
                oz = -side_span * 0.5 + side_gap * (j + 0.5)
                px, pz = local_box_point(x, z, facade_x, oz, angle)
                add_box(
                    f"{name}_SideWindow_{floor+1:02d}_{'L' if side < 0 else 'R'}_{j+1:02d}",
                    (px, yy, pz),
                    (0.10, window_h, side_panel),
                    "glass",
                    "Buildings",
                    "reconstructed side window",
                    angle=angle,
                )
    if balconies and width >= 20.0:
        for floor in range(1, max(1, floors)):
            yy = base + floor_h * floor + 0.16
            ox, oz = local_box_point(x, z, 0.0, depth * 0.5 + 0.70, angle)
            add_box(f"{name}_Balcony_{floor:02d}", (ox, yy, oz), (min(9.0, width * 0.35), 0.20, 1.25), "concrete", "Buildings", "balcony slab", angle=angle)
            rail_x, rail_z = local_box_point(x, z, 0.0, depth * 0.5 + 1.30, angle)
            add_cylinder_between(f"{name}_BalconyRail_{floor:02d}", (rail_x - 2.5, yy + 0.75, rail_z), (rail_x + 2.5, yy + 0.75, rail_z), 0.045, "steel", "Details", "balcony rail")


def rooftop_equipment(name, x, z, width, depth, roof_y, angle=0.0):
    """Small rooftop elements prevent the upper skyline from reading as a flat cap."""
    for i, (ox, oz, sx, sz, material) in enumerate(
        (
            (-width * 0.25, -depth * 0.18, min(4.2, width * 0.18), min(3.0, depth * 0.22), "steel"),
            (width * 0.20, depth * 0.16, min(3.6, width * 0.16), min(2.6, depth * 0.20), "roof"),
        )
    ):
        px, pz = local_box_point(x, z, ox, oz, angle)
        add_box(f"{name}_RoofPlant_{i+1}", (px, roof_y + 0.9, pz), (sx, 1.8, sz), material, "Details", "rooftop plant", angle=angle)
    px, pz = local_box_point(x, z, width * 0.04, depth * 0.05, angle)
    add_box(f"{name}_RoofSkylight", (px, roof_y + 0.55, pz), (min(8.0, width * 0.22), 0.22, min(3.5, depth * 0.22)), "glass", "Details", "rooftop skylight", angle=angle)


def add_building(name, x, z, width, depth, base, height, body="cream", roof="roof", floors=3, angle=0.0, bands=True):
    add_box(f"{name}_Massing", (x, base + height * 0.5, z), (width, height, depth), body, "Buildings", "building massing", angle, bevel=0.35)
    add_box(f"{name}_Roof", (x, base + height + 0.35, z), (width + 1.0, 0.7, depth + 1.0), roof, "Buildings", "roof slab", angle, bevel=0.18)
    if bands:
        facade_bands(name, x, z, width, depth, base, height, floors, body, angle)
    facade_windows_and_pilasters(name, x, z, width, depth, base, height, floors, angle, balconies=(width >= 24.0 and floors <= 3))
    rooftop_equipment(name, x, z, width, depth, base + height, angle)
    # A small entrance canopy gives the large blocks a human-scale datum.
    ox, oz = rotate_xz(0.0, depth * 0.5 + 1.6, angle)
    add_box(f"{name}_Entry", (x + ox, base + 2.2, z + oz), (min(width * 0.45, 12), 0.35, 3.2), "paving_light", "Details", "building entrance", angle=angle)


def add_stepped_building(name, x, z, width, depth, base, height, body="brick", angle=0.0):
    # Three overlapping terraces approximate the stepped massing visible in the
    # upper and east complexes while remaining independently selectable.
    parts = ((0.72, 0.42), (0.86, 0.33), (1.0, 0.25))
    for i, (scale, frac) in enumerate(parts):
        h = height * frac
        yy = base + sum(height * p[1] for p in parts[:i]) + h * 0.5
        add_box(f"{name}_Step_{i+1}", (x, yy, z), (width * scale, h, depth * scale), body if i != 2 else "cream", "Buildings", "stepped building mass", angle, bevel=0.28)
        add_box(f"{name}_Step_{i+1}_Roof", (x, yy + h * 0.5 + 0.25, z), (width * scale + 0.7, 0.45, depth * scale + 0.7), "roof_rust", "Buildings", "stepped roof", angle)
        facade_windows_and_pilasters(
            f"{name}_Step_{i+1}",
            x,
            z,
            width * scale,
            depth * scale,
            base + sum(height * p[1] for p in parts[:i]),
            h,
            max(1, int(round(h / 3.4))),
            angle,
            balconies=(i == 2 and width >= 30.0),
        )
    rooftop_equipment(name, x, z, width, depth, base + height, angle)


def add_buildings():
    # West / dormitory precinct around the long athletics field.
    for i, (x, z, w, d, h, ang) in enumerate(
        (
            (93, -72, 33, 15, 10, 0.08),
            (136, -55, 39, 16, 12, 0.05),
            (181, -76, 30, 14, 9, -0.06),
            (91, -125, 28, 14, 12, 0.05),
            (190, -128, 32, 15, 12, -0.04),
            (84, -185, 30, 16, 11, 0.1),
            (196, -190, 34, 15, 10, -0.1),
            (92, -226, 31, 14, 12, 0.04),
        )
    ):
        add_building(f"West_Residence_{i+1:02d}", x, z, w, d, terrain_height(x, z) + 0.5, h, "brick_light", "roof_rust", floors=2, angle=ang, bands=False)

    # Long north teaching bars: anchors correspond to the measured 60 m and
    # 46 m components at the north edge of the core.
    add_building("North_Teaching_Block_A", 367.5, -29.0, 62.0, 39.0, 22.5, 14.5, "blue", "roof", floors=4, bands=True)
    add_building("North_Teaching_Block_B", 378.5, -132.5, 61.0, 17.0, 22.0, 14.0, "cream", "roof_rust", floors=4, bands=True)
    add_building("North_Teaching_Block_C", 320.0, -130.5, 46.0, 11.0, 22.0, 13.5, "brick_light", "roof", floors=3, bands=True)
    add_stepped_building("North_Research_Link", 331.0, -147.0, 48.0, 61.0, 20.5, 14.0, "cream", angle=-0.03)
    add_building("North_Auditorium", 429.0, -95.0, 37.0, 26.0, 19.0, 11.0, "brick", "roof_rust", floors=2, bands=False)
    add_box("North_Auditorium_Glass_Front", (429.0, 24.1, -81.2), (29.0, 7.0, 0.55), "glass", "Buildings", "glass facade")

    # West core / lower campus blocks.
    add_building("West_Academic_Block", 260.0, -231.0, 39.0, 9.0, 12.6, 11.0, "brick", "roof_rust", floors=2, bands=True)
    add_building("West_Lecture_Block", 260.0, -274.0, 8.0, 20.0, 11.8, 15.5, "blue", "roof", floors=3, bands=False)
    add_building("West_Science_Block", 293.0, -219.0, 25.0, 15.0, 13.0, 12.0, "cream", "roof", floors=3, bands=True)
    add_box("West_Tower_Sign", (236.0, 32.0, -239.0), (5.5, 5.0, 27.0), "blue", "Buildings", "vertical campus marker")
    add_box("West_Tower_Sign_Cap", (236.0, 35.0, -239.0), (6.5, 1.0, 28.0), "roof_rust", "Buildings", "vertical campus marker")

    # Central platform buildings and the large east multi-level complex.
    add_stepped_building("Central_Library", 316.0, -262.0, 60.0, 48.0, 15.0, 17.0, "blue", angle=0.02)
    add_building("Central_Student_Center", 353.0, -224.0, 32.0, 43.0, 17.5, 10.0, "brick_light", "roof_rust", floors=2, bands=True, angle=-0.04)
    add_stepped_building("East_Administration_Complex", 406.0, -248.0, 43.0, 48.0, 20.5, 12.0, "cream", angle=-0.025)
    add_building("East_Forum", 422.0, -204.0, 28.0, 26.0, 22.0, 9.0, "blue", "roof", floors=2, bands=True)
    add_building("East_Tower", 366.0, -247.0, 10.0, 15.0, 19.5, 21.0, "brick", "roof_rust", floors=4, bands=False)
    add_box("East_Tower_Core", (366.0, 31.0, -247.0), (4.0, 20.0, 9.0), "glass", "Buildings", "vertical circulation core")

    # South/east sports and service buildings.
    add_building("South_Gymnasium", 402.0, -332.0, 44.0, 31.0, 8.7, 9.5, "brick", "roof_rust", floors=2, bands=False)
    add_building("South_Cafeteria", 466.0, -310.0, 52.0, 24.0, 8.0, 8.5, "cream", "roof", floors=2, bands=True)
    add_building("South_Dormitory_A", 500.0, -352.0, 73.0, 18.0, 7.0, 10.5, "brick_light", "roof_rust", floors=2, bands=True)
    add_building("South_Dormitory_B", 500.0, -284.0, 72.0, 18.0, 7.5, 10.5, "blue", "roof", floors=2, bands=True)
    add_building("South_Service_Block", 580.0, -349.0, 48.0, 17.0, 5.8, 8.0, "concrete", "roof", floors=2, bands=False)
    add_building("East_Sports_Hall", 528.0, -170.0, 54.0, 27.0, 10.5, 12.0, "blue", "roof", floors=2, bands=False)


def add_fine_anchor_features():
    """Small site-specific masses taken from the measured color/height plan."""
    # North green court inside the upper teaching cluster.
    add_prism("North_Green_Court", [(305, -53), (394, -53), (394, -5), (305, -5)], 20.6, 21.0, "grass_light", "Platforms", "north courtyard lawn")
    for i, (x, z) in enumerate(((309, -49), (390, -49), (309, -9), (390, -9))):
        add_box(f"North_Court_Planter_{i+1}", (x, 21.8, z), (3.2, 1.6, 3.2), "concrete", "Details", "courtyard planter")
    add_box("North_Court_Walk_North", (349.5, 21.25, -2.5), (93.0, 0.28, 4.0), "paving_light", "Platforms", "courtyard walk")
    add_box("North_Court_Walk_South", (349.5, 21.25, -55.5), (93.0, 0.28, 4.0), "paving_light", "Platforms", "courtyard walk")

    # The central source plan contains a sequence of differently colored
    # elevated galleries around the main pedestrian axis.
    add_prism("Central_Red_Gallery", [(259, -303), (293, -303), (319, -276), (301, -247), (266, -254)], 16.1, 16.75, "track_red", "Platforms", "central colored gallery")
    add_prism("Central_Yellow_Gallery", [(333, -229), (345, -229), (371, -191), (362, -181), (350, -197)], 25.8, 26.45, "source_yellow", "Platforms", "central colored gallery")
    add_prism("Central_Cyan_Atrium", [(332, -228), (373, -228), (442, -185), (431, -151), (350, -171)], 30.5, 31.1, "source_cyan", "Platforms", "elevated atrium deck")
    # The cyan deck is elevated rather than a floating sheet: slender piers,
    # footings and edge rails carry it back to the central terrace.
    for i, (x, z, bottom) in enumerate(((342, -219, 19.0), (365, -219, 19.0), (424, -180, 22.0), (416, -158, 24.0), (356, -176, 20.5))):
        add_cylinder(f"Cyan_Atrium_Pier_{i+1}", (x, (bottom + 30.5) * 0.5, z), 0.48, 30.5 - bottom, "steel", "Bridges", "elevated atrium support", sides=10)
        add_box(f"Cyan_Atrium_Footing_{i+1}", (x, bottom + 0.18, z), (2.4, 0.36, 2.4), "concrete", "Bridges", "elevated atrium footing")
    platform_edge_rail("Cyan_Atrium_West_Rail", (332, -228), (373, -228), 31.1, "steel")
    platform_edge_rail("Cyan_Atrium_East_Rail", (442, -185), (431, -151), 31.1, "steel")
    add_prism("East_Rose_Garden", [(387, -273), (431, -273), (437, -224), (411, -185), (386, -194)], 23.7, 24.1, "source_rose", "Platforms", "east garden terrace")
    add_box("Central_Red_Pavilion", (281, 19.0, -229), (21.0, 5.5, 13.0), "source_orange", "Buildings", "small pavilion")
    add_box("Central_Red_Pavilion_Roof", (281, 22.0, -229), (23.0, 0.7, 15.0), "roof_rust", "Buildings", "small pavilion roof")

    # Round landmark and light-blue concourse on the east upper platform.
    add_cylinder("East_Rotunda", (431, 30.0, -161), 8.5, 12.0, "source_cyan", "Buildings", "circular campus landmark", sides=24)
    add_cylinder("East_Rotunda_Roof", (431, 36.2, -161), 10.0, 0.8, "source_yellow", "Buildings", "circular roof", sides=24)
    add_uv_dome("East_Rotunda_Dome", (431, 36.55, -161), 8.7, "glass", "Details", "circular glazed roof", rings=4, segments=16)
    add_box("East_Rotunda_Entry", (431, 24.4, -171), (8.0, 2.4, 3.0), "glass", "Details", "circular landmark entry")

    # Additional long service/residence wings complete the eastern envelope
    # visible in the source plan beyond the main south dormitory pair.
    add_building("South_Dormitory_C", 577.0, -350.0, 58.0, 14.0, 6.2, 9.0, "source_orange", "roof_rust", floors=2, bands=False)
    add_building("South_Dormitory_D", 577.0, -302.0, 58.0, 14.0, 6.5, 9.0, "cream", "roof", floors=2, bands=False)
    add_building("East_Service_Wing", 610.0, -244.0, 38.0, 13.0, 7.4, 8.0, "source_orange", "roof_rust", floors=2, bands=False)


def add_oval_disc(name, cx, cz, rx, rz, y, thickness, material, collection_name, role, segments=64):
    footprint = [(cx + rx * cos(2 * pi * i / segments), cz + rz * sin(2 * pi * i / segments)) for i in range(segments)]
    return add_prism(name, footprint, y - thickness, y, material, collection_name, role)


def add_oval_ring(name, cx, cz, outer_rx, outer_rz, inner_rx, inner_rz, y, thickness, material, collection_name, role, segments=64):
    verts = []
    for yy in (y - thickness, y):
        for rx, rz in ((outer_rx, outer_rz), (inner_rx, inner_rz)):
            for i in range(segments):
                a = 2 * pi * i / segments
                verts.append((cx + rx * cos(a), yy, cz + rz * sin(a)))
    # ring loops: bottom outer=0, bottom inner=S, top outer=2S, top inner=3S
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces += [
            (i, j, segments + j, segments + i),
            (2 * segments + i, 3 * segments + i, 3 * segments + j, 2 * segments + j),
            (i, 2 * segments + i, 2 * segments + j, j),
            (segments + i, segments + j, 3 * segments + j, 3 * segments + i),
        ]
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_field(name, cx, cz, width, depth, y, material, collection_name="Sports", line_material="line", angle=0.0):
    add_box(name, (cx, y, cz), (width, 0.28, depth), material, collection_name, "sports field", angle)
    add_box(f"{name}_CenterLine", (cx, y + 0.16, cz), (width - 1.2, 0.04, 0.18), line_material, collection_name, "field marking", angle)
    add_box(f"{name}_MidLine", (cx, y + 0.16, cz), (0.18, 0.04, depth - 1.2), line_material, collection_name, "field marking", angle)
    for side in (-1, 1):
        add_box(f"{name}_EndLine_{side}", (cx + side * (width * 0.5 - 0.7), y + 0.16, cz), (0.12, 0.04, depth - 1.2), line_material, collection_name, "field marking", angle)


def add_sports():
    # The measured large red plate becomes the west oval athletics precinct.
    cx, cz, y = 142.0, -149.0, 5.8
    add_oval_ring("West_Athletics_Track", cx, cz, 53.0, 85.5, 45.0, 77.0, y, 0.38, "track_red", "Sports", "athletics track")
    add_oval_ring("West_Athletics_Lane_1", cx, cz, 50.2, 82.7, 48.0, 80.5, y + 0.04, 0.05, "track_lane", "Sports", "track lane")
    for lane in range(2, 5):
        outer_rx = 48.0 - (lane - 2) * 2.05
        outer_rz = 80.5 - (lane - 2) * 2.35
        inner_rx = outer_rx - 0.85
        inner_rz = outer_rz - 0.85
        add_oval_ring(f"West_Athletics_Lane_{lane}", cx, cz, outer_rx, outer_rz, inner_rx, inner_rz, y + 0.07, 0.045, "track_lane", "Sports", "track lane")
    add_oval_disc("West_Athletics_Field", cx, cz, 44.0, 76.0, y + 0.05, 0.12, "grass", "Sports", "athletics infield")
    add_field("West_Soccer_Pitch", cx, cz, 62.0, 103.0, y + 0.20, "grass_light", "Sports", angle=0.0)
    # Stands read as low terraces against the long oval edges.
    add_box("West_Stand_West", (91.0, 9.0, -149.0), (5.0, 6.0, 83.0), "concrete", "Sports", "athletics stand")
    add_box("West_Stand_East", (193.0, 9.0, -149.0), (5.0, 6.0, 83.0), "concrete", "Sports", "athletics stand")
    for i, zz in enumerate((-190, -165, -140, -115)):
        add_box(f"West_Stand_Tier_{i+1}", (91.2, 11.0 + i * 0.65, zz), (4.6, 0.42, 15.0), "paving_light", "Sports", "athletics stand tier")
    add_box("West_Scoreboard", (96.0, 15.0, -63.0), (2.5, 14.0, 18.0), "roof", "Sports", "scoreboard")
    add_box("West_Scoreboard_Face", (94.6, 15.0, -63.0), (0.12, 9.0, 15.0), "blue_light", "Sports", "scoreboard face")
    for i, (x, z) in enumerate(((98, -71), (186, -71), (98, -227), (186, -227))):
        add_cylinder(f"West_Floodlight_{i+1}_Mast", (x, 15.0, z), 0.16, 20.0, "steel", "Sports", "stadium floodlight", sides=8)
        add_box(f"West_Floodlight_{i+1}_Bar", (x, 25.0, z), (3.0, 0.3, 0.35), "white", "Sports", "stadium floodlight")

    # The south cyan/tan plates become a rectangular field and courts.
    add_box("South_Main_Grass_Field", (315.5, 9.7, -324.5), (64.0, 0.35, 53.0), "grass", "Sports", "main sports field")
    add_field("South_Football_Field", 315.5, -324.5, 58.0, 46.0, 9.95, "grass_light", "Sports")
    add_box("South_Field_Surround", (315.5, 9.45, -324.5), (69.5, 0.25, 58.5), "paving", "Sports", "sports surround")
    for side in (-1, 1):
        gz = -324.5 + side * 21.2
        add_cylinder_between(f"South_Goal_{side}_Crossbar", (289.0, 12.0, gz), (292.8, 12.0, gz), 0.07, "white", "Sports", "football goal")
        add_cylinder_between(f"South_Goal_{side}_Post_L", (289.0, 9.9, gz), (289.0, 12.0, gz), 0.07, "white", "Sports", "football goal")
        add_cylinder_between(f"South_Goal_{side}_Post_R", (292.8, 9.9, gz), (292.8, 12.0, gz), 0.07, "white", "Sports", "football goal")
    # Courts are grouped near the south gym.
    for i, (x, z, mat_name) in enumerate(((369, -319, "court_blue"), (409, -319, "court_green"), (449, -319, "court_red"), (369, -367, "court_green"), (409, -367, "court_blue"))):
        add_box(f"South_Court_{i+1}", (x, 9.9, z), (31.0, 0.28, 23.0), mat_name, "Sports", "court surface")
        add_box(f"South_Court_{i+1}_Mid_X", (x, 10.08, z), (29.0, 0.05, 0.15), "white", "Sports", "court line")
        add_box(f"South_Court_{i+1}_Mid_Z", (x, 10.08, z), (0.15, 0.05, 21.0), "white", "Sports", "court line")
        add_cylinder_between(f"South_Court_{i+1}_Net", (x, 11.0, z - 11.0), (x, 11.0, z + 11.0), 0.045, "white", "Sports", "court net")
    add_box("South_Grandstand", (350, 13.5, -293.0), (66.0, 7.0, 5.0), "concrete", "Sports", "sports grandstand")
    for i in range(5):
        add_box(f"South_Grandstand_Tier_{i+1}", (350, 17.0 + i * 0.7, -295.0 - i * 0.9), (58 - i * 4, 0.45, 2.2), "paving_light", "Sports", "grandstand tier")


def bridge_box(name, p1, p2, width, thickness, material="concrete"):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    dx, dz = x2 - x1, z2 - z1
    length = max(0.01, sqrt(dx * dx + dz * dz))
    nx, nz = -dz / length * width * 0.5, dx / length * width * 0.5
    b = thickness * 0.5
    verts = [
        (x1 + nx, y1 - b, z1 + nz),
        (x1 - nx, y1 - b, z1 - nz),
        (x1 - nx, y1 + b, z1 - nz),
        (x1 + nx, y1 + b, z1 + nz),
        (x2 + nx, y2 - b, z2 + nz),
        (x2 - nx, y2 - b, z2 - nz),
        (x2 - nx, y2 + b, z2 - nz),
        (x2 + nx, y2 + b, z2 + nz),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (3, 2, 6, 7), (0, 3, 7, 4), (1, 5, 6, 2)]
    obj = mesh_object(name, verts, faces, material, "Bridges", "inter-building bridge")
    # Independent railings are deliberately separate from the bridge deck.
    for side in (-1, 1):
        sx, sz = (x1 + nx * side * 2.0, z1 + nz * side * 2.0)
        ex, ez = (x2 + nx * side * 2.0, z2 + nz * side * 2.0)
        rail_y1, rail_y2 = y1 + 1.55, y2 + 1.55
        add_cylinder_between(f"{name}_Rail_{side}_Top", (sx, rail_y1, sz), (ex, rail_y2, ez), 0.08, "steel", "Bridges", "bridge handrail")
        steps = max(1, int(length / 6.0))
        for i in range(steps + 1):
            t = i / steps
            px, pz = sx + (ex - sx) * t, sz + (ez - sz) * t
            py = rail_y1 + (rail_y2 - rail_y1) * t
            add_cylinder(f"{name}_RailPost_{side}_{i:02d}", (px, py - 0.68, pz), 0.055, 1.5, "steel", "Bridges", "bridge rail post")
    return obj


def add_cylinder_between(name, p1, p2, radius, material, collection_name, role):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    length = sqrt(vx * vx + vy * vy + vz * vz)
    # A cylinder aligned to an arbitrary vector is most robustly made as a
    # polygonal prism directly in a local orthonormal frame.
    if length < 1e-5:
        return add_cylinder(name, p1, radius, 0.1, material, collection_name, role)
    ux, uy, uz = vx / length, vy / length, vz / length
    ax, ay, az = (0.0, 1.0, 0.0) if abs(uy) < 0.88 else (1.0, 0.0, 0.0)
    # cross product u x a
    nx, ny, nz = uy * az - uz * ay, uz * ax - ux * az, ux * ay - uy * ax
    nl = sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    bx, by, bz = uy * nz - uz * ny, uz * nx - ux * nz, ux * ny - uy * nx
    sides = 8
    verts = []
    for p in (p1, p2):
        for i in range(sides):
            a = 2 * pi * i / sides
            ca, sa = cos(a), sin(a)
            verts.append((p[0] + radius * (nx * ca + bx * sa), p[1] + radius * (ny * ca + by * sa), p[2] + radius * (nz * ca + bz * sa)))
    faces = [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((i, j, sides + j, sides + i))
    return mesh_object(name, verts, faces, material, collection_name, role)


def add_bridges():
    bridge_box("Bridge_West_to_Central", (278, 18.0, -239), (303, 22.0, -239), 5.2, 0.75, "concrete")
    bridge_box("Bridge_Central_to_East", (369, 25.0, -238), (391, 27.6, -238), 5.5, 0.8, "concrete")
    bridge_box("Bridge_East_North", (411, 30.5, -224), (411, 31.6, -188), 5.0, 0.72, "paving_light")
    bridge_box("Bridge_North_Research", (352, 34.5, -150), (382, 35.5, -139), 5.0, 0.7, "concrete")
    bridge_box("Bridge_South_Link", (347, 14.0, -296), (378, 20.0, -265), 5.0, 0.72, "paving_light")
    bridge_box("Bridge_East_Forum", (429, 28.0, -205), (454, 25.5, -205), 4.5, 0.7, "concrete")


def platform_edge_rail(name, p1, p2, y, material="steel"):
    x1, z1 = p1
    x2, z2 = p2
    dx, dz = x2 - x1, z2 - z1
    length = max(0.01, sqrt(dx * dx + dz * dz))
    nx, nz = -dz / length, dx / length
    add_cylinder_between(f"{name}_TopRail", (x1, y + 1.35, z1), (x2, y + 1.35, z2), 0.065, material, "Details", "platform handrail")
    count = max(1, int(length / 5.0))
    for i in range(count + 1):
        t = i / count
        px, pz = x1 + dx * t, z1 + dz * t
        add_cylinder(f"{name}_Post_{i:02d}", (px, y + 0.65, pz), 0.055, 1.35, material, "Details", "platform rail post", sides=8)
    # A second low guard rail is common around the elevated public decks.
    add_cylinder_between(f"{name}_MidRail", (x1, y + 0.63, z1), (x2, y + 0.63, z2), 0.04, material, "Details", "platform guard rail")


def add_public_realm_details():
    # Glass/steel guardrails outline the steep public decks independently of
    # the slabs, so the connection topology remains easy to inspect.
    platform_edge_rail("Upper_Terrace_North_Rail", (310, -113), (414, -113), 30.1, "steel")
    platform_edge_rail("Upper_Terrace_East_Rail", (426, -114), (426, -180), 30.1, "steel")
    platform_edge_rail("East_Terrace_South_Rail", (381, -211), (443, -215), 23.3, "steel")
    platform_edge_rail("Central_Terrace_West_Rail", (273, -241), (277, -298), 18.8, "steel")
    platform_edge_rail("West_Courtyard_East_Rail", (291, -219), (286, -284), 13.0, "steel")
    # Benches, planters and bollards animate the central pedestrian route.
    for i, (x, z, a) in enumerate(((307, -283, 0.0), (330, -248, 0.4), (353, -201, -0.3), (383, -171, 0.2), (299, -317, 0.0))):
        add_box(f"Plaza_Bench_{i+1:02d}_Seat", (x, terrain_height(x, z) + 0.8, z), (4.2, 0.35, 0.62), "wood" if "wood" in MATS else "roof_rust", "Details", "plaza bench", angle=a)
        add_box(f"Plaza_Bench_{i+1:02d}_Back", (x, terrain_height(x, z) + 1.6, z - 0.28), (4.2, 1.2, 0.18), "roof_rust", "Details", "plaza bench back", angle=a)
    for i, (x, z) in enumerate(((268, -333), (278, -316), (293, -290), (311, -264), (329, -238), (347, -208), (363, -177), (380, -148))):
        add_cylinder(f"Spine_Bollard_{i+1:02d}", (x, terrain_height(x, z) + 0.55, z), 0.16, 1.1, "steel", "Details", "pedestrian bollard", sides=8)
    # A low perimeter fence and gates define the south sports courts.
    for i, (x, z) in enumerate(((354, -387), (454, -387), (470, -353), (470, -289))):
        add_cylinder(f"Court_Fence_Post_{i+1:02d}", (x, 12.0, z), 0.07, 4.0, "steel", "Sports", "sports fence post", sides=8)
    add_cylinder_between("Court_Fence_South", (354, 13.8, -387), (470, 13.8, -387), 0.055, "steel", "Sports", "sports fence rail")
    add_cylinder_between("Court_Fence_East", (470, 13.8, -387), (470, 13.8, -289), 0.055, "steel", "Sports", "sports fence rail")


def add_stairs(name, x, z, width, run, lower_y, upper_y, angle=0.0):
    count = max(2, int(abs(upper_y - lower_y) / 0.65))
    for i in range(count):
        t = (i + 1) / count
        yy = lower_y + (upper_y - lower_y) * t
        zz_local = -run * 0.5 + run * (i + 0.5) / count
        ox, oz = rotate_xz(0.0, zz_local, angle)
        add_box(f"{name}_Step_{i+1:02d}", (x + ox, yy, z + oz), (width, 0.30, run / count + 0.18), "paving_light", "Stairs", "terraced stair", angle=angle)


def add_stairs_and_ramps():
    add_stairs("West_Courtyard_Stair", 285, -250, 10.0, 18.0, 13.0, 19.0, angle=0.0)
    add_stairs("Central_Library_Stair", 333, -218, 13.0, 17.0, 18.8, 26.0, angle=-0.15)
    add_stairs("East_Complex_Stair", 380, -267, 9.0, 21.0, 23.3, 30.0, angle=0.0)
    add_stairs("North_Terrace_Stair", 303, -111, 12.0, 18.0, 30.1, 35.0, angle=0.0)
    add_stairs("South_Sports_Ramp", 281, -288, 9.0, 20.0, 9.5, 15.0, angle=0.2)
    add_corridor("Library_Access_Ramp", [(292, -303), (299, -288), (308, -275)], 5.0, 17.0, "paving_light", "Stairs", "accessible ramp")


def add_tree(name, x, z, base_y=None, scale=1.0, light=False):
    y = terrain_height(x, z) + 0.2 if base_y is None else base_y
    add_cylinder(f"{name}_Trunk", (x, y + 2.1 * scale, z), 0.42 * scale, 4.2 * scale, "trunk", "Details", "tree trunk", sides=8)
    add_uv_dome(f"{name}_Canopy", (x, y + 5.1 * scale, z), 3.5 * scale, "canopy_light" if light else "canopy", "Details", "tree canopy", rings=4, segments=9)


def add_landscape_details():
    tree_points = [
        (28, -392), (63, -350), (74, -300), (57, -226), (71, -160), (64, -91),
        (218, -393), (244, -383), (268, -378), (290, -385), (445, -393), (494, -389),
        (575, -386), (630, -369), (646, -315), (638, -260), (646, -176), (642, -96),
        (221, -196), (214, -126), (219, -71), (279, -91), (292, -69), (442, -106),
        (475, -144), (504, -200), (472, -252), (547, -254), (568, -298),
    ]
    for i, (x, z) in enumerate(tree_points):
        add_tree(f"Campus_Tree_{i+1:02d}", x, z, scale=0.72 + (i % 3) * 0.14, light=(i % 4 == 0))
    # Simple light poles trace the central pedestrian spine.
    for i, (x, z, y) in enumerate(((268, -310, 15), (294, -273, 18), (326, -229, 21), (349, -183, 25), (374, -139, 30), (398, -98, 30))):
        add_cylinder(f"Spine_Light_{i+1:02d}_Pole", (x, y + 2.0, z), 0.10, 4.0, "steel", "Details", "path light", sides=8)
        add_uv_dome(f"Spine_Light_{i+1:02d}_Lamp", (x, y + 4.1, z), 0.32, "white", "Details", "path light", rings=3, segments=8)
    # A water court reinforces the central plaza topology.
    add_box("Central_Water_Court", (332, 19.15, -296), (25, 0.28, 10), "water", "Details", "water court")
    for i in range(4):
        add_box(f"Water_Court_Edge_{i+1}", (332 + (-1 if i < 2 else 1) * (13.2 if i % 2 == 0 else 0), 19.4, -296 + (-1 if i % 2 == 0 else 1) * 5.4), (26 if i < 2 else 0.35, 0.25, 0.35 if i < 2 else 11), "paving_light", "Details", "water court edge")
    # Campus gate marker at the south approach.
    add_box("South_Gate_Pylon_L", (240, 10.0, -399), (3.0, 15.0, 3.0), "brick", "Details", "campus gate")
    add_box("South_Gate_Pylon_R", (284, 10.0, -399), (3.0, 15.0, 3.0), "brick", "Details", "campus gate")
    add_box("South_Gate_Beam", (262, 17.0, -399), (48.0, 3.0, 3.0), "steel", "Details", "campus gate")


def look_at(camera, target):
    from mathutils import Vector

    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def add_cameras_and_lights():
    scene = bpy.context.scene
    # Workbench is used for deterministic QA renders on the headless portable
    # Blender runtime; the saved model remains ordinary editable mesh data.
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = False
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.5
    scene.display.shading.curvature_valley_factor = 1.0
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 820
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world = bpy.data.worlds.new("Campus_World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.028, 0.040, 0.055, 1.0)
        bg.inputs["Strength"].default_value = 0.28
    # Sun and broad fill keep the low-poly massing legible.
    sun_data = bpy.data.lights.new("Campus_Sun", "SUN")
    sun_data.energy = 3.2
    sun_data.angle = 0.25
    sun = bpy.data.objects.new("Campus_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (0.58, -0.72, -0.45)
    area_data = bpy.data.lights.new("Campus_Fill", "AREA")
    area_data.energy = 1800
    area_data.shape = "DISK"
    area_data.size = 260
    area = bpy.data.objects.new("Campus_Fill", area_data)
    scene.collection.objects.link(area)
    area.location = (270, 250, -220)
    look_at(area, (300, 10, -220))
    # Camera 1: plan view for QA and topology.
    cam_data = bpy.data.cameras.new("Campus_Top_Camera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 475.0
    cam = bpy.data.objects.new("Campus_Top_Camera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (340, 470, -204)
    look_at(cam, (330, 7, -204))
    scene.camera = cam
    cam["view_purpose"] = "campus topology / plan QA"
    scene.render.filepath = str(QA_DIR / "recreated_top.png")
    bpy.ops.render.render(write_still=True)
    # Camera 2: oblique view that shows terraces, bridges and sports precinct.
    ob_data = bpy.data.cameras.new("Campus_Oblique_Camera")
    ob_data.type = "ORTHO"
    ob_data.ortho_scale = 520.0
    ob = bpy.data.objects.new("Campus_Oblique_Camera", ob_data)
    scene.collection.objects.link(ob)
    ob.location = (760, 330, 210)
    look_at(ob, (325, 13, -205))
    ob["view_purpose"] = "campus massing / bridge QA"
    scene.camera = ob
    scene.render.filepath = str(QA_DIR / "recreated_oblique.png")
    bpy.ops.render.render(write_still=True)
    # Restore the plan camera as the active view in the saved file.
    scene.camera = cam


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene["model_type"] = "new campus reconstruction"
    scene["reference_policy"] = "locked source and supplied reference images; source geometry not copied"
    scene["reconstruction_method"] = "procedural semantic massing with measured anchors"
    setup_materials()
    setup_collections()
    add_terrain()
    add_roads_and_plazas()
    add_buildings()
    add_fine_anchor_features()
    add_sports()
    add_bridges()
    add_stairs_and_ramps()
    add_public_realm_details()
    add_landscape_details()
    add_cameras_and_lights()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    print(f"SAVED {OUT}")
    print(f"OBJECTS {len(bpy.data.objects)} COLLECTIONS {len(bpy.data.collections)} MATERIALS {len(bpy.data.materials)}")


if __name__ == "__main__":
    main()
