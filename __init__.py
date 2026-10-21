bl_info = {
    "name": "Propeller Generator",
    "author": "oLV - Olivier LAVAUD",
    "version": (1, 0, 2),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Propeller",
    "description": "Génère des hélices paramétriques NACA 4 chiffres",
    "category": "Add Mesh",
}

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ============================================================
# PRESETS
# ============================================================

PRESETS = {
    "rc_plane": {
        "blades": 3, "diameter": 120.0, "root_diameter": 10.0, "root_height": 12.0,
        "pitch": -1.0, "chord_mode": "ellipse", "chord_fraction": 0.15,
        "ellipse_length": 1.1, "centerline": 0.3, "fairing": 4.0, "sweep": 0.0,
        "pitch_tip": -1.0, "naca_root": 9430, "naca_mid": 6412, "naca_tip": 4412,
        "transition_point": 0.33, "trailing_thickness": 0.4,
        "spinner_type": "ogive", "spinner_on_hub": True,
        "spinner_diameter": 10.0, "spinner_length": 8.0, "spinner_rounding": 0.5,
        "shroud": False, "shaft_type": "cylinder", "shaft_diameter": 5.0,
    },
    "rb_plane": {
        "blades": 2, "diameter": 80.0, "root_diameter": 3.0, "root_height": 6.0,
        "pitch": 70.0, "chord_mode": "ellipse", "chord_fraction": 0.50,
        "ellipse_length": 1.0, "centerline": 0.5, "fairing": 0.0, "sweep": 0.0,
        "pitch_tip": -1.0, "naca_root": 4410, "naca_mid": 3410, "naca_tip": 2410,
        "transition_point": 0.25, "trailing_thickness": 0.3,
        "spinner_type": "none", "shroud": False,
        "shaft_type": "cylinder", "shaft_diameter": 1.5,
    },
    "airplane": {
        "blades": 3, "diameter": 150.0, "root_diameter": 12.0, "root_height": 10.0,
        "pitch": 100.0, "chord_mode": "ellipse", "chord_fraction": 0.15,
        "ellipse_length": 1.1, "centerline": 0.3, "fairing": 2.0, "sweep": 0.0,
        "pitch_tip": -1.0, "naca_root": 6412, "naca_mid": 4412, "naca_tip": 2412,
        "transition_point": 0.33, "trailing_thickness": 0.4,
        "spinner_type": "ogive", "spinner_on_hub": True,
        "spinner_diameter": 12.0, "spinner_length": 10.0, "spinner_rounding": 0.5,
        "shroud": False, "shaft_type": "cylinder", "shaft_diameter": 6.0,
    },
    "pc_fan": {
        "blades": 7, "diameter": 120.0, "root_diameter": 40.0, "root_height": 10.0,
        "pitch": 40.0, "chord_mode": "ellipse", "chord_fraction": 0.28,
        "ellipse_length": 1.8, "centerline": 0.7, "fairing": 0.0, "sweep": -0.25,
        "pitch_tip": 30.0, "naca_root": 12, "naca_mid": 12, "naca_tip": 10,
        "transition_point": 0.30, "trailing_thickness": 0.3,
        "spinner_type": "none", "shroud": False,
        "shaft_type": "cylinder", "shaft_diameter": 8.0,
    },
    "toy_boat": {
        "blades": 3, "diameter": 80.0, "root_diameter": 12.0, "root_height": 24.0,
        "pitch": 60.0, "chord_mode": "ellipse", "chord_fraction": 0.70,
        "ellipse_length": 1.0, "centerline": 0.5, "fairing": 0.0, "sweep": 1.0,
        "pitch_tip": -1.0, "naca_root": 6410, "naca_mid": 4410, "naca_tip": 2410,
        "transition_point": 0.40, "trailing_thickness": 0.4,
        "spinner_type": "none", "shroud": False,
        "shaft_type": "cylinder", "shaft_diameter": 5.0,
    },
    "pullcopter": {
        "blades": 3, "diameter": 160.0, "root_diameter": 16.0, "root_height": 6.0,
        "pitch": 160.0, "chord_mode": "ellipse", "chord_fraction": 0.20,
        "ellipse_length": 1.2, "centerline": 1.0, "fairing": 4.0, "sweep": -0.25,
        "pitch_tip": -1.0, "naca_root": 9440, "naca_mid": 6412, "naca_tip": 3412,
        "transition_point": 0.33, "trailing_thickness": 0.4,
        "spinner_type": "ogive", "spinner_on_hub": True,
        "spinner_diameter": 18.0, "spinner_length": 10.0, "spinner_rounding": 0.5,
        "shroud": True, "shroud_offset": -0.5, "shroud_wall": 2.0,
        "shroud_length": 10.0, "shroud_chamfer": 0.4,
        "shaft_type": "cylinder", "shaft_diameter": 6.0,
    },
}

# ============================================================
# PARAMÈTRES GLOBAUX
# ============================================================

