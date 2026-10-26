import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const MODEL_URL = "../export/robot_mascot.glb";

// ---------------------------------------------------------------- DOM refs
const viewportEl   = document.getElementById("viewport");
const loadingEl    = document.getElementById("loading");
const loadingPctEl = document.getElementById("loading-pct");
const errorEl      = document.getElementById("error");
const errorDetailEl= document.getElementById("error-detail");
const retryBtn     = document.getElementById("retry-btn");
const statTrisEl   = document.getElementById("stat-tris");
const statNodesEl  = document.getElementById("stat-nodes");
const autorotateBtn= document.getElementById("autorotate-btn");
const resetBtn      = document.getElementById("reset-btn");
const poseButtons   = Array.from(document.querySelectorAll(".pose-btn"));

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
viewportEl.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x26333f);
scene.fog = new THREE.Fog(0x26333f, 2.2, 5.5);

const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 50);
let defaultCamPos = new THREE.Vector3(0.55, 0.42, 0.78);
let defaultTarget = new THREE.Vector3(0, 0.17, 0);
camera.position.copy(defaultCamPos);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 0.32;
controls.maxDistance = 1.6;
controls.maxPolarAngle = Math.PI * 0.52;
controls.target.copy(defaultTarget);
controls.autoRotate = false;
controls.autoRotateSpeed = 1.6;

// ---------------------------------------------------------------- lighting
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const hemi = new THREE.HemisphereLight(0x9fb3c4, 0x14181d, 0.55);
scene.add(hemi);

const key = new THREE.DirectionalLight(0xfff2de, 2.4);
key.position.set(0.9, 1.4, 0.9);
key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.near = 0.2;
key.shadow.camera.far = 3;
key.shadow.camera.left = -0.4;
key.shadow.camera.right = 0.4;
key.shadow.camera.top = 0.4;
key.shadow.camera.bottom = -0.4;
key.shadow.bias = -0.0015;
key.shadow.radius = 3;
scene.add(key);

const fill = new THREE.DirectionalLight(0x8fb6ff, 0.5);
fill.position.set(-1.1, 0.6, -0.4);
scene.add(fill);

const rim = new THREE.DirectionalLight(0xffd9a8, 0.9);
rim.position.set(-0.3, 0.9, -1.2);
scene.add(rim);

