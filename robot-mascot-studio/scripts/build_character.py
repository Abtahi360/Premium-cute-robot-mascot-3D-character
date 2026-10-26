#!/usr/bin/env python3
"""
build_character.py
Procedurally constructs "Orb" - a premium cute robot mascot - as a rigid
multi-part hierarchy (head/torso/limbs as separate named nodes, parented
like a jointed toy figure, NOT a skinned/deformed mesh - appropriate for a
hard-shell robot character). Exports a single GLB with the full node
hierarchy intact so it can be posed/animated in Three.js by rotating named
nodes, and later re-rigged with true glTF skin/animation clips if desired.

Source of truth for the geometry: this script. No Blender/.blend file is
produced because Blender is not available in this environment (see
docs/README.md for details on that limitation).
"""
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

rng = np.random.default_rng(7)

# ---------------------------------------------------------------- materials
def mat(name, color, metallic, roughness, emissive=None, emissive_strength=1.0):
    kw = dict(
        name=name,
        baseColorFactor=[*color, 1.0],
        metallicFactor=metallic,
        roughnessFactor=roughness,
    )
    if emissive:
        kw["emissiveFactor"] = [c * emissive_strength for c in emissive]
    return PBRMaterial(**kw)

MAT_SHELL   = mat("Shell_IvoryWhite",  (0.95, 0.94, 0.90), 0.15, 0.30)
MAT_GRAPHITE= mat("Graphite_Dark",     (0.09, 0.09, 0.10), 0.35, 0.45)
MAT_COPPER  = mat("Accent_Copper",     (0.75, 0.44, 0.18), 0.90, 0.28)
MAT_FACE    = mat("FaceDisplay_Glass", (0.02, 0.02, 0.025),0.10, 0.06)
MAT_EYE     = mat("Eye_Amber", (0.05,0.03,0.0), 0.0, 0.3,
                   emissive=(1.0, 0.62, 0.12), emissive_strength=4.0)
MAT_SMILE   = mat("Smile_Amber", (0.05,0.03,0.0), 0.0, 0.3,
                   emissive=(1.0, 0.70, 0.25), emissive_strength=3.5)
MAT_CORE    = mat("ChestCore_Cyan", (0.0,0.05,0.06), 0.0, 0.25,
                   emissive=(0.25, 0.85, 1.0), emissive_strength=3.0)
MAT_TIP     = mat("AntennaTip_Amber", (0.05,0.03,0.0), 0.0, 0.3,
                   emissive=(1.0, 0.65, 0.15), emissive_strength=3.0)

def apply_material(m, material):
    m.visual = TextureVisuals(material=material)
    return m

# ------------------------------------------------------------ primitives
def ellipsoid(rx, ry, rz, subdiv=3):
    s = trimesh.creation.icosphere(subdivisions=subdiv, radius=1.0)
    s.apply_scale([rx, ry, rz])
    return s

def capsule(radius, height, subdiv=3):
    return trimesh.creation.capsule(height=height, radius=radius, count=(2**(subdiv+1), 2**subdiv))

def ring(major_r, minor_r, sections=40):
    return trimesh.creation.torus(major_radius=major_r, minor_radius=minor_r,
                                   major_sections=sections, minor_sections=16)

def cyl(radius, height, sections=24):
    return trimesh.creation.cylinder(radius=radius, height=height, sections=sections)

def translate(m, xyz):
    m = m.copy()
    m.apply_translation(xyz)
    return m

def rotate(m, axis, angle_deg, point=(0,0,0)):
    m = m.copy()
    T = trimesh.transformations.rotation_matrix(np.radians(angle_deg), axis, point)
    m.apply_transform(T)
    return m

