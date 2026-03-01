# 🛠️ Project Genesis: Plugin Development Guide

Willkommen beim Bau neuer Fähigkeiten für das Genesis OS. Dieser Guide enthält alles, was du (oder deine Sub-Agenten) brauchst, um ein Plugin von Null auf "Production-Ready" zu bringen.

---

## 1. Das Starter-Template

### A. Backend (`backend/main.py`)
Dieses Script wird vom Kernel geladen und ist für die Logik verantwortlich.

```python
from kernel.core.logger import logger
from datetime import datetime

class MyPlugin:
    def __init__(self):
        self.kernel = None

    def initialize(self, kernel):
        """Wird beim Systemstart aufgerufen."""
        self.kernel = kernel
        logger.info("MyPlugin initialized")

    def on_event(self, event):
        """Reagiert auf Events vom Bus."""
        if event["event"] == "TICK_MINUTELY":
            self._do_background_task()

    def handle_status(self):
        """API Handler: GET /v1/plugins/my-id/status"""
        state = self.kernel.state_manager.get_domain("my_domain")
        return {"status": "active", "data": state}

# Singleton Instanz
plugin = MyPlugin()

# Exportierte Funktionen (für den Plugin-Loader)
def initialize(kernel): plugin.initialize(kernel)
def on_event(event): plugin.on_event(event)
def handle_status(): return plugin.handle_status()
```

### B. Unit Test (`backend/tests.py`)
Agenten nutzen dies, um ihre Logik autonom zu verifizieren.

```python
import sys
import unittest
from unittest.mock import MagicMock

def run_tests():
    print("[TEST] Running MyPlugin Backend Tests...")
    # Mocking Kernel/State
    mock_kernel = MagicMock()
    # Hier Testlogik implementieren...
    print("✓ All tests passed.")
    return True

if __name__ == "__main__":
    if not run_tests(): sys.exit(1)
```

### C. Frontend (`frontend/view.js`)
Das Dashboard lädt diese Komponente automatisch in einen isolierten Container.

```javascript
/**
 * UI Komponente für MyPlugin
 */
async function initMyUI() {
  const root = document.getElementById('plugin-root-my-id');
  if (!root) return;

  root.innerHTML = `
    <div class="panel-card">
      <h3>🚀 Mein neues Feature</h3>
      <div id="live-data">Lade Daten...</div>
      <button onclick="triggerAction()">Klick mich</button>
    </div>
  `;
  updateUI();
}

async function updateUI() {
  const resp = await fetch('/v1/plugins/my-id/status');
  const data = await resp.json();
  document.getElementById('live-data').textContent = JSON.stringify(data);
}

// Global registrieren für den Button-Klick
window.triggerAction = () => { alert("Aktion ausgeführt!"); };

// Start-Trigger
setTimeout(initMyUI, 100);
```

---

## 2. Der autonome Workflow für KI-Agenten

Wenn du ein Plugin baust, folge diesem Pfad:

1. **Erstellen:** Lege die Ordnerstruktur laut `PLUGIN_SPECIFICATION.md` an.
2. **Implementieren:** Schreibe Backend, Frontend und Manifest.
3. **Zertifizieren:**
   - Führe `python3 kernel/core/integrity.py kernel/plugins/[deine-id]` aus.
   - Korrigiere alle Fehlermeldungen (Isolation, fehlende Felder).
4. **Testen:**
   - Führe `python3 kernel/core/tester.py` aus.
5. **Einreichen:** Erst wenn beides grün ist, pushe den Code nach GitHub.

---

## 3. Debugging-Tricks
- **Live Logs:** `tail -f kernel.log.jsonl | jq .`
- **API Check:** `curl localhost:5000/v1/plugins` (Zeigt alle geladenen Plugins)
- **State Check:** `curl localhost:5000/v1/state/physique`