class PropellerProperties(bpy.types.PropertyGroup):
    # Propeller
    blades: bpy.props.IntProperty(name="Blades", default=3, min=1, max=12)
    diameter: bpy.props.FloatProperty(name="Diameter (mm)", default=150.0, min=10.0)
    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[("CW", "Clockwise", ""), ("CCW", "Counterclockwise", "")],
        default="CCW"
    )
    root_diameter: bpy.props.FloatProperty(name="Root Diameter (mm)", default=14.0, min=2.0)
    root_height: bpy.props.FloatProperty(name="Root Height (mm)", default=8.0, min=1.0)
    pitch: bpy.props.FloatProperty(name="Pitch (mm/rev, -1=auto)", default=-1.0)

    # Blade
    chord_mode: bpy.props.EnumProperty(
        name="Chord Mode",
        items=[("ellipse", "Ellipse", ""), ("linear", "Linear", ""), ("constant", "Constant", "")],
        default="ellipse"
    )
    chord_fraction: bpy.props.FloatProperty(name="Chord Fraction", default=0.15, min=0.05, max=0.8)
    ellipse_length: bpy.props.FloatProperty(name="Ellipse Length", default=1.1, min=1.0, max=2.5)
    centerline: bpy.props.FloatProperty(name="Centerline", default=1.0, min=0.0, max=1.0)
    fairing: bpy.props.FloatProperty(name="Fairing (mm)", default=3.0, min=0.0)
    sweep: bpy.props.FloatProperty(name="Sweep (deg/mm)", default=0.0)
    offset: bpy.props.FloatProperty(name="Offset (mm)", default=0.0)
    pitch_tip: bpy.props.FloatProperty(name="Pitch Tip (-1=same)", default=-1.0)

    # Airfoils
    naca_root: bpy.props.IntProperty(name="NACA Root", default=8430, min=0, max=9999)
    naca_mid: bpy.props.IntProperty(name="NACA Mid", default=6412, min=0, max=9999)
    naca_tip: bpy.props.IntProperty(name="NACA Tip", default=3412, min=0, max=9999)
    transition_point: bpy.props.FloatProperty(name="Transition Point", default=0.33, min=0.0, max=1.0)
    trailing_thickness: bpy.props.FloatProperty(name="Trailing Thickness (mm)", default=0.4, min=0.0)

    # Hub
    hub_extend: bpy.props.FloatProperty(name="Hub Extend (mm)", default=2.0, min=0.0)
    shaft_type: bpy.props.EnumProperty(
        name="Shaft Type",
        items=[("none", "None", ""), ("cylinder", "Cylinder", ""),
               ("keyway", "Keyway", ""), ("hex", "Hex", ""), ("D", "D-Shape", "")],
        default="cylinder"
    )
    shaft_diameter: bpy.props.FloatProperty(name="Shaft Diameter (mm)", default=5.0, min=0.5)
    shaft_depth: bpy.props.FloatProperty(name="Shaft Depth (-1=auto)", default=-1.0)
    shaft_chamfer: bpy.props.FloatProperty(name="Shaft Chamfer (mm)", default=0.4, min=0.0)
    keyway_size: bpy.props.FloatVectorProperty(
        name="Keyway Size Override [W,H]", size=2, default=(0.0, 0.0), min=0.0)

    # Spinner
    spinner_type: bpy.props.EnumProperty(
        name="Spinner",
        items=[("none", "None", ""), ("ogive", "Ogive", ""), ("parabolic", "Parabolic", "")],
        default="none"
    )
    spinner_on_hub: bpy.props.BoolProperty(name="Spinner On Hub", default=True)
    spinner_diameter: bpy.props.FloatProperty(name="Spinner Diameter (mm)", default=20.0, min=1.0)
    spinner_length: bpy.props.FloatProperty(name="Spinner Length (mm)", default=20.0, min=1.0)
    spinner_rounding: bpy.props.FloatProperty(name="Spinner Rounding", default=0.5, min=0.0, max=1.0)

    # Shroud
    shroud: bpy.props.BoolProperty(name="Shroud", default=False)
    shroud_offset: bpy.props.FloatProperty(
        name="Shroud Offset (mm)", default=2.0, min=-2.0, soft_min=0.0,
        description="Jeu radial entre la pointe des pales et le carénage"
                    " (négatif = recouvrement, pales soudées à l'anneau)")
    shroud_wall: bpy.props.FloatProperty(name="Shroud Wall (mm)", default=1.8, min=0.2)
    shroud_length: bpy.props.FloatProperty(name="Shroud Length (mm)", default=10.0, min=1.0)
    shroud_chamfer: bpy.props.FloatProperty(name="Shroud Chamfer (mm)", default=0.4, min=0.0)

    # Render / output
    points: bpy.props.IntProperty(name="Points (0=auto)", default=0, min=0)
    slices: bpy.props.IntProperty(name="Slices (0=auto)", default=0, min=0)
    color: bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR', size=3, default=(0.88, 0.88, 0.88),
        min=0.0, max=1.0)
    z_up: bpy.props.BoolProperty(
        name="Orient Z-up (Blender-native)", default=True,
        description="Oriente l'hélice selon Z (au lieu de Y)")
    scale: bpy.props.FloatProperty(
        name="Scale", default=0.001, min=1e-6, soft_max=1.0,
        description="Échelle appliquée après génération (0.001 = mm vers mètres)")
    ground: bpy.props.BoolProperty(
        name="Place on Ground", default=True,
        description="Déplace le maillage pour que son point le plus bas soit à Z=0")
    shade_smooth: bpy.props.BoolProperty(name="Smooth Shading", default=True)
    uv_unwrap: bpy.props.BoolProperty(name="UV Unwrap", default=True)


# ============================================================
# FONCTIONS MATHÉMATIQUES
# ============================================================

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def lerp(a, b, t):
    return a + (b - a) * t