def arc_tube(halfwidth, dip, radius, n=10, z=0.0, axis_y=0.0):
    """Smile-shaped (u-curve) tube built from chained small capsule segments."""
    xs = np.linspace(-halfwidth, halfwidth, n)
    ys = axis_y + dip * (xs / halfwidth) ** 2 - dip
    pts = np.stack([xs, ys, np.full_like(xs, z)], axis=1)
    parts = []
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        seg_vec = p1 - p0
        seg_len = np.linalg.norm(seg_vec)
        seg = cyl(radius, seg_len, sections=8)
        # cylinder is built along +Z by default in trimesh; align to seg_vec
        z_axis = np.array([0, 0, 1.0])
        v = seg_vec / seg_len
        axis_cross = np.cross(z_axis, v)
        if np.linalg.norm(axis_cross) < 1e-8:
            R = np.eye(4)
        else:
            ang = np.arccos(np.clip(np.dot(z_axis, v), -1, 1))
            R = trimesh.transformations.rotation_matrix(ang, axis_cross)
        seg.apply_transform(R)
        seg.apply_translation((p0 + p1) / 2)
        joint = trimesh.creation.icosphere(subdivisions=2, radius=radius)
        joint.apply_translation(p1)
        parts.extend([seg, joint])
    first_joint = trimesh.creation.icosphere(subdivisions=2, radius=radius)
    first_joint.apply_translation(pts[0])
    parts.append(first_joint)
    return trimesh.util.concatenate(parts)

def merge(parts):
    return trimesh.util.concatenate(parts)

# ---------------------------------------------------------- dimensions (m)
HEAD_H, HEAD_W, HEAD_D = 0.130, 0.112, 0.104
NECK_GAP   = 0.006
TORSO_H, TORSO_W, TORSO_D = 0.075, 0.095, 0.072
HIP_H, HIP_W, HIP_D = 0.022, 0.082, 0.066
UPLEG_L, UPLEG_R = 0.046, 0.0205
LOWLEG_L, LOWLEG_R = 0.040, 0.0175
BOOT_L, BOOT_H, BOOT_W = 0.058, 0.030, 0.034
SHOULDER_R = 0.0195
UPARM_L, UPARM_R = 0.044, 0.0155
FOREARM_L, FOREARM_R = 0.040, 0.0135
HAND_L, HAND_R = 0.024, 0.0135
FINGER_L, FINGER_R = 0.017, 0.0048

# ----------------------------------------------------------- vertical stack
y_ground   = 0.0
y_boot_c   = BOOT_H * 0.46
y_ankle    = BOOT_H * 0.86
y_lowleg_c = y_ankle + LOWLEG_L / 2
y_knee     = y_ankle + LOWLEG_L
y_upleg_c  = y_knee + UPLEG_L / 2
y_hip_jt   = y_knee + UPLEG_L
y_hip_c    = y_hip_jt + HIP_H * 0.55
y_torso_bot= y_hip_jt + HIP_H
y_torso_c  = y_torso_bot + TORSO_H / 2
y_torso_top= y_torso_bot + TORSO_H
y_shoulder = y_torso_top - 0.008
y_head_c   = y_torso_top + NECK_GAP + HEAD_H / 2
TOTAL_H    = y_torso_top + NECK_GAP + HEAD_H

LEG_X = HIP_W * 0.30
ARM_X = TORSO_W / 2 + SHOULDER_R * 0.55

scene = trimesh.Scene()

def add(mesh, material, node_name, parent, local_xyz=(0,0,0), rotation=None):
    """mesh is defined in the PART's own local space, already shaped; we
    place it at local_xyz relative to parent via a transform, and the mesh's
    own vertex data is stored un-translated at the node's local origin."""
    apply_material(mesh, material)
    T = np.eye(4)
    if rotation is not None:
        axis, deg = rotation
        T = trimesh.transformations.rotation_matrix(np.radians(deg), axis)
    T[:3, 3] = local_xyz
    scene.add_geometry(mesh, node_name=node_name, geom_name=node_name,
                        parent_node_name=parent, transform=T)

# root ----------------------------------------------------------------
scene.add_geometry(trimesh.Trimesh(), node_name="root", geom_name=None)

