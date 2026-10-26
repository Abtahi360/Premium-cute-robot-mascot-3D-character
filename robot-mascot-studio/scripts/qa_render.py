"""
Lightweight headless QA renderer (matplotlib, flat Lambertian shading).
No GPU/OpenGL context is available in this container (no pyglet/OSMesa),
so this produces simplified documentation shots -- not a substitute for
viewing the GLB in the real-time Three.js preview, which uses proper PBR.
"""
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

scene = trimesh.load("/home/claude/robot-mascot-studio/export/robot_mascot.glb")
mesh = scene.dump(concatenate=True)  # bake world transforms, merge all parts
mesh.apply_scale(1.0)

light_dir = np.array([0.4, 0.8, 0.9]); light_dir /= np.linalg.norm(light_dir)

def render(elev, azim, path, title):
    fig = plt.figure(figsize=(5, 6), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_proj_type("ortho")
    tris = mesh.vertices[mesh.faces]
    normals = mesh.face_normals
    shade = np.clip(normals @ light_dir, 0.08, 1.0)
    base = np.array([0.90, 0.89, 0.86])
    colors = base[None, :] * shade[:, None]
    colors = np.clip(colors, 0, 1)
    pc = Poly3DCollection(tris, facecolor=colors, edgecolor=(0,0,0,0.04), linewidths=0.05)
    ax.add_collection3d(pc)
    b = mesh.bounds
    ctr = b.mean(axis=0)
    r = (b[1]-b[0]).max()/2 * 1.1
    ax.set_xlim(ctr[0]-r, ctr[0]+r); ax.set_ylim(ctr[1]-r, ctr[1]+r); ax.set_zlim(ctr[2]-r, ctr[2]+r)
    ax.set_box_aspect([1,1,1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor("#dfe7ee")
    fig.patch.set_facecolor("#dfe7ee")
    ax.set_title(title, fontsize=10, color="#333")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)

# Note: mesh uses Y-up; mplot3d plots (x,y,z) so we feed (x, z, y) via swap trick:
# simplest: rotate view using azim/elev on existing axes with z=height already mapped above (we set zlim to y-range)
# We need faces' (x,y,z) reordered to (x, z_depth, y_height) for correct plot orientation:
mesh.vertices = mesh.vertices[:, [0, 2, 1]]
mesh.faces = mesh.faces  # faces indices unaffected by coordinate swap

render(12, 90,  "/home/claude/robot-mascot-studio/renders/front.png", "Front")
render(12, -90, "/home/claude/robot-mascot-studio/renders/back.png", "Back")
render(12, 0,   "/home/claude/robot-mascot-studio/renders/side.png", "Side")
render(18, 45,  "/home/claude/robot-mascot-studio/renders/three-quarter.png", "Three-Quarter")
print("done")
