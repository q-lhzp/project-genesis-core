# 🧩 Project Genesis Core: Plugin System Specification (v7.0)

## 1. Philosophie
Project Genesis Core ist ein **modulares Betriebssystem für eine digitale Lebensform**. 
Das System ist darauf ausgelegt, dass **mehrere unabhängige KI-Agenten** gleichzeitig arbeiten können, ohne Code zu zerstören oder Kontext-Kollisionen zu verursachen.

### Die Goldenen Regeln für Agenten:
1. **Scope-Lock:** Du arbeitest NUR in deinem zugewiesenen Plugin-Verzeichnis.
2. **Core-Protection:** Die Verzeichnisse `/kernel/core/`, `/bridge/` und `/dashboard/` sind tabu.
3. **No Direct I/O:** Keine direkten Schreibzugriffe auf `.json` Dateien. Nutze die Kernel-API (`/v1/state`).
4. **Event-First:** Kommunikation erfolgt asynchron über den Event-Bus.

---

## 2. Die Anatomie eines Plugins
Ein Plugin besteht aus drei Schichten: **Backend** (Logik), **Frontend** (UI) und **Skill** (Instruktionen).

**Verzeichnisstruktur:**
```text
plugins/[plugin_id]/
├── manifest.json           # Metadaten & API-Definitionen
├── backend/
│   ├── main.py             # Kernel-Logik & Event-Handler
│   └── tests.py            # Automatisierte Unit-Tests
├── frontend/
│   └── view.js             # Dashboard UI-Komponente
└── skill/ (optional)
    └── instructions.md     # Zusätzliche KI-Instruktionen
```

### 2.1 Das Manifest (`manifest.json`)
```json
{
  "id": "my-engine",
  "name": "My New Feature",
  "version": "1.0.0",
  "api_routes": {
    "GET /status": "handle_status",
    "POST /action": "handle_action"
  },
  "ui": {
    "tab_id": "myfeature",
    "icon": "🚀",
    "entry": "view.js"
  },
  "events": {
    "subscribes": ["TICK_HOURLY"],
    "publishes": ["EVENT_CUSTOM"]
  }
}
```

---

## 3. Zertifizierung (Zwingend erforderlich)
Jeder Agent MUSS sein Plugin zertifizieren, bevor er Code einreicht.

1. **Integrity Check:** `python3 kernel/core/integrity.py kernel/plugins/[plugin_id]`
   - Prüft Struktur, Manifest und Dateisystem-Isolation.
2. **Logic Test:** `python3 kernel/core/tester.py`
   - Führt alle `backend/tests.py` aus.

---

## 4. Debugging & Logging
Nutze den zentralen Logger für maschinenlesbare Fehlerdiagnose:
```python
from kernel.core.logger import logger
logger.info("Task completed", data={"result": "ok"})
```
Alle Logs werden strukturiert in `kernel.log.jsonl` gespeichert.

---

## 5. State Management
- **Lesen:** `GET /v1/state/[domain]`
- **Schreiben:** `PATCH /v1/state/[domain]` (Merge) oder `POST` (Overwrite).