# hips ------------------------------------------------------------------
hips = ellipsoid(HIP_W/2, HIP_H/2, HIP_D/2, subdiv=3)
add(hips, MAT_SHELL, "hips", "root", (0, y_hip_c, 0))

# legs (mirrored) --------------------------------------------------------
for side, sx in (("L", -1), ("R", 1)):
    x = LEG_X * sx
    upleg = capsule(UPLEG_R, UPLEG_L - 2*UPLEG_R)
    upleg = rotate(upleg, (1,0,0), 90)
    add(upleg, MAT_GRAPHITE, f"upperleg_{side}", "hips", (x, y_upleg_c - y_hip_c, 0))

    knee_ring = ring(UPLEG_R*0.95, UPLEG_R*0.22, sections=24)
    knee_ring = rotate(knee_ring, (1,0,0), 90)
    add(knee_ring, MAT_COPPER, f"knee_{side}", f"upperleg_{side}", (0, y_knee - y_upleg_c, 0))

    lowleg = capsule(LOWLEG_R, LOWLEG_L - 2*LOWLEG_R)
    lowleg = rotate(lowleg, (1,0,0), 90)
    add(lowleg, MAT_SHELL, f"lowerleg_{side}", f"knee_{side}", (0, y_lowleg_c - y_knee, 0))

    ankle_ring = ring(LOWLEG_R*0.95, LOWLEG_R*0.22, sections=24)
    ankle_ring = rotate(ankle_ring, (1,0,0), 90)
    add(ankle_ring, MAT_COPPER, f"ankle_{side}", f"lowerleg_{side}", (0, y_ankle - y_lowleg_c, 0))

    boot = ellipsoid(BOOT_W/2, BOOT_H/2, BOOT_L/2, subdiv=3)
    boot = translate(boot, (0, 0, BOOT_L*0.18))
    sole = ellipsoid(BOOT_W/2*0.92, BOOT_H*0.16, BOOT_L/2*0.95, subdiv=2)
    sole = translate(sole, (0, -BOOT_H*0.42, BOOT_L*0.14))
    boot_glow = cyl(BOOT_W*0.22, 0.003, sections=20)
    boot_glow = rotate(boot_glow, (1,0,0), 90)
    boot_glow = translate(boot_glow, (0, -BOOT_H*0.46, BOOT_L*0.45))
    add(merge([boot]), MAT_SHELL, f"foot_{side}_shell", f"ankle_{side}", (0, y_boot_c - y_ankle, 0))
    add(sole, MAT_GRAPHITE, f"foot_{side}_sole", f"ankle_{side}", (0, y_boot_c - y_ankle, 0))
    add(boot_glow, MAT_TIP, f"foot_{side}_glow", f"ankle_{side}", (0, y_boot_c - y_ankle, 0))

# torso -------------------------------------------------------------------
torso = ellipsoid(TORSO_W/2, TORSO_H/2, TORSO_D/2, subdiv=3)
add(torso, MAT_SHELL, "torso", "hips", (0, y_torso_c - y_hip_c, 0))

belt = ring(TORSO_W/2*0.86, TORSO_H*0.045, sections=40)
belt = rotate(belt, (1,0,0), 90)
add(belt, MAT_COPPER, "torso_belt", "torso", (0, -TORSO_H*0.30, 0))

core_ring = ring(0.016, 0.0022, sections=32)
add(core_ring, MAT_COPPER, "chest_ring", "torso", (0, -0.004, TORSO_D/2*0.92))
core_disc = cyl(0.0115, 0.004, sections=28)
core_disc = rotate(core_disc, (1,0,0), 90)
add(core_disc, MAT_CORE, "chest_core", "torso", (0, -0.004, TORSO_D/2*0.95))

