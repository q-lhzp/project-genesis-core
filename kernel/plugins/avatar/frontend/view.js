/**
 * Avatar Engine Plugin Frontend - VRM Viewer (v7.0 Legacy Style)
 * Matches the look and feel of the project-genesis legacy dashboard.
 */

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

let vrmModel = null;
let scene, camera, renderer;
let targetBlendShapes = { joy: 0, angry: 0, sad: 0, fear: 0, neutral: 1 };
let currentBlendShapes = { joy: 0, angry: 0, sad: 0, fear: 0, neutral: 1 };
const LERP_SPEED = 0.05;

async function initAvatarUI() {
  const root = document.getElementById('plugin-root-avatar');
  if (!root) return;

  root.innerHTML = `
    <style>
      .avatar-container { position: relative; width: 100%; height: 600px; background: radial-gradient(circle, #1a1a2e 0%, #0a0a0f 100%); border-radius: 12px; overflow: hidden; border: 1px solid #1e1e30; }
      canvas { width: 100%; height: 100%; display: block; }
      
      .avatar-hud { position: absolute; bottom: 1rem; left: 1rem; right: 1rem; display: flex; justify-content: space-between; align-items: flex-end; pointer-events: none; }
      .hud-left { background: rgba(10, 10, 15, 0.8); backdrop-filter: blur(8px); padding: 0.8rem 1.2rem; border-radius: 8px; border: 1px solid rgba(124, 111, 240, 0.3); pointer-events: auto; }
      .hud-status { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; text-transform: uppercase; color: #7c6ff0; letter-spacing: 0.1em; margin-bottom: 0.2rem; }
      .hud-val { font-size: 0.9rem; font-weight: bold; color: #eeeef4; }
      
      .loader-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0a0a0f; color: #7c6ff0; z-index: 10; }
      .spinner { width: 40px; height: 40px; border: 3px solid rgba(124, 111, 240, 0.1); border-top-color: #7c6ff0; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
      @keyframes spin { to { transform: rotate(360deg); } }
    </style>

    <div class="avatar-container">
      <div id="av-loader" class="loader-overlay">
        <div class="spinner"></div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; letter-spacing: 0.2em;">Linking Neural Interface...</div>
      </div>
      <canvas id="av-canvas"></canvas>
      <div class="avatar-hud">
        <div class="hud-left">
          <div class="hud-status">Current Expression</div>
          <div id="av-expression" class="hud-val">Neutral</div>
        </div>
        <div style="color: #6a6a80; font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; pointer-events: auto; cursor: help;" title="VRM v1.0 Standard Compliance">SYS_VER: v7.0.4_ZETA</div>
      </div>
    </div>
  `;

  const canvas = document.getElementById('av-canvas');
  setupScene(canvas);
  await loadModel();
  animate();
  
  // Update Loop for expressions
  setInterval(syncAvatarState, 2000);
}

function setupScene(canvas) {
  scene = new THREE.Scene();
  
  camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  camera.position.set(0, 1.3, 2.5);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(5, 5, 5);
  scene.add(directionalLight);
}

async function loadModel() {
  try {
    const resp = await fetch('/v1/state/avatar_state');
    const state = await resp.json();
    
    // In v7.0, VRM paths are relative to /shared/media
    const vrmPath = state.vrm_path || '/shared/media/avatars/q.vrm';
    
    const loader = new GLTFLoader();
    const gltf = await new Promise((res, rej) => loader.load(vrmPath, res, null, rej));
    vrmModel = gltf.scene;
    
    // Auto-scale/position
    vrmModel.position.set(0, 0, 0);
    scene.add(vrmModel);
    
    document.getElementById('av-loader').style.display = 'none';
  } catch (e) {
    console.error("Avatar Load Error:", e);
    document.getElementById('av-loader').innerHTML = `<div style="color:#e05050">Model not found: q.vrm</div>`;
  }
}

function animate() {
  requestAnimationFrame(animate);
  if (vrmModel) {
    // Idle float
    vrmModel.position.y = Math.sin(Date.now() * 0.001) * 0.02;
    vrmModel.rotation.y = Math.sin(Date.now() * 0.0005) * 0.05;

    // Smooth Expression Lerp
    for (const key in targetBlendShapes) {
      currentBlendShapes[key] += (targetBlendShapes[key] - currentBlendShapes[key]) * LERP_SPEED;
    }
    
    applyExpressions();
  }
  renderer.render(scene, camera);
}

function applyExpressions() {
  if (!vrmModel) return;
  // Fallback: Apply color tint based on expressions
  const { joy, angry, sad, fear } = currentBlendShapes;
  
  vrmModel.traverse(child => {
    if (child.isMesh && (child.name.toLowerCase().includes('face') || child.name.toLowerCase().includes('skin'))) {
      if (!child.userData.originalColor) child.userData.originalColor = child.material.color.clone();
      
      const r = child.userData.originalColor.r + (angry * 0.5) + (joy * 0.1);
      const g = child.userData.originalColor.g + (joy * 0.3);
      const b = child.userData.originalColor.b + (sad * 0.4) + (fear * 0.2);
      
      child.material.color.setRGB(Math.min(1, r), Math.min(1, g), Math.min(1, b));
    }
  });
}

async function syncAvatarState() {
  try {
    const resp = await fetch('/v1/state/avatar_state');
    const state = await resp.json();
    if (state.blend_shapes) {
      targetBlendShapes = { ...state.blend_shapes };
      
      // Update HUD
      const dominant = Object.entries(targetBlendShapes).reduce((a, b) => a[1] > b[1] ? a : b)[0];
      document.getElementById('av-expression').textContent = dominant.charAt(0).toUpperCase() + dominant.slice(1);
    }
  } catch (e) {}
}

setTimeout(initAvatarUI, 100);
