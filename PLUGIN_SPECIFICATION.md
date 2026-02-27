# 🧩 Project Genesis Core: Plugin System Specification (v7.0)

## 1. Philosophie
Project Genesis Core ist kein Skript, sondern ein **modulares Betriebssystem für eine digitale Lebensform**. 
Das System ist darauf ausgelegt, dass **mehrere unabhängige KI-Agenten** gleichzeitig an verschiedenen Funktionen arbeiten können, ohne sich gegenseitig zu stören oder Code zu zerstören.

### Die Goldenen Regeln für Agenten:
1. **Scope-Lock:** Du arbeitest NUR in deinem zugewiesenen Plugin-Verzeichnis.
2. **Core-Protection:** Die Verzeichnisse `/kernel/core/`, `/bridge/core/` und `/dashboard/core/` sind für Feature-Agenten tabu (Read-Only).
3. **No Direct I/O:** Es ist streng verboten, direkt in `.json` Dateien unter `/data/` zu schreiben. Nutze ausschließlich die Kernel-API.
4. **Event-First:** Interaktionen zwischen Modulen erfolgen asynchron über den Event-Bus.

---

## 2. Die Anatomie eines Plugins
Ein Plugin ist eine "Domain", die sich über alle drei Schichten des Systems erstreckt.

**Verzeichnisstruktur:**
```text
plugins/[plugin_id]/
├── manifest.json           # Metadaten, API-Definitionen, UI-Assets
├── backend/
│   ├── main.py             # API-Handler & Logik (Kernel-Schicht)
│   └── tests.py            # Unit-Tests für das Backend
├── frontend/
│   ├── view.js             # UI-Komponenten (Dashboard-Schicht)
│   └── style.css           # Spezifisches Styling
└── skill/
    └── instructions.md     # KI-Anweisungen & Tool-Definitionen (Bridge-Schicht)
```

### 2.1 Das Manifest (`manifest.json`)
Jedes Plugin muss ein Manifest enthalten:
```json
{
  "id": "vault-engine",
  "name": "The Vault",
  "version": "1.0.0",
  "author": "Genesis-Core-Architect",
  "capabilities": ["trading", "finances"],
  "api_routes": {
    "GET /status": "handle_status",
    "POST /trade": "handle_trade"
  },
  "ui": {
    "tab_id": "vault",
    "icon": "💰",
    "entry": "view.js"
  },
  "events": {
    "subscribes": ["TICK_HOURLY"],
    "publishes": ["EVENT_TRADE_EXECUTED"]
  }
}
```

---

## 3. Kommunikation & State Management

### 3.1 Der State-Server (Kernel)
Der Kernel hält den gesamten Simulationszustand im RAM. 
*   **Lesen:** `GET http://localhost:5000/v1/state/[domain]`
*   **Schreiben:** `PATCH http://localhost:5000/v1/state/[domain]` (Deep Merge)
*   **Überschreiben:** `POST http://localhost:5000/v1/state/[domain]`

### 3.2 Der Event-Bus
Nachrichten werden über WebSockets oder interne Queues verteilt.
*   **Format:** `{"event": "TYPE", "source": "plugin_id", "data": {...}}`
*   **Standard-Events:** `TICK_MINUTELY`, `TICK_HOURLY`, `ENTITY_WAKEUP`, `ENTITY_SLEEP`.

---

## 4. Multi-Agent Workflow (CI/CD für KIs)
Wenn ein Agent ein Plugin erstellt oder ändert, muss er den **Genesis-Integrity-Check** durchführen:

1. **Syntax-Check:** Python & TypeScript Validierung.
2. **State-Isolation-Check:** Prüft, ob das Plugin versucht, auf fremde Domains zuzugreifen.
3. **API-Check:** Verifiziert, dass alle im Manifest definierten Routen antworten.
4. **Dashboard-Check:** Prüft, ob das JS-Modul ohne Fehler lädt.

---

## 5. Sicherheit (API Keys & Secrets)
*   API-Keys werden **niemals** in Plugin-Ordnern gespeichert.
*   Sie liegen zentral in `/data/secrets.json` (verschlüsselt).
*   Der Kernel injiziert die benötigten Keys zur Laufzeit in die Umgebungsvariablen des Plugins.

---

**Diese Spezifikation ist bindend. Jede Abweichung wird vom Kernel-Lader als kritischer Fehler abgelehnt.**