# shoulders + arms (mirrored) ---------------------------------------------
for side, sx in (("L", -1), ("R", 1)):
    x = ARM_X * sx
    sh = trimesh.creation.icosphere(subdivisions=3, radius=SHOULDER_R)
    add(sh, MAT_SHELL, f"shoulder_{side}", "torso", (x, y_shoulder - y_torso_c, 0))
    sh_ring = ring(SHOULDER_R*0.92, SHOULDER_R*0.2, sections=24)
    sh_ring = rotate(sh_ring, (0,1,0), 90)
    add(sh_ring, MAT_COPPER, f"shoulder_ring_{side}", f"shoulder_{side}", (0,0,0))

    uparm = capsule(UPARM_R, UPARM_L - 2*UPARM_R)
    uparm = rotate(uparm, (1,0,0), 90)
    # slight outward lean at rest
    uparm = rotate(uparm, (0,0,1), -6*sx)
    add(uparm, MAT_GRAPHITE, f"upperarm_{side}", f"shoulder_{side}", (0.004*sx, -UPARM_L*0.46, 0))

    elbow = ring(UPARM_R*0.95, UPARM_R*0.22, sections=20)
    elbow = rotate(elbow, (1,0,0), 90)
    add(elbow, MAT_COPPER, f"elbow_{side}", f"upperarm_{side}", (0, -UPARM_L*0.52, 0))

    forearm = capsule(FOREARM_R, FOREARM_L - 2*FOREARM_R)
    forearm = rotate(forearm, (1,0,0), 90)
    forearm = rotate(forearm, (0,0,1), -4*sx)
    add(forearm, MAT_SHELL, f"forearm_{side}", f"elbow_{side}", (0, -FOREARM_L*0.46, 0))

    wrist = ring(FOREARM_R*0.95, FOREARM_R*0.22, sections=18)
    wrist = rotate(wrist, (1,0,0), 90)
    add(wrist, MAT_COPPER, f"wrist_{side}", f"forearm_{side}", (0, -FOREARM_L*0.52, 0))

    palm = capsule(HAND_R, HAND_L - 2*HAND_R)
    palm = rotate(palm, (1,0,0), 90)
    finger_parts = [palm]
    for i, fx in enumerate(np.linspace(-1, 1, 4)):
        f = capsule(FINGER_R, FINGER_L - 2*FINGER_R)
        f = translate(f, (fx*HAND_R*1.5, -HAND_L*0.42, 0))
        finger_parts.append(f)
    thumb = capsule(FINGER_R*1.1, FINGER_L*0.85 - 2*FINGER_R)
    thumb = rotate(thumb, (0,0,1), 60*sx)
    thumb = translate(thumb, (HAND_R*1.9*sx, -HAND_L*0.08, 0))
    finger_parts.append(thumb)
    hand = merge(finger_parts)
    add(hand, MAT_SHELL, f"hand_{side}", f"wrist_{side}", (0, -HAND_L*0.42, 0))
    knuckle = cyl(HAND_R*0.55, 0.0025, sections=16)
    knuckle = rotate(knuckle, (1,0,0), 90)
    add(knuckle, MAT_COPPER, f"hand_badge_{side}", f"hand_{side}", (0, 0, HAND_R*0.9))

# neck + head ---------------------------------------------------------------
neck = cyl(TORSO_W*0.18, NECK_GAP*2.2, sections=24)
add(neck, MAT_GRAPHITE, "neck", "torso", (0, y_torso_top - y_torso_c + NECK_GAP*0.3, 0))

head = ellipsoid(HEAD_W/2, HEAD_H/2, HEAD_D/2, subdiv=4)
add(head, MAT_SHELL, "head", "neck", (0, NECK_GAP*1.1 + HEAD_H/2, 0))

# face display --------------------------------------------------------------
face = ellipsoid(HEAD_W*0.37, HEAD_H*0.30, HEAD_D*0.12, subdiv=3)
add(face, MAT_FACE, "face_display", "head", (0, HEAD_H*0.03, HEAD_D*0.44))
bezel = ring(HEAD_W*0.37, HEAD_D*0.012, sections=48)
bezel = rotate(bezel, (1,0,0), 0)
add(bezel, MAT_COPPER, "face_bezel", "head", (0, HEAD_H*0.03, HEAD_D*0.46))

