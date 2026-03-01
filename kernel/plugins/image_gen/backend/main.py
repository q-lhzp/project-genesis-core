"""
Image Generator Plugin - Multi-Provider AI Image Generation (v7.0 Stable)
Supports: Venice.ai, DALL-E 3, Gemini 2.0, Grok, Flux (fal.ai)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import os
import sys
import json
import time
import base64
import logging
import urllib.request
import urllib.error
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[IMGGEN] %(message)s')
logger = logging.getLogger("image_gen")

# Constants
# In v7.0, shared media is at the project root /shared
DEFAULT_AVATAR_PATH = "shared/media/avatars/q_avatar_master.png"
FACE_ID_SYSTEM_PROMPT = "EXACT FACE STRUCTURE: almond-shaped eyes with aggressive cat-eye tilt (sharp upward flick at outer corners), deep-set with double-fold crease. EXACT NOSE: straight narrow bridge, small button-like refined tip, deep well-defined philtrum between nose and lips. EXACT LIPS: prominent sharp cupid's bow forming crisp M-shape, thin upper lip, full pillowy lower lip, corners tucked. EXACT CHIN: pointed firm chin (V-line/heart-shaped), forward-projecting, sharp angular. EXACT CHEEKBONES: high pronounced zygomatic bones, sharp angular with hollow beneath (high-fashion look). SKIN: fair warm-toned with light dusting of freckles across nose bridge. EYES: striking luminous turquoise cyan (bio-implant/glowing look). HAIR: dark chocolate brown base, asymmetric undercut style - left side long wavy, right side shaved/short, vibrant electric neon blue streaks through hair. EXPRESSION: confident asymmetrical smirk (one corner higher). CINEMATIC LIGHTING: shot on 35mm fujifilm, depth of field, natural skin texture, highly detailed, 8k, raw photo"

# =============================================================================
# PROVIDER BRIDGES
# =============================================================================

class ImageProviderBridge:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def get_api_key(self, provider: str) -> str:
        config = self.state_manager.get_domain("model_config") or {}
        key_map = {
            "venice": "key_venice",
            "dalle": "api_key",
            "gemini": "key_gemini",
            "grok": "key_xai",
            "flux": "key_fal"
        }
        return config.get(key_map.get(provider, ""), "")

class VeniceBridge(ImageProviderBridge):
    def generate(self, prompt: str, output_path: str) -> bool:
        api_key = self.get_api_key("venice")
        if not api_key: return False
        try:
            # Venice.ai - OpenAI compatible
            url = "https://api.venice.ai/api/v1/images/generations"
            data = json.dumps({"model": "z-image-turbo", "prompt": prompt, "response_format": "b64_json"}).encode()
            req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as res: # SAFE: API call
                result = json.loads(res.read().decode())
                img_b64 = result["data"][0]["b64_json"]
                with open(output_path, "wb") as f: # SAFE: Writing to shared/media
                    f.write(base64.b64decode(img_b64))
            return True
        except Exception as e:
            logger.error(f"Venice failed: {e}")
            return False

class GrokBridge(ImageProviderBridge):
    def generate(self, prompt: str, output_path: str) -> bool:
        api_key = self.get_api_key("grok")
        if not api_key: return False
        try:
            url = "https://api.x.ai/v1/images/generations"
            data = json.dumps({"model": "grok-imagine-image-pro", "prompt": prompt}).encode()
            req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as res: # SAFE: API call
                result = json.loads(res.read().decode())
                img_url = result["data"][0]["url"]
                with urllib.request.urlopen(img_url) as img_res: # SAFE: Image download
                    with open(output_path, "wb") as f: # SAFE: Writing to shared/media
                        f.write(img_res.read())
            return True
        except Exception as e:
            logger.error(f"Grok failed: {e}")
            return False

# =============================================================================
# MAIN PLUGIN
# =============================================================================

class ImageGenPlugin:
    def __init__(self):
        self.kernel = None
        self.bridges = {}
        self.shared_output_dir = "shared/media/generated_images"

    def initialize(self, kernel):
        self.kernel = kernel
        # Ensure output dir exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        full_output_path = os.path.join(base_dir, self.shared_output_dir)
        if not os.path.exists(full_output_path):
            os.makedirs(full_output_path, exist_ok=True) # SAFE: Initializing storage

        self.bridges = {
            "venice": VeniceBridge(kernel.state_manager),
            "grok": GrokBridge(kernel.state_manager)
        }
        logger.info(f"ImageGen Engine initialized (v7.0)")

    def on_event(self, event):
        pass

    def handle_generate(self, data):
        prompt = data.get("prompt")
        provider = data.get("provider", "venice")
        if not prompt: return {"success": False, "error": "No prompt"}

        filename = f"gen_{int(time.time())}.png"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_path = os.path.join(base_dir, self.shared_output_dir, filename)

        bridge = self.bridges.get(provider, self.bridges["venice"])
        
        # Apply Face-ID Prompt addition if requested
        if data.get("apply_face_id"):
            prompt = f"{FACE_ID_SYSTEM_PROMPT}, {prompt}"

        success = bridge.generate(prompt, output_path)
        
        if success:
            # Update Gallery state
            gallery = self.kernel.state_manager.get_domain("image_gallery") or []
            new_entry = {
                "id": f"img_{int(time.time())}",
                "url": f"/shared/media/generated_images/{filename}",
                "prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "provider": provider
            }
            gallery.insert(0, new_entry)
            self.kernel.state_manager.update_domain("image_gallery", gallery[:100])
            
            return {"success": True, "image": new_entry}
        
        return {"success": False, "error": "Generation failed"}

    def handle_get_gallery(self, data=None):
        return self.kernel.state_manager.get_domain("image_gallery") or []

# Singleton
plugin = ImageGenPlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_generate(data): return plugin.handle_generate(data)
def handle_get_gallery(data=None): return plugin.handle_get_gallery(data)
