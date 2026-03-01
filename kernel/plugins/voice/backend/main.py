"""
Voice Engine Plugin - Emotional TTS Synthesis (v7.0 Stable)
Refactored for 1:1 Legacy Compliance & v7.0 Architecture
"""

import json
import os
import subprocess
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='[VOICE] %(message)s')
logger = logging.getLogger("voice")

# =============================================================================
# VOICE LOGIC
# =============================================================================

class VoicePlugin:
    def __init__(self):
        self.kernel = None
        self.shared_voice_dir = "shared/media/voice"

    def initialize(self, kernel):
        self.kernel = kernel
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        full_voice_path = os.path.join(base_dir, self.shared_voice_dir)
        if not os.path.exists(full_voice_path):
            os.makedirs(full_voice_path, exist_ok=True) # SAFE: Initializing storage
            
        logger.info("Voice Engine initialized (v7.0)")

    def on_event(self, event):
        pass

    def handle_generate_speech(self, data: Dict[str, Any]):
        """API Handler: POST /v1/plugins/voice/generate"""
        text = data.get("text")
        voice = data.get("voice", "default")
        if not text: return {"success": False, "error": "No text provided"}

        filename = f"speech_{int(time.time())}.wav"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_path = os.path.join(base_dir, self.shared_voice_dir, filename)

        # In a real scenario, this would call Chatterbox-Turbo or ElevenLabs
        # For now, we simulate the output
        try:
            # Simulate shell call to TTS
            logger.info(f"Generating speech for: {text[:30]}...")
            
            # Update state with new audio
            speech_state = {
                "id": f"aud_{int(time.time())}",
                "url": f"/shared/media/voice/{filename}",
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "voice": voice
            }
            
            # Fire Event for Lip-Sync
            self._fire_event("EVENT_SPEECH_GENERATED", speech_state)
            
            return {"success": True, "audio": speech_state}
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return {"success": False, "error": str(e)}

    def handle_list_voices(self, data=None):
        return [
            {"id": "nova", "name": "Nova (Warm/British)"},
            {"id": "shimmer", "name": "Shimmer (Soft/Clear)"},
            {"id": "alloy", "name": "Alloy (Neutral/Direct)"}
        ]

    def _fire_event(self, event_type, data):
        if self.kernel and self.kernel.event_bus:
            asyncio.run_coroutine_threadsafe(
                self.kernel.event_bus.publish(event_type, "plugin.voice", data),
                self.kernel.event_loop
            )

# Singleton instance
plugin = VoicePlugin()

def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_generate_speech(data): return plugin.handle_generate_speech(data)
def handle_list_voices(data=None): return plugin.handle_list_voices(data)
def handle_get_voice_config(data=None): return {"current_voice": "nova", "pitch": 1.0}
def handle_set_emotion(data): return {"success": True, "emotion": data.get("emotion")}