// ground
const groundGeo = new THREE.CircleGeometry(1.1, 64);
const groundMat = new THREE.ShadowMaterial({ opacity: 0.32 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

const ringGeo = new THREE.RingGeometry(0.0, 0.46, 64);
const ringMat = new THREE.MeshBasicMaterial({
  color: 0x1b2530, transparent: true, opacity: 0.9, side: THREE.DoubleSide,
});
const ringFloor = new THREE.Mesh(ringGeo, ringMat);
ringFloor.rotation.x = -Math.PI / 2;
ringFloor.position.y = -0.0005;
scene.add(ringFloor);

// ---------------------------------------------------------------- resize
function onResize() {
  const w = viewportEl.clientWidth, h = viewportEl.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
window.addEventListener("resize", onResize);
onResize();

// ---------------------------------------------------------------- loading
let robotRoot = null;
const nodes = {};
let poseState = { current: "idle", startedAt: 0, returning: false };
const clock = new THREE.Clock();

function setLoading(pct) {
  if (pct == null) {
    loadingPctEl.textContent = "";
  } else {
    loadingPctEl.textContent = ` ${Math.round(pct)}%`;
  }
}

function hideLoading() {
  loadingEl.classList.add("is-hidden");
}

function showError(message) {
  loadingEl.classList.add("is-hidden");
  errorDetailEl.textContent = message;
  errorEl.hidden = false;
}

function loadModel() {
  errorEl.hidden = true;
  loadingEl.classList.remove("is-hidden");
  setLoading(0);

  if (robotRoot) {
    scene.remove(robotRoot);
    robotRoot = null;
  }

  const loader = new GLTFLoader();
  loader.load(
    MODEL_URL,
    (gltf) => {
      const root = gltf.scene;
      root.traverse((obj) => {
        if (obj.isMesh) {
          obj.castShadow = true;
          obj.receiveShadow = true;
          if (obj.material) obj.material.envMapIntensity = 1.0;
        }
        nodes[obj.name] = obj;
      });

      // Frame & ground the model.
      const box = new THREE.Box3().setFromObject(root);
      const size = new THREE.Vector3();
      box.getSize(size);
      root.position.y -= box.min.y;

      const center = new THREE.Vector3();
      box.getCenter(center);
      const height = size.y;
      const focusHeight = height * 0.46;

      defaultTarget = new THREE.Vector3(0, focusHeight, 0);
      const dist = Math.max(0.45, height * 2.15);
      defaultCamPos = new THREE.Vector3(dist * 0.62, focusHeight + height * 0.18, dist * 0.78);
      camera.position.copy(defaultCamPos);
      controls.target.copy(defaultTarget);
      controls.minDistance = height * 0.9;
      controls.maxDistance = height * 4.2;
      controls.update();

      scene.add(root);
      robotRoot = root;
      captureRestPose();

      const triCount = countTriangles(root);
      const nodeCount = Object.keys(nodes).length;
      statTrisEl.textContent = `${triCount.toLocaleString()} tris`;
      statNodesEl.textContent = `${nodeCount} nodes`;

      hideLoading();
    },
    (xhr) => {
      if (xhr.lengthComputable) setLoading((xhr.loaded / xhr.total) * 100);
    },
    (err) => {
      console.error(err);
      showError(
        "robot_mascot.glb failed to load. Serve this folder over HTTP (not file://) " +
        "from the project root, e.g. `python3 -m http.server` from robot-mascot-studio/, " +
        "then open preview/index.html via that server."
      );
    }
  );
}

function countTriangles(root) {
  let n = 0;
  root.traverse((obj) => {
    if (obj.isMesh && obj.geometry) {
      const geo = obj.geometry;
      n += geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3;
    }
  });
  return Math.round(n);
}

// ---------------------------------------------------------------- pose rig
const restQuat = {};
function captureRestPose() {
  const names = [
    "head", "neck", "torso", "hips",
    "shoulder_L", "shoulder_R",
    "upperarm_L", "upperarm_R",
    "elbow_L", "elbow_R",
    "forearm_L", "forearm_R",
    "wrist_L", "wrist_R",
    "hand_L", "hand_R",
    "antenna_L", "antenna_R",
  ];
  names.forEach((n) => {
    const o = nodes[n];
    if (o) restQuat[n] = o.quaternion.clone();
  });
}

function setLocalEuler(name, x = 0, y = 0, z = 0, order = "XYZ") {
  const o = nodes[name];
  if (!o || !restQuat[name]) return;
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(x, y, z, order));
  o.quaternion.copy(restQuat[name]).multiply(q);
}

function resetPoseNodes() {
  Object.keys(restQuat).forEach((n) => nodes[n] && nodes[n].quaternion.copy(restQuat[n]));
}

const POSE_DURATIONS = { wave: 2.0, point: 1.9, explain: 2.6 };

function animatePose(mode, t) {
  if (!robotRoot) return;

  if (mode === "idle") {
    const bob = Math.sin(t * 1.3) * 0.004;
    robotRoot.position.y = bob + (robotRoot.userData.baseY ?? 0);
    setLocalEuler("head", Math.sin(t * 0.6) * 0.035, Math.sin(t * 0.45 + 1) * 0.05, 0);
    setLocalEuler("torso", 0, Math.sin(t * 0.5) * 0.02, 0);
    setLocalEuler("upperarm_L", Math.sin(t * 0.8) * 0.04, 0, 0);
    setLocalEuler("upperarm_R", Math.sin(t * 0.8 + 1) * 0.04, 0, 0);
    setLocalEuler("antenna_L", Math.sin(t * 1.6) * 0.05, 0, 0);
    setLocalEuler("antenna_R", Math.sin(t * 1.6 + 0.6) * 0.05, 0, 0);
    return;
  }

  resetPoseNodes();
  const bob = Math.sin(t * 1.3) * 0.002;
  if (robotRoot.userData.baseY != null) robotRoot.position.y = bob + robotRoot.userData.baseY;

  if (mode === "wave") {
    const raise = THREE.MathUtils.smoothstep(t, 0, 0.35);
    const lower = 1 - THREE.MathUtils.smoothstep(t, POSE_DURATIONS.wave - 0.4, POSE_DURATIONS.wave);
    const lift = raise * lower;
    const wag = Math.sin(t * 9) * (lift > 0.5 ? 0.35 : 0.1) * lift;
    setLocalEuler("shoulder_R", 0, 0, -lift * 1.9);
    setLocalEuler("upperarm_R", 0, 0, -lift * 0.5);
    setLocalEuler("forearm_R", wag * 0.5, 0, -lift * 0.3);
    setLocalEuler("hand_R", 0, 0, wag);
    setLocalEuler("head", 0, lift * 0.12, 0);
  } else if (mode === "point") {
    const ext = THREE.MathUtils.smoothstep(t, 0, 0.4) * (1 - THREE.MathUtils.smoothstep(t, POSE_DURATIONS.point - 0.4, POSE_DURATIONS.point));
    setLocalEuler("shoulder_R", -ext * 1.2, 0, -ext * 0.5);
    setLocalEuler("upperarm_R", -ext * 0.3, ext * 0.2, 0);
    setLocalEuler("forearm_R", -ext * 0.15, 0, 0);
    setLocalEuler("head", 0, -ext * 0.1, 0);
  } else if (mode === "explain") {
    const env = THREE.MathUtils.smoothstep(t, 0, 0.3) * (1 - THREE.MathUtils.smoothstep(t, POSE_DURATIONS.explain - 0.4, POSE_DURATIONS.explain));
    const sway = Math.sin(t * 1.8);
    setLocalEuler("shoulder_L", 0, 0, sway * 0.5 * env);
    setLocalEuler("shoulder_R", 0, 0, -sway * 0.5 * env);
    setLocalEuler("upperarm_L", -0.3 * env, 0, 0.1 * sway * env);
    setLocalEuler("upperarm_R", -0.3 * env, 0, -0.1 * sway * env);
    setLocalEuler("forearm_L", -0.2 * env, 0, 0);
    setLocalEuler("forearm_R", -0.2 * env, 0, 0);
    setLocalEuler("head", 0, Math.sin(t * 0.9) * 0.08 * env, 0);
  }
}

function setPose(mode) {
  poseButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.pose === mode));
  poseState = { current: mode, startedAt: clock.getElapsedTime() };
}

