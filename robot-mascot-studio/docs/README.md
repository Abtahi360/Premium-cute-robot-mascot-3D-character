# Orb — Premium Cute Robot Mascot

A procedurally-built 3D character for a developer portfolio: a rounded,
toy-like robot with an ivory shell, copper accents, a glossy black face
display, and warm amber eyes — built as a real, inspectable, multi-part
GLB rather than a flat image.

## Environment check (Phase 1 — what was actually available)

This container has no Blender, no Blender Python module (`bpy`), and no
GPU/display context (no `pyglet`, no OSMesa). Those were verified, not
assumed — see the commands run at the start of this session. The
network allowlist also only reaches PyPI/npm/GitHub-type package hosts,
not a Blender download.

What *was* available and is what this project actually uses:
- Python + `numpy`
- `trimesh`, `manifold3d`, `pygltflib` (installed this session) for
  constructing real mesh geometry and exporting valid glTF/GLB
- Node.js + a browser-side Three.js (loaded by the browser from a CDN at
  preview time — not something this container runs itself, see
  "What could not be tested" below)

Given that, the chosen workflow was: **procedural geometry construction
in Python** (primitives — ellipsoids, capsules, cylinders, tori —
combined into a named, parented node hierarchy) rather than Blender
sculpting or an AI 3D-generation service (neither was reachable).

## What this produces — and what it doesn't

**Real, not a mockup:** every part (head, face display, eyes, smile,
ear modules, antennae, torso, chest core, shoulders, arms, fingers,
hips, legs, boots) is genuine 3D geometry with volume, visible from
every angle, assembled from 55 named, parented nodes — not a flat
image or a single undifferentiated blob.

**Not a hand-sculpted character.** This is primitive-based procedural
modeling, not an artist's sculpt. It is a solid, coherent first pass —
clean silhouette, correct proportions, real joints — but it will not
have the fine surface nuance a trained 3D character artist would hand-
sculpt in Blender or ZBrush. If you have access to Blender yourself,
the cleanest path to that level of polish is to import `robot_mascot.glb`
and refine from there (see "Getting a .blend file" below).

**No `.blend` file.** Blender isn't installed in this environment, so
there's no `model/robot_mascot.blend` — `scripts/build_character.py`
*is* the editable source of truth instead. To get a `.blend`: open
Blender yourself → File → Import → glTF 2.0 → `export/robot_mascot.glb`.
The full node hierarchy and materials come across.

**Rigid hierarchy, not a skinned skeleton.** The GLB has **0 skins and
0 baked animations** (verified structurally — see QA_CHECKLIST.md).
Instead, each body part is its own mesh, parented to its joint's parent
(e.g. `hand_R` → `wrist_R` → `forearm_R` → `elbow_R` → `upperarm_R` →
`shoulder_R` → `torso`), the same way a jointed toy figure or LEGO
minifig is built. For a hard-shell robot this is arguably more correct
than a deformable skinned mesh (nothing should bend or stretch — shell
panels should rotate rigidly at the seams), and it's enough structure
to pose or animate every joint later, either procedurally or by adding
real glTF skin + AnimationClips in Blender.

**Idle / Wave / Point / Explain exist, but as JavaScript, not glTF
clips.** `preview/main.js` finds each named node at load time and
drives its local rotation every frame (sine-wave idle sway, eased
wave/point/explain gestures that auto-return to idle). This is a real,
working animation system you can see and interact with in the preview
— it's just implemented in the viewer rather than baked into the GLB
file, because hand-authoring glTF animation keyframe buffers by script
is failure-prone and a true sculpted rig is better done in Blender.
Porting these same node names into Blender's dope sheet as keyframes,
or into real `AnimationClip`s, is a reasonable next step.

## Build workflow

```
cd robot-mascot-studio
python3 scripts/build_character.py      # generates export/robot_mascot.glb
python3 scripts/qa_render.py            # regenerates renders/*.png
```

## Running the preview

The viewer must be served over HTTP (not opened as a `file://` URL,
because ES module imports and the GLTFLoader's fetch of the `.glb`
are both blocked under `file://` by most browsers):

```
cd robot-mascot-studio
python3 -m http.server 8080
```

Then open `http://localhost:8080/preview/index.html`.

Controls: drag to orbit, scroll/pinch to zoom, the bottom dock switches
gestures (Idle/Wave/Point/Explain), and the two circular buttons toggle
auto-rotate and reset the camera.

## Known limitations / unfinished work

- No `.blend` (Blender unavailable — see above).
- No baked glTF animation clips or skin (rigid hierarchy + JS-driven
  gestures instead — see above).
- Procedural-primitive aesthetic, not hand-sculpted surface detail.
- The preview's actual in-browser behavior (orbit, zoom, load, console
  errors) **could not be executed/tested in this environment** — there
  is no browser or GPU context available here. It was verified short of
  that: the GLB was structurally validated, all file paths were smoke-
  tested over a real HTTP server, and `main.js` was syntax-checked. See
  QA_CHECKLIST.md for the exact pass/fail/untestable breakdown.
- Triangle count (~42K, see QA_CHECKLIST.md) is real-time friendly but
  under the 50K–100K target range — intentional, given the primitive-
  based workflow; raise `subdivisions` in `build_character.py` to add
  density if a future pass needs it.