def naca_params(code):
    code = int(code)
    return (0.01 * (code // 1000),
            0.1 * ((code // 100) % 10),
            0.01 * (code % 100))

def naca_camber(x, m, p):
    if m == 0:
        return 0.0
    pc = clamp(p, 1e-6, 1 - 1e-6)
    a = 2 * pc * x - x * x
    if x < pc:
        return m * a / (pc * pc)
    return m * (1 - 2 * pc + a) / ((1 - pc) * (1 - pc))

def naca_gradient(x, m, p):
    if m == 0:
        return 0.0
    pc = clamp(p, 1e-6, 1 - 1e-6)
    denom = (pc if x < pc else (1 - pc)) ** 2
    return (2 * m * (pc - x)) / denom

def naca_thickness(x, t):
    a0, a1, a2, a3, a4 = 0.2969, -0.126, -0.3516, 0.2843, -0.1036
    x2 = x * x
    return 5 * t * (a0 * math.sqrt(x) + a1 * x + a2 * x2 + a3 * x2 * x + a4 * x2 * x2)

def naca_surface(x, m, p, t, chordlen=1.0, origin=0.0, direction=1, te_thick=0.2, side=1):
    xp = 0.5 * (1 - math.cos(math.pi * x))
    theta = math.atan(naca_gradient(xp, m, p))
    yc = naca_camber(xp, m, p)
    yt = naca_thickness(xp, t)
    d = -1 if direction < 0 else 1
    org = clamp(origin, 0, 1)
    px = chordlen * d * (xp - side * yt * math.sin(theta) - org)
    py = chordlen * (yc + side * yt * math.cos(theta)) + side * xp * te_thick / 2
    return (px, py)

def naca_profile(n, m, p, t, chordlen=1.0, origin=0.0, direction=1, te_thick=0.2):
    pts = []
    if direction < 0:
        for i in range(n, 0, -1):
            pts.append(naca_surface(i / n, m, p, t, chordlen, origin, direction, te_thick, -1))
        for i in range(0, n):
            pts.append(naca_surface(i / n, m, p, t, chordlen, origin, direction, te_thick, 1))
        pts.append(naca_surface(1.0, m, p, t, chordlen, origin, direction, te_thick, 1))
    else:
        for i in range(n, 0, -1):
            pts.append(naca_surface(i / n, m, p, t, chordlen, origin, direction, te_thick, 1))
        for i in range(0, n):
            pts.append(naca_surface(i / n, m, p, t, chordlen, origin, direction, te_thick, -1))
        pts.append(naca_surface(1.0, m, p, t, chordlen, origin, direction, te_thick, -1))
    return pts

def ellipse_d(majaxis, minaxis, angle):
    a, b = 0.5 * majaxis, 0.5 * minaxis
    bc = b * math.cos(angle)
    as_ = a * math.sin(angle)
    denom = math.sqrt(bc * bc + as_ * as_)
    if denom < 1e-9:
        return 0.0
    return 2 * a * b / denom

def attack_angle_r(r, direction, pitch, tspan, pitch_mode="constant", pitch_tip=None):
    r = max(r, 1e-6)
    pt = pitch if pitch_tip is None else pitch_tip
    p = pitch + (pt - pitch) * tspan if pitch_mode == "linear" else pitch
    return -direction * math.atan(p / (2 * math.pi * r))

def chord_length(z, length, maxchord, hh, attackangle, esemimajor, mode="ellipse"):
    t = clamp(z / length, 0, 1) if length > 1e-9 else 0.0
    if mode == "ellipse":
        # FIX : ratio borné sous 1 pour ne jamais effondrer l'anneau de pointe.
        ratio = clamp(z / esemimajor, 0.0, 0.995) if esemimajor > 1e-9 else 0.0
        c = maxchord * math.sqrt(max(0.0, 1 - ratio * ratio))
    elif mode == "constant":
        c = maxchord
    elif mode == "linear":
        c = lerp(maxchord, maxchord / 2, t)
    else:
        c = maxchord
    c = max(c, maxchord * 0.02)
    return ellipse_d(c, hh, attackangle)

def fairing_thickness(z, fairing, fairthickness):
    if fairing <= 0:
        return 0.0
    return fairthickness * (1 - math.sin(math.radians(90 * min(1, z / fairing))))

def airfoil_section_3d(profile_2d, r, attackangle, sweep):
    """
    X=tangentiel, Y=corde (axe hélice), Z=rayon.
    FIX : section plane (plus d'enroulement de la corde autour de l'axe,
    qui repliait la pale quand la corde était grande devant le rayon).
    Le sweep est une rotation de la section autour de l'axe Y.
    """
    ca, sa = math.cos(attackangle), math.sin(attackangle)
    ang = math.radians(r * sweep)
    cg, sg = math.cos(ang), math.sin(ang)
    pts = []
    for (px, py) in profile_2d:
        rx = ca * px - sa * py
        ry = sa * px + ca * py
        pts.append((rx * cg + r * sg,
                    ry,
                    -rx * sg + r * cg))
    return pts

def keyway_size(diameter):
    if diameter <= 6:   return (2, 1.0)
    if diameter <= 8:   return (2, 1.2)
    if diameter <= 10:  return (3, 1.4)
    if diameter <= 12:  return (3, 1.8)
    if diameter <= 17:  return (4, 2.3)
    if diameter <= 22:  return (5, 2.8)
    if diameter <= 30:  return (6, 3.3)
    if diameter <= 38:  return (8, 3.3)
    if diameter <= 44:  return (10, 4.3)
    if diameter <= 50:  return (12, 4.3)
    if diameter <= 58:  return (14, 4.9)
    if diameter <= 65:  return (16, 5.4)
    if diameter <= 75:  return (18, 6.4)
    if diameter <= 85:  return (20, 6.4)
    if diameter <= 95:  return (22, 7.4)
    if diameter <= 110: return (25, 8.4)
    return (25, 8.4)


# ============================================================
# GÉNÉRATION DE LA PALE
# ============================================================

def _span_samples(total, step):
    """Liste de positions 0..total incluant exactement les extrémités."""
    if total <= 1e-9:
        return [0.0]
    n = max(1, int(math.ceil(total / max(step, 1e-6))))
    return [total * i / n for i in range(n + 1)]

def build_blade_vnf(props):
    rhub = props.root_diameter / 2
    # FIX : la pale démarre à l'intérieur du moyeu (plus de contact tangent).
    root_inset = clamp(props.root_diameter * 0.10, 0.4, 2.0)
    # FIX : la longueur tient compte de l'enfoncement racine, sinon la pointe
    # n'atteint pas le diamètre nominal (défaut de contact avec le carénage).
    r_root = rhub - root_inset
    blength = props.diameter / 2 - r_root
    bpitch = props.pitch if props.pitch >= 0 else blength
    esemimajor = props.ellipse_length * blength
    maxchordlen = 2 * props.chord_fraction * blength
    hh = min(maxchordlen, props.root_height)
    ztrans = blength * props.transition_point
    blen = blength - ztrans

    slicelen = (blength / clamp(props.slices, 2, 400)) if props.slices > 0 else 0.8
    airfoilsegs = props.points if props.points > 0 else clamp(
        round(2 * blength * props.chord_fraction), 8, 80)

    m_root, p_root, t_root = naca_params(props.naca_root)
    m_mid, p_mid, t_mid = naca_params(props.naca_mid)
    m_tip, p_tip, t_tip = naca_params(props.naca_tip)

    dir_sign = 1 if props.direction == "CW" else -1

    shift = props.root_height * (1.0 - props.centerline)

    fairingthick = 0.0
    if props.fairing > 0:
        ang_fair = -dir_sign * math.atan(bpitch / (2 * math.pi * max(rhub, 1e-6)))
        fd = ellipse_d(maxchordlen, hh, ang_fair)
        if fd > 1e-9:
            fairingthick = props.fairing / fd

    sweep = props.sweep * dir_sign
    sections = []

    def add_section(z_span, z_local, is_root):
        # FIX : rayon racine décalé vers l'intérieur du moyeu.
        rz = r_root + z_span
        if is_root:
            interp = math.sin(math.radians(90 * z_local / ztrans)) if ztrans > 1e-9 else 1.0
            thick = lerp(t_root, t_mid, interp) + fairing_thickness(
                z_local, props.fairing, fairingthick)
            cam = lerp(m_root, m_mid, interp)
            campos = lerp(p_root, p_mid, interp)
        else:
            interp = 1 - math.cos(math.radians(90 * z_local / blen)) if blen > 1e-9 else 1.0
            thick = lerp(t_mid, t_tip, interp) + fairing_thickness(
                z_span, props.fairing, fairingthick)
            cam = lerp(m_mid, m_tip, interp)
            campos = lerp(p_mid, p_tip, interp)

        tspan = z_span / blength if blength > 1e-9 else 0.0
        aa = attack_angle_r(
            rz, dir_sign, bpitch, tspan,
            "constant" if props.pitch_tip < 0 else "linear",
            None if props.pitch_tip < 0 else props.pitch_tip)
        clen = chord_length(z_span, blength, maxchordlen, hh, aa,
                            esemimajor, props.chord_mode)
        profile = naca_profile(airfoilsegs, cam, campos, thick, clen,
                               props.centerline, dir_sign, props.trailing_thickness)
        pts = airfoil_section_3d(profile, rz, aa, sweep)
        pts = [(x, y + shift, z) for (x, y, z) in pts]
        sections.append(pts)

    root_spans = _span_samples(ztrans, slicelen) if ztrans > 1e-9 else []
    main_spans = _span_samples(blen, slicelen)
    if ztrans > 1e-9 and len(main_spans) > 1:
        main_spans = main_spans[1:]  # évite la section dupliquée à ztrans

    for z in root_spans:
        add_section(z, z, True)
    for z in main_spans:
        add_section(ztrans + z, z, False)

    if not sections:
        return [], []

    n_ring = len(sections[0])
    vertices = []
    for ring in sections:
        vertices.extend(ring)

    faces = []
    n_sections = len(sections)
    for s in range(n_sections - 1):
        base_a = s * n_ring
        base_b = (s + 1) * n_ring
        for i in range(n_ring):
            j = (i + 1) % n_ring
            faces.append((base_a + i, base_a + j, base_b + j, base_b + i))

    # FIX : bouchons en éventail (triangles) au lieu de ngones non plans.
    first = sections[0]
    root_c = (sum(p[0] for p in first) / n_ring,
              sum(p[1] for p in first) / n_ring,
              sum(p[2] for p in first) / n_ring)
    vertices.append(root_c)
    root_i = len(vertices) - 1
    for i in range(n_ring):
        faces.append((root_i, i, (i + 1) % n_ring))

    last = sections[-1]
    tip_c = (sum(p[0] for p in last) / n_ring,
             sum(p[1] for p in last) / n_ring,
             sum(p[2] for p in last) / n_ring)
    vertices.append(tip_c)
    tip_i = len(vertices) - 1
    last_base = (n_sections - 1) * n_ring
    for i in range(n_ring):
        faces.append((tip_i, last_base + (i + 1) % n_ring, last_base + i))

    return vertices, faces


# ============================================================
# SPINNER — profils 2D → révolution autour de Y
# ============================================================

def profile_to_solid_of_revolution(profile_2d, center_y, n_steps=48):
    n_prof = len(profile_2d)
    verts = []
    for step in range(n_steps):
        a = 2 * math.pi * step / n_steps
        ca, sa = math.cos(a), math.sin(a)
        for (r, h) in profile_2d:
            verts.append((r * ca, center_y + h, r * sa))

    faces = []
    for step in range(n_steps):
        s2 = (step + 1) % n_steps
        base1 = step * n_prof
        base2 = s2 * n_prof
        for i in range(n_prof - 1):
            faces.append((base1 + i, base1 + i + 1,
                          base2 + i + 1, base2 + i))
    return verts, faces


def _spinner_fallback(R, l, center_y):
    profile = [(0.0, 0.0), (R, 0.0), (0.0, l)]
    return profile_to_solid_of_revolution(profile, center_y)


def build_parabolic_spinner(props, center_y):
    """Paraboloïde : rayon R à la base, tangent au moyeu, pointe arrondie."""
    d = max(props.spinner_diameter, 1e-3)
    l = max(props.spinner_length, 1e-3)
    R = 0.5 * d
    rounding = clamp(props.spinner_rounding, 0.0, 1.0)
    q = 0.5 + 0.5 * rounding

    profile = [(0.0, 0.0)]
    n = 40
    for i in range(1, n + 1):
        t = i / n
        r = R * max(0.0, 1.0 - t * t) ** q
        profile.append((r, l * t))
    return profile_to_solid_of_revolution(profile, center_y)


def build_ogive_spinner(props, center_y):
    """
    Ogive tangente correcte :
      - rayon maximal exactement d/2 à la base,
      - tangente horizontale au moyeu,
      - nez arrondi raccordé par une courbe de Bézier C1.
    """
    d = max(props.spinner_diameter, 1e-3)
    l = max(props.spinner_length, 1e-3)
    R = 0.5 * d
    rounding = clamp(props.spinner_rounding, 0.0, 1.0)
    rnose = clamp(0.24 * rounding * d, 0.02 * d, 0.45 * R)
    rnose = min(rnose, 0.75 * l)
    ht = l - rnose

    if ht <= 1e-6 or rnose >= R * 0.98 or R <= 1e-9:
        return _spinner_fallback(R, l, center_y)

    # Cercle tangent au cylindre en y=0 et passant par (rnose, ht).
    a = (R * R - rnose * rnose - ht * ht) / (2.0 * (R - rnose))
    rc = R - a
    inner = rc * rc - ht * ht
    if rc <= 1e-9 or inner <= 1e-9:
        return _spinner_fallback(R, l, center_y)

    # Pente dr/dy au point de raccord.
    slope = -ht / math.sqrt(inner)

    profile = [(0.0, 0.0)]
    n_body = 40
    for i in range(1, n_body + 1):
        y = ht * i / n_body
        r = a + math.sqrt(max(0.0, rc * rc - y * y))
        profile.append((min(max(r, 0.0), R), y))

    # Nez : Bézier cubique, tangente de l'ogive au départ, verticale à la pointe.
    p0r, p0y = rnose, ht
    dy = l - ht
    p1r, p1y = p0r + slope * 0.45 * dy, p0y + 0.45 * dy
    p2r, p2y = 0.35 * rnose, l
    n_nose = 16
    for i in range(1, n_nose + 1):
        t = i / n_nose
        u = 1.0 - t
        r = (u ** 3) * p0r + 3 * (u ** 2) * t * p1r + 3 * u * (t ** 2) * p2r
        y = (u ** 3) * p0y + 3 * (u ** 2) * t * p1y + 3 * u * (t ** 2) * p2y + (t ** 3) * l
        profile.append((max(0.0, r), min(y, l)))

    return profile_to_solid_of_revolution(profile, center_y)


# ============================================================
# SHROUD
# ============================================================

def build_shroud(props, center_y):
    # FIX : le jeu shroud_offset est un jeu radial réel (et non la moitié).
    # Une valeur négative recouvre la pointe des pales et les soude à l'anneau.
    offset = props.shroud_offset
    wall = max(props.shroud_wall, 0.2)
    l = max(props.shroud_length, 1.0)
    ch = props.shroud_chamfer
    r_in = max(props.diameter / 2 + offset, props.root_diameter / 2 + 0.5, 0.5)
    r_out = r_in + wall
    y0 = center_y - l / 2
    y1 = center_y + l / 2

    ch = max(0.0, min(ch, wall * 0.4, l * 0.4))

    profile = [
        (r_in + ch, y0),
        (r_in, y0 + ch),
        (r_in, y1 - ch),
        (r_in + ch, y1),
        (r_out - ch, y1),
        (r_out, y1 - ch),
        (r_out, y0 + ch),
        (r_out - ch, y0),
        (r_in + ch, y0),
    ]
    return profile_to_solid_of_revolution(profile, 0.0, n_steps=64)


# ============================================================
# ALÉSAGES
# ============================================================

def make_shaft_cutter(props, y_min, y_max):
    shaft_type = props.shaft_type
    if shaft_type == "none":
        return None

    size = props.shaft_diameter
    y_bottom = y_min - 1.0
    if props.shaft_depth > 0:
        y_top = y_bottom + max(props.shaft_depth, 1.0)
    else:
        y_top = y_max + 1.0
        if props.spinner_type != "none" and props.spinner_on_hub:
            y_top += props.spinner_length
    depth = max(y_top - y_bottom, 1.0)
    y_center = 0.5 * (y_top + y_bottom)

    mesh = bpy.data.meshes.new("ShaftCutter")
    obj = bpy.data.objects.new("ShaftCutter", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    n_seg = 48
    rot = Matrix.Translation((0, y_center, 0)) @ Matrix.Rotation(math.radians(90), 4, 'X')

    if shaft_type == "cylinder":
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n_seg,
                              radius1=size / 2, radius2=size / 2, depth=depth, matrix=rot)

    elif shaft_type == "hex":
        r_circ = size / math.sqrt(3)
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6,
                              radius1=r_circ, radius2=r_circ, depth=depth, matrix=rot)

    elif shaft_type in ("D", "keyway"):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n_seg,
                              radius1=size / 2, radius2=size / 2, depth=depth, matrix=rot)
        bm.to_mesh(mesh)
        bm.free()

        if shaft_type == "D":
            flat_depth = size * 0.15
            flat_x = size / 2 - flat_depth
            cube_bm = bmesh.new()
            bmesh.ops.create_cube(cube_bm, size=1.0)
            for v in cube_bm.verts:
                # FIX : le cube ne coupe que le côté +X (il vidait tout l'alésage).
                v.co.x = v.co.x * size + flat_x + size / 2
                v.co.y = v.co.y * depth * 1.5 + y_center
                v.co.z = v.co.z * size * 2
            op = 'DIFFERENCE'
        else:
            kw_std = keyway_size(size)
            kw_w = props.keyway_size[0] if props.keyway_size[0] > 0 else kw_std[0]
            kw_h = props.keyway_size[1] if props.keyway_size[1] > 0 else kw_std[1]
            kw_w = min(kw_w, size * 0.8)
            kw_h = min(kw_h, kw_w)
            cube_bm = bmesh.new()
            bmesh.ops.create_cube(cube_bm, size=1.0)
            for v in cube_bm.verts:
                v.co.x = v.co.x * kw_w
                v.co.y = v.co.y * depth * 1.5 + y_center
                v.co.z = v.co.z * kw_h + (size / 2)
            op = 'UNION'

        cube_mesh = bpy.data.meshes.new("CutterCube")
        cube_bm.to_mesh(cube_mesh)
        cube_bm.free()
        cube_obj = bpy.data.objects.new("CutterCube", cube_mesh)
        bpy.context.collection.objects.link(cube_obj)

        try:
            _apply_boolean(obj, cube_obj, op, "ShaftShape")
        except Exception:
            _remove_object(obj)
            raise
        finally:
            _remove_object(cube_obj)
        return obj

    bm.to_mesh(mesh)
    bm.free()
    return obj


# ============================================================
# MATÉRIAU
# ============================================================

def _get_propeller_material(rgb):
    mat = bpy.data.materials.get("PropellerMat")
    if mat is None:
        mat = bpy.data.materials.new(name="PropellerMat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out is None:
            out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.42
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return mat


def assign_material(obj, rgb):
    # FIX : un seul slot, toutes les faces dessus (les booléens ajoutaient un slot vide).
    me = obj.data
    me.materials.clear()
    me.materials.append(_get_propeller_material(rgb))
    for p in me.polygons:
        p.material_index = 0


# ============================================================
# UTILITAIRES OBJETS
# ============================================================

def _ensure_object_mode():
    obj = bpy.context.object
    if obj is not None and obj.mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass


def _solo_select(obj):
    _ensure_object_mode()
    view = bpy.context.view_layer
    for o in view.objects:
        try:
            o.select_set(False)
        except RuntimeError:
            pass
    obj.select_set(True)
    view.objects.active = obj


def _remove_object(obj):
    if obj is None:
        return
    try:
        me = obj.data if obj.type == 'MESH' else None
        name = obj.name
    except (ReferenceError, RuntimeError):
        return
    if name not in bpy.data.objects:
        return
    try:
        bpy.data.objects.remove(obj, do_unlink=True)
    except (RuntimeError, ReferenceError):
        return
    if me is not None and me.users == 0:
        try:
            bpy.data.meshes.remove(me)
        except RuntimeError:
            pass


def _join_meshes(target, source):
    """Dernier recours : fusionne les géométries sans booléen."""
    _solo_select(target)
    source.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()


def _apply_boolean(target, operand, operation, name="Bool"):
    """
    Applique un booléen sur une COPIE du maillage, valide le résultat
    (certains solveurs renvoient un maillage vide sans lever d'erreur),
    puis bascule sur un autre solveur si nécessaire.
    """
    solvers = [i.identifier for i in
               bpy.types.BooleanModifier.bl_rna.properties['solver'].enum_items]
    order = [s for s in ("MANIFOLD", "EXACT", "FLOAT") if s in solvers]
    target_faces = len(target.data.polygons)
    operand_faces = len(operand.data.polygons)
    attempts = []

    for solver in order:
        test = target.copy()
        test.data = target.data.copy()
        test.modifiers.clear()
        bpy.context.collection.objects.link(test)
        _solo_select(test)

        mod = test.modifiers.new(name=name, type='BOOLEAN')
        mod.operation = operation
        mod.object = operand
        mod.solver = solver

        result_ok = False
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            nv = len(test.data.vertices)
            nf = len(test.data.polygons)
            if nv > 0 and nf > 0:
                if operation == 'UNION':
                    result_ok = nf >= max(1, int(0.5 * max(target_faces, operand_faces)))
                else:
                    result_ok = nf >= max(1, int(0.2 * target_faces))
            attempts.append(f"{solver}: v={nv} f={nf}")
        except Exception as e:
            attempts.append(f"{solver}: {e}")

        if result_ok:
            good_mesh = test.data
            old_mesh = target.data
            target.data = good_mesh
            bpy.data.objects.remove(test, do_unlink=True)
            if old_mesh.users == 0:
                try:
                    bpy.data.meshes.remove(old_mesh)
                except RuntimeError:
                    pass
            return True

        bad_mesh = test.data
        bpy.data.objects.remove(test, do_unlink=True)
        if bad_mesh.users == 0:
            try:
                bpy.data.meshes.remove(bad_mesh)
            except RuntimeError:
                pass

    raise RuntimeError(f"Booléen {operation} échoué ({name}) : {' | '.join(attempts)}")


def _union_safe(target, operand, name):
    """Union booléenne, avec fusion simple en dernier recours."""
    try:
        _apply_boolean(target, operand, 'UNION', name)
    except RuntimeError as e:
        print(f"Booléen {name} échoué, fusion sans booléen : {e}")
        _join_meshes(target, operand)


# ============================================================
# NETTOYAGE MESH
# ============================================================

def clean_mesh(mesh, dist=0.01):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if dist > 0:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def chamfer_shaft_mouths(obj, radius, chamfer, y_values):
    """Chanfreine les lèvres de l'alésage (type cylindre)."""
    if chamfer <= 1e-6:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    rim = []
    tol_r = max(radius * 0.15, 0.05)
    for e in bm.edges:
        v1, v2 = e.verts
        if abs(v1.co.y - v2.co.y) > 1e-3:
            continue
        for yv in y_values:
            if abs(v1.co.y - yv) < 1e-2 and abs(v2.co.y - yv) < 1e-2:
                r1 = math.hypot(v1.co.x, v1.co.z)
                r2 = math.hypot(v2.co.x, v2.co.z)
                if abs(r1 - radius) <= tol_r and abs(r2 - radius) <= tol_r:
                    rim.append(e)
                    break
    if rim:
        try:
            bmesh.ops.bevel(bm, geom=rim, offset=min(chamfer, radius * 0.4),
                            segments=1, affect='EDGES', clamp_overlap=True)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        except Exception as e:
            print("Chamfer alésage ignoré :", e)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# ============================================================
# VALIDATION + APPLICATION DES PRESETS
# ============================================================

def validate_props(props):
    if props.blades < 1:
        raise ValueError("Blades doit être >= 1")
    if props.diameter <= props.root_diameter:
        raise ValueError("Diameter doit être > Root Diameter")
    if props.root_height <= 0:
        raise ValueError("Root Height doit être > 0")
    if not (1.0 <= props.ellipse_length <= 2.5):
        raise ValueError("Ellipse Length doit être dans [1.0 .. 2.5]")
    if not (0.0 < props.chord_fraction <= 0.8):
        raise ValueError("Chord Fraction doit être dans (0 .. 0.8]")
    if props.transition_point < 0 or props.transition_point > 1:
        raise ValueError("Transition Point doit être dans [0 .. 1]")
    if props.shaft_type != "none":
        if props.shaft_diameter >= props.root_diameter * 0.9:
            raise ValueError("Shaft Diameter est trop grand pour le moyeu")
        if props.shaft_diameter <= 0:
            raise ValueError("Shaft Diameter doit être > 0")
    if props.spinner_type != "none":
        if props.spinner_diameter <= 0 or props.spinner_length <= 0:
            raise ValueError("Spinner Diameter/Length doivent être > 0")
    if props.shroud:
        if props.shroud_wall <= 0 or props.shroud_length <= 0:
            raise ValueError("Shroud Wall/Length doivent être > 0")
    if props.scale <= 0:
        raise ValueError("Scale doit être > 0")


def reset_props(props):
    """Remet toutes les propriétés à leur valeur par défaut."""
    for rp in props.bl_rna.properties:
        key = rp.identifier
        if key in ("rna_type", "name") or rp.is_readonly:
            continue
        try:
            if getattr(rp, "array_length", 0) > 0:
                setattr(props, key, tuple(rp.default_array))
            else:
                setattr(props, key, rp.default)
        except Exception as e:
            print(f"Reset {key} impossible : {e}")


# ============================================================
# CRÉATION DE L'OBJET BLENDER
# ============================================================

def create_propeller_object(context, props):
    validate_props(props)

    temp_objects = []
    result = None
    try:
        # === 1. Pales (un objet par pale : booléens séquentiels robustes) ===
        verts_blade, faces_blade = build_blade_vnf(props)
        if not verts_blade:
            return None

        blade_objs = []
        for b in range(props.blades):
            angle = 2 * math.pi * b / props.blades
            ca, sa = math.cos(angle), math.sin(angle)
            vv = []
            for (x, y, z) in verts_blade:
                vv.append((ca * x + sa * z,
                           y + props.offset,
                           -sa * x + ca * z))

            blade_mesh = bpy.data.meshes.new("PropellerMesh")
            blade_mesh.from_pydata(vv, [], [tuple(f) for f in faces_blade])
            blade_mesh.validate()
            blade_mesh.update()
            clean_mesh(blade_mesh)

            blade = bpy.data.objects.new("Propeller", blade_mesh)
            context.collection.objects.link(blade)
            temp_objects.append(blade)
            blade_objs.append(blade)

        blade_obj = blade_objs[0]

        # === 2. Moyeu ===
        bm = bmesh.new()
        n_hub = 48
        r_hub = props.root_diameter / 2
        h_hub = props.root_height + props.hub_extend

        maxchordlen = 2 * props.chord_fraction * (props.diameter / 2 - r_hub)
        hh = min(maxchordlen, props.root_height)
        y_margin = max(0.5, hh * 0.05)
        y_hub_min = -y_margin
        y_hub_max = h_hub + y_margin

        hub_bottom = []
        hub_top = []
        for i in range(n_hub):
            a = 2 * math.pi * i / n_hub
            hub_bottom.append(bm.verts.new((r_hub * math.cos(a), y_hub_min, r_hub * math.sin(a))))
            hub_top.append(bm.verts.new((r_hub * math.cos(a), y_hub_max, r_hub * math.sin(a))))
        for i in range(n_hub):
            j = (i + 1) % n_hub
            bm.faces.new((hub_bottom[i], hub_bottom[j], hub_top[j], hub_top[i]))
        bm.faces.new(tuple(reversed(hub_bottom)))
        bm.faces.new(tuple(hub_top))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        hub_mesh = bpy.data.meshes.new("HubMesh")
        bm.to_mesh(hub_mesh)
        bm.free()
        hub_obj = bpy.data.objects.new("Hub", hub_mesh)
        context.collection.objects.link(hub_obj)
        temp_objects.append(hub_obj)

        # === 3. Union pales + moyeu, pale par pale ===
        _union_safe(blade_obj, hub_obj, "UnionHub")
        _remove_object(hub_obj)
        if hub_obj in temp_objects:
            temp_objects.remove(hub_obj)

        for other in blade_objs[1:]:
            _union_safe(blade_obj, other, "UnionBlade")
            _remove_object(other)
            if other in temp_objects:
                temp_objects.remove(other)

        # === 4. Spinner ===
        if props.spinner_type != "none":
            # La base est légèrement à l'intérieur du moyeu (recouvrement franc).
            center_y = h_hub - 0.5 if props.spinner_on_hub else -0.5
            if props.spinner_type == "parabolic":
                sp_v, sp_f = build_parabolic_spinner(props, center_y)
            else:
                sp_v, sp_f = build_ogive_spinner(props, center_y)
            if sp_v:
                sp_mesh = bpy.data.meshes.new("SpinnerMesh")
                sp_mesh.from_pydata(sp_v, [], sp_f)
                sp_mesh.validate()
                sp_mesh.update()
                clean_mesh(sp_mesh)
                sp_obj = bpy.data.objects.new("Spinner", sp_mesh)
                context.collection.objects.link(sp_obj)
                temp_objects.append(sp_obj)
                _union_safe(blade_obj, sp_obj, "UnionSpinner")
                _remove_object(sp_obj)
                if sp_obj in temp_objects:
                    temp_objects.remove(sp_obj)

        # === 5. Shroud ===
        if props.shroud:
            center_y = h_hub / 2
            sh_v, sh_f = build_shroud(props, center_y)
            if sh_v:
                sh_mesh = bpy.data.meshes.new("ShroudMesh")
                sh_mesh.from_pydata(sh_v, [], sh_f)
                sh_mesh.validate()
                sh_mesh.update()
                clean_mesh(sh_mesh)
                sh_obj = bpy.data.objects.new("Shroud", sh_mesh)
                context.collection.objects.link(sh_obj)
                temp_objects.append(sh_obj)
                _union_safe(blade_obj, sh_obj, "UnionShroud")
                _remove_object(sh_obj)
                if sh_obj in temp_objects:
                    temp_objects.remove(sh_obj)

        # === 6. Matériau (AVANT les cut, puis réassigné après nettoyage) ===
        assign_material(blade_obj, props.color)

        # === 7. Alésage ===
        cutter = make_shaft_cutter(props, y_hub_min, y_hub_max)
        if cutter is not None:
            temp_objects.append(cutter)
            try:
                _apply_boolean(blade_obj, cutter, 'DIFFERENCE', "ShaftCut")
            finally:
                _remove_object(cutter)
                temp_objects.remove(cutter)

        # === 8. Nettoyage final ===
        clean_mesh(blade_obj.data, dist=0.02)

        # === 9. Chanfrein de l'alésage ===
        if props.shaft_type == "cylinder" and props.shaft_chamfer > 0:
            chamfer_shaft_mouths(blade_obj, props.shaft_diameter / 2,
                                 props.shaft_chamfer, (y_hub_min, y_hub_max))

        # === 10. Matériau / slots définitifs ===
        assign_material(blade_obj, props.color)

        # === 11. Orientation + échelle ===
        rot_x = math.radians(90) if props.z_up else 0.0
        blade_obj.rotation_euler = (rot_x, 0.0, 0.0)
        s = max(props.scale, 1e-6)
        blade_obj.scale = (s, s, s)
        _solo_select(blade_obj)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # === 12. Poser sur le sol ===
        if props.ground and len(blade_obj.data.vertices):
            zmin = min(v.co.z for v in blade_obj.data.vertices)
            blade_obj.data.transform(Matrix.Translation((0.0, 0.0, -zmin)))
            blade_obj.data.update()

        # === 13. UV ===
        if props.uv_unwrap:
            _uv_unwrap(blade_obj)

        # === 14. Lissage ===
        if props.shade_smooth:
            try:
                _solo_select(blade_obj)
                bpy.ops.object.shade_smooth_by_angle(
                    angle=math.radians(35), keep_sharp_edges=True)
            except Exception as e:
                print("Smooth shading indisponible :", e)

        bpy.context.view_layer.update()
        result = blade_obj
        temp_objects.remove(blade_obj)
        return result

    finally:
        for o in list(temp_objects):
            _remove_object(o)


def _uv_unwrap(obj):
    _solo_select(obj)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),
                                 island_margin=0.003,
                                 correct_aspect=True,
                                 scale_to_bounds=False)
    except Exception as e:
        print("UV unwrap ignoré :", e)
    finally:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass


