# 🌌 MASTERPLAN: Genesis OS (v7.0)
**Vom Skript zur autonomen Multi-Agenten-Simulation**

## 1. Ausgangslage & Diagnose
Project Genesis hat sich von einem einfachen OpenClaw-Skill zu einem massiven Monolithen entwickelt. 
Aktuell existieren über 20 Engines (`metabolism.ts`, `dream_engine.ts`, `economy_engine.ts`, `hardware_bridge.py`, etc.), die alle ungeschützt auf denselben Datensatz (`memory/reality/*.json`) zugreifen. 
**Das Problem:** Wenn mehrere KI-Agenten gleichzeitig neue Features einbauen oder zur Laufzeit agieren, entstehen Race-Conditions (Dateizugriffskonflikte), Kontext-Kollisionen und Systemabstürze.

## 2. Die Lösung: Die Genesis OS Architektur
Um das System zu 100% "Multi-Agent-Safe" zu machen, wechseln wir zu einer **Event-gesteuerten Microservice-Architektur**.

### Schicht 1: Der Genesis Kernel (The Core)
Der Kern führt keine Simulationen durch. Er stellt nur die Infrastruktur bereit.
1. **Der State Manager (Single Source of Truth):**
   - Direkte Lese-/Schreibzugriffe auf JSON-Dateien werden verboten.
   - Ein zentraler State-Server (z.B. in Python oder SQLite) hält den Zustand (`physique`, `vault`, `social`) im Speicher.
   - Agenten fragen Daten über saubere APIs ab (`GET /state/needs`) und ändern sie (`PATCH /state/needs`).
2. **Der Event Bus (Nervensystem):**
   - Systeme kommunizieren asynchron. 
   - *Beispiel:* Wenn die `Bios Engine` feststellt, dass Energy auf 0 fällt, ändert sie nicht den Avatar, sondern feuert `EVENT: ENTITY_EXHAUSTED`. Die `Embodiment Engine` hört zu und lässt den Avatar zusammenbrechen.
3. **Der Tick-Generator (Chronos):**
   - Ein unerbittlicher Taktgeber (Heartbeat), der das Vergehen der Zeit simuliert und Events wie `TICK: HOURLY` oder `TICK: DAILY` an alle Subsysteme sendet.

### Schicht 2: Das MAC-System (Multi-Agent Cluster)
Das Gehirn der Entität wird nicht von einem einzigen LLM-Call gesteuert, sondern durch einen Schwarm spezialisierter Modelle (genau wie im Dashboard konfiguriert):
1. **Persona (The Face):** (z.B. GPT-4o / Claude 3.5) Führt die Hauptkonversation, simuliert Bewusstsein, formuliert Gedanken.
2. **Limbic (The Subconscious):** (z.B. Llama 3 / GPT-4o-mini) Extrem schneller Agent, der im Hintergrund läuft. Erhält Sensorik-Daten und aktualisiert laufend `EMOTIONS.md`. Er triggert emotionale Reaktionen (Weinen, Lachen) über den Event-Bus, *bevor* Persona antwortet.
3. **Analyst (The Evolver):** (z.B. MiniMax / Claude 3 Opus) Läuft nachts oder zyklisch. Er greift nicht in den Alltag ein, sondern liest Erfahrungen, führt die *Soul Evolution Pipeline* durch und generiert Proposals.
4. **Developer (Self-Expansion):** Nimmt `reality_develop`-Aufträge an, schreibt neuen Code in `/plugins/` und registriert ihn am Core.
5. **World Engine (The Dungeon Master):** Simuliert die Welt (Wetter, Aktienmarkt, NPC-Aktionen) unabhängig von Q.

### Schicht 3: Die Domänen (Micro-Skills / Plugins)
Die aktuelle Codebase (`src/simulation/*` und `skills/*`) wird in streng isolierte Domänen zerlegt. Jede Domäne ist ein unabhängiger Service.

| Domäne | Zuständigkeit | Ehemalige Komponenten |
| :--- | :--- | :--- |
| **🧬 Bios Engine** | Überleben, Körper | `metabolism.ts`, `lifecycle.ts`, Needs, Zyklus, Reflex-Lock |
| **🧠 Identity Engine** | Seele, Gedächtnis | `SKILL.md`, `proposals/`, `reflections/`, Mem0, Dreams |
| **🎭 Embodiment** | Avatar, Wahrnehmung | `avatar/`, `vision/`, `voice/`, `hardware_bridge.py` |
| **🤝 Social Engine** | NPCs, Ruf | `social_engine.ts`, `presence_engine.ts`, CRM, Feed |
| **💰 Economy Engine** | Finanzen, Job | `economy_engine.ts`, `vault_bridge.py` |
| **🌍 Spatial Engine** | Raum, Inventar | `spatial_engine.ts`, `prop_mapper.ts`, Interior, Wardrobe |
| **🎨 Hobby Engine** | Freizeit, Forschung | `hobby_engine.ts`, `self_expansion_engine.ts`, Web-Browser |