eye_r_outer, eye_r_tube = HEAD_W*0.085, HEAD_W*0.016
for side, ex in (("L", -1), ("R", 1)):
    eye = ring(eye_r_outer, eye_r_tube, sections=32)
    add(eye, MAT_EYE, f"eye_{side}", "face_display", (HEAD_W*0.16*ex, HEAD_H*0.065, HEAD_D*0.17))
    pupil = cyl(eye_r_tube*0.9, 0.003, sections=16)
    pupil = rotate(pupil, (1,0,0), 90)
    add(pupil, MAT_EYE, f"eye_pupil_{side}", f"eye_{side}", (0, 0, eye_r_tube*0.3))

smile = arc_tube(HEAD_W*0.14, HEAD_H*0.028, HEAD_W*0.012, n=10)
add(smile, MAT_SMILE, "smile", "face_display", (0, -HEAD_H*0.09, HEAD_D*0.17))

# ears ------------------------------------------------------------------------
for side, ex in (("L", -1), ("R", 1)):
    outer = ring(HEAD_W*0.14, HEAD_W*0.02, sections=36)
    outer = rotate(outer, (0,1,0), 90)
    add(outer, MAT_GRAPHITE, f"ear_outer_{side}", "head", (HEAD_W*0.49*ex, -HEAD_H*0.02, 0))
    inner = ring(HEAD_W*0.085, HEAD_W*0.014, sections=28)
    inner = rotate(inner, (0,1,0), 90)
    add(inner, MAT_COPPER, f"ear_inner_{side}", f"ear_outer_{side}", (0.004*ex, 0, 0))
    core = cyl(HEAD_W*0.04, 0.003, sections=24)
    core = rotate(core, (0,0,1), 90)
    add(core, MAT_TIP, f"ear_core_{side}", f"ear_inner_{side}", (0.004*ex, 0, 0))

# antennae ----------------------------------------------------------------------
for side, ax in (("L", -1), ("R", 1)):
    rod = cyl(0.0028, HEAD_H*0.34, sections=12)
    base = (HEAD_W*0.30*ax, HEAD_H*0.46, -HEAD_D*0.05)
    tilt = (("z", -14*ax))
    rod2 = rotate(rod, (0,0,1), -14*ax)
    rod2 = rotate(rod2, (1,0,0), -8)
    add(rod2, MAT_GRAPHITE, f"antenna_{side}", "head", base)
    tip = trimesh.creation.icosphere(subdivisions=2, radius=0.006)
    tip_local = trimesh.transformations.rotation_matrix(np.radians(-14*ax), (0,0,1))
    tip_local = tip_local @ trimesh.transformations.rotation_matrix(np.radians(-8), (1,0,0))
    tip_offset = (tip_local @ np.array([0, HEAD_H*0.34, 0, 1]))[:3]
    add(tip, MAT_TIP, f"antenna_tip_{side}", f"antenna_{side}", tip_offset)

# ---------------------------------------------------------------- export
scene.metadata["title"] = "Orb - Premium Cute Robot Mascot"
glb_path = "/home/claude/robot-mascot-studio/export/robot_mascot.glb"
scene.export(glb_path)

# ---------------------------------------------------------------- stats
tri_count = sum(len(g.faces) for g in scene.geometry.values() if hasattr(g, "faces"))
bounds = scene.bounds
import os
size_kb = os.path.getsize(glb_path) / 1024
print(f"TOTAL_HEIGHT_M={TOTAL_H:.4f}")
print(f"HEAD_FRACTION={ (HEAD_H)/TOTAL_H:.3f}")
print(f"TRIANGLES={tri_count}")
print(f"GLB_SIZE_KB={size_kb:.1f}")
print(f"BOUNDS={bounds.tolist() if bounds is not None else None}")
print(f"NODE_COUNT={len(scene.graph.nodes)}")
print("NODES=", sorted(scene.graph.nodes))