# ============================================================
# OPÉRATEURS
# ============================================================

class PROP_OT_generate(bpy.types.Operator):
    bl_idname = "propeller.generate"
    bl_label = "Generate Propeller"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.propeller_props
        try:
            obj = create_propeller_object(context, props)
        except (ValueError, AssertionError) as e:
            self.report({'ERROR'}, f"Paramètres invalides : {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Erreur : {e}")
            return {'CANCELLED'}
        if obj is None:
            self.report({'ERROR'}, "Génération échouée")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Hélice générée : {len(obj.data.vertices)} vertices")
        return {'FINISHED'}


class PROP_OT_apply_preset(bpy.types.Operator):
    bl_idname = "propeller.apply_preset"
    bl_label = "Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.StringProperty()

    def execute(self, context):
        props = context.scene.propeller_props
        reset_props(props)
        data = PRESETS.get(self.preset, {})
        for key, val in data.items():
            if hasattr(props, key):
                try:
                    setattr(props, key, val)
                except Exception as e:
                    print(f"Preset {self.preset} : impossible de définir {key} = {val} : {e}")
        return {'FINISHED'}


class PROP_OT_reset(bpy.types.Operator):
    bl_idname = "propeller.reset"
    bl_label = "Reset Defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reset_props(context.scene.propeller_props)
        return {'FINISHED'}