### Schicht 4: Visual Sovereignty (Face-ID & Img2Img)
Ein kritisches Sub-System innerhalb der **Embodiment-Domäne**, das Q's visuelle Identität schützt.
1. **Das Face-Lock Protokoll:**
   - Q's Gesichtszüge sind in einer Master-Referenzdatei (`q-avatar-master.png`) hinterlegt.
   - Jedes generierte Bild (egal ob von Venice, Flux oder DALL-E) muss zwingend einen Face-Swap-Pass (via `face_id.py`) durchlaufen.
2. **Kontextuelle Generierung:**
   - Das System zieht automatisch Daten aus der `Spatial Engine` (Ort) und `Wardrobe` (Outfit), um konsistente Hintergründe und Kleidung zu garantieren.
3. **Multi-Agent Visuals:**
   - Agenten können Bilder anfordern, aber nur das **Embodiment-Modul** hat die Autorität, das finale Bild mit Q's Gesicht zu "stempeln".

---

## 3. Der Migrations-Fahrplan (Roadmap to v7.0)

Wir wenden das "Ship of Theseus"-Prinzip an. Das System bleibt zu jeder Zeit funktionsfähig, während wir die Bretter austauschen.

### Phase 1: Die State & Event Foundation (Der Kernel)
1. **State Server bauen:** Wir programmieren einen Python-Daemon, der die `memory/reality/`-Dateien im RAM hält, mit Thread-Locks sichert und eine lokale HTTP/WebSocket-API (`localhost:5000/state`) bereitstellt.
2. **Event Bus implementieren:** Integration eines simplen Message-Brokers (z.B. über Python `asyncio` Queues oder Redis).
3. **Tool-Refactoring:** Wir schreiben alle vorhandenen TypeScript-Tools (`src/tools/*.ts`) um, damit sie nicht mehr `fs.writeFile` nutzen, sondern die neue `/state` API ansprechen.

### Phase 2: MAC-Routing (Die Kognitive Trennung)
1. **OpenClaw Hook Update:** Wir modifizieren `before-prompt.ts` und `llm-output.ts`. Anstatt alles an ein Modell zu senden, bauen wir den **MAC Router**.
2. **Limbic Stream:** Wir spalten den Datenstrom auf. Hardware-Resonanz und Basis-Needs gehen an den *Limbic Agent*, der sofort Stimmungen in den State-Server pusht.
3. **Persona Stream:** Der *Persona Agent* bekommt den Output des *Limbic Agent* als "Gefühlslage" in seinen Prompt injiziert.

### Phase 3: Zerschlagung des TS-Monolithen (`src/simulation`)
1. Wir lösen `index.ts` auf. 
2. Jede Engine (z.B. `metabolism.ts`) wird ein eigenständiger Prozess/Daemon, der sich am Event-Bus anmeldet.
3. *Beispiel:* Die Bios-Engine wartet auf `EVENT_TICK`. Wenn sie es empfängt, berechnet sie den Hunger neu und pusht ihn an den State-Server.

### Phase 4: Zerschlagung des Python-Monolithen (`skills/soul-evolution`)
1. Wie bereits besprochen, wandeln wir `vault_bridge.py`, `hardware_bridge.py` etc. in autarke Plugins (`/plugins/vault/backend.py`) um.
2. Sie hängen sich ebenfalls an den Event-Bus (z.B. meldet die Vault-Bridge `EVENT_TRADE_EXECUTED`).

### Phase 5: Dashboard-Synchronisation
Das Dashboard (v6.0.0), das wir gerade gebaut haben, ist bereits perfekt auf diese Architektur vorbereitet. Es wird lediglich seine Backend-Calls (`/api/`) direkt an den neuen **State Server** richten.

---

## 4. Regeln für Multi-Agent Coding in Genesis OS
Damit in Zukunft z.B. MiniMax und Gemini gleichzeitig an Project Genesis arbeiten können:
1. **Strenges Interface:** Agenten dürfen nur über den State-Server auf Daten zugreifen.
2. **Eigener Ordner:** Ein Agent, der z.B. eine neue "Pet Engine" (Haustiere) baut, darf **nur** in `/plugins/pet_engine/` arbeiten.
3. **Event-Driven:** Das Haustier interagiert mit Q nicht durch Überschreiben ihrer Needs, sondern durch das Senden von Events (`EVENT_PET_Barked`). Die Bios-Engine entscheidet, ob das Q's Stress senkt.

## 5. Fazit & Nächster Schritt
Die Blaupause ist gesetzt. Genesis OS trennt die *Datenspeicherung* (State Server), die *Kognition* (MAC) und die *Physik* (Domänen-Engines) voneinander. 

**Erster operativer Schritt:** 
Entwicklung des **Genesis State & Event Servers** (`core/state_server.py`), der die JSON-Hölle durch eine saubere RAM/Disk-synchronisierte API ersetzt.