poseButtons.forEach((btn) => {
  btn.addEventListener("click", () => setPose(btn.dataset.pose));
});

// ---------------------------------------------------------------- tools
autorotateBtn.addEventListener("click", () => {
  controls.autoRotate = !controls.autoRotate;
  autorotateBtn.setAttribute("aria-pressed", String(controls.autoRotate));
});

resetBtn.addEventListener("click", () => {
  controls.autoRotate = false;
  autorotateBtn.setAttribute("aria-pressed", "false");
  camera.position.copy(defaultCamPos);
  controls.target.copy(defaultTarget);
  controls.update();
});

retryBtn.addEventListener("click", loadModel);

// ---------------------------------------------------------------- loop
renderer.setAnimationLoop(() => {
  const t = clock.getElapsedTime();
  if (robotRoot) {
    if (robotRoot.userData.baseY == null) robotRoot.userData.baseY = robotRoot.position.y;
    const elapsed = t - poseState.startedAt;
    const duration = POSE_DURATIONS[poseState.current];
    if (poseState.current !== "idle" && duration != null && elapsed > duration) {
      setPose("idle");
    } else {
      animatePose(poseState.current, poseState.current === "idle" ? t : elapsed);
    }
  }
  controls.update();
  renderer.render(scene, camera);
});

loadModel();