# ============================================================
# PANNEAU UI
# ============================================================

class PROP_PT_panel(bpy.types.Panel):
    bl_label = "Propeller Generator"
    bl_idname = "PROP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Propeller"

    def draw(self, context):
        layout = self.layout
        props = context.scene.propeller_props

        header, body = layout.panel("propeller_gen_presets", default_closed=False)
        header.label(text="Presets")
        if body:
            row = body.row(align=True)
            for name in ["rc_plane", "rb_plane", "airplane"]:
                op = row.operator("propeller.apply_preset", text=name.replace("_", " ").title())
                op.preset = name
            row = body.row(align=True)
            for name in ["pc_fan", "toy_boat", "pullcopter"]:
                op = row.operator("propeller.apply_preset", text=name.replace("_", " ").title())
                op.preset = name
            body.operator("propeller.reset", icon='LOOP_BACK')

        header, body = layout.panel("propeller_gen_propeller", default_closed=False)
        header.label(text="Propeller")
        if body:
            body.prop(props, "blades")
            body.prop(props, "diameter")
            body.prop(props, "direction")
            body.prop(props, "root_diameter")
            body.prop(props, "root_height")
            body.prop(props, "pitch")

        header, body = layout.panel("propeller_gen_blade", default_closed=False)
        header.label(text="Blade")
        if body:
            body.prop(props, "chord_mode")
            body.prop(props, "chord_fraction")
            body.prop(props, "ellipse_length")
            body.prop(props, "centerline")
            body.prop(props, "fairing")
            body.prop(props, "sweep")
            body.prop(props, "offset")
            body.prop(props, "pitch_tip")

        header, body = layout.panel("propeller_gen_airfoils", default_closed=True)
        header.label(text="Airfoils")
        if body:
            body.prop(props, "naca_root")
            body.prop(props, "naca_mid")
            body.prop(props, "naca_tip")
            body.prop(props, "transition_point")
            body.prop(props, "trailing_thickness")

        header, body = layout.panel("propeller_gen_hub", default_closed=False)
        header.label(text="Hub & Shaft")
        if body:
            body.prop(props, "hub_extend")
            body.prop(props, "shaft_type")
            body.prop(props, "shaft_diameter")
            body.prop(props, "shaft_depth")
            body.prop(props, "shaft_chamfer")
            if props.shaft_type == "keyway":
                body.prop(props, "keyway_size")

        header, body = layout.panel("propeller_gen_spinner", default_closed=True)
        header.label(text="Spinner")
        if body:
            body.prop(props, "spinner_type")
            if props.spinner_type != "none":
                body.prop(props, "spinner_on_hub")
                body.prop(props, "spinner_diameter")
                body.prop(props, "spinner_length")
                body.prop(props, "spinner_rounding")

        header, body = layout.panel("propeller_gen_shroud", default_closed=True)
        header.label(text="Shroud")
        if body:
            body.prop(props, "shroud")
            if props.shroud:
                body.prop(props, "shroud_offset")
                body.prop(props, "shroud_wall")
                body.prop(props, "shroud_length")
                body.prop(props, "shroud_chamfer")

        header, body = layout.panel("propeller_gen_output", default_closed=True)
        header.label(text="Output")
        if body:
            body.prop(props, "color")
            body.prop(props, "z_up")
            body.prop(props, "scale")
            body.prop(props, "ground")
            body.prop(props, "shade_smooth")
            body.prop(props, "uv_unwrap")
            body.prop(props, "points")
            body.prop(props, "slices")

        layout.operator("propeller.generate", icon="MESH_DATA")


# ============================================================
# ENREGISTREMENT
# ============================================================

classes = (
    PropellerProperties,
    PROP_OT_generate,
    PROP_OT_apply_preset,
    PROP_OT_reset,
    PROP_PT_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.propeller_props = bpy.props.PointerProperty(type=PropellerProperties)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    if hasattr(bpy.types.Scene, "propeller_props"):
        del bpy.types.Scene.propeller_props

if __name__ == "__main__":
    register()
