/**
 * Embodiment Engine - VRM Viewer Module (v1.0.0)
 */

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

let vrmModel = null;
let scene, camera, renderer;

async function initAvatarUI() {
  const root = document.getElementById('plugin-root-avatar-engine');
  if (!root) return;

  root.innerHTML = `
    <div style="width:100%; height:500px; background:#000; border-radius:8px; overflow:hidden; position:relative;">
      <canvas id="avatar-canvas"></canvas>
      <div id="avatar-loader" style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.7); color:var(--accent);">
        Linking Neural Interface...
      </div>
    </div>
  `;

  const canvas = document.getElementById('avatar-canvas');
  setupScene(canvas);
  await loadModel();
  animate();
  
  // Sync loop for expressions
  setInterval(syncExpressions, 2000);
}

function setupScene(canvas) {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0a12);
  
  camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / 500, 0.1, 1000);
  camera.position.set(0, 1.4, 2.5);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, 500);
  renderer.setPixelRatio(window.devicePixelRatio);

  const light = new THREE.DirectionalLight(0xffffff, 1.0);
  light.position.set(1, 1, 1);
  scene.add(light);
  scene.add(new THREE.AmbientLight(0xffffff, 0.4));
}

async function loadModel() {
  try {
    const resp = await fetch('/v1/plugins/avatar/config');
    const config = await resp.json();
    
    const loader = new GLTFLoader();
    const gltf = await new Promise((res, rej) => loader.load(config.vrm_path, res, null, rej));
    vrmModel = gltf.scene;
    scene.add(vrmModel);
    
    document.getElementById('avatar-loader').style.display = 'none';
  } catch (e) {
    document.getElementById('avatar-loader').textContent = "Connection Error: " + e.message;
  }
}

async function syncExpressions() {
  if (!vrmModel) return;
  try {
    const resp = await fetch('/v1/state/avatar_state');
    const state = await resp.json();
    // In a full three-vrm implementation, we would apply blendshapes here.
    // For now, we simulate by pulsing emissive materials on the face mesh.
    vrmModel.traverse(child => {
      if (child.isMesh && child.name.toLowerCase().includes('face')) {
        const stress = state.blend_shapes?.angry || 0;
        child.material.emissive = new THREE.Color(stress, 0, 0);
        child.material.emissiveIntensity = stress * 0.5;
      }
    });
  } catch (e) {}
}

function animate() {
  requestAnimationFrame(animate);
  if (vrmModel) {
    vrmModel.rotation.y = Math.sin(Date.now() * 0.0005) * 0.1;
  }
  renderer.render(scene, camera);
}

setTimeout(initAvatarUI, 100);
