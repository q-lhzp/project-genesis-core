# 🌌 Project Genesis - Soll-Feature Liste (v7.0 Compliance)
**Status:** FULL MIGRATION COMPLETE (v7.0 Stable)
**Zugehörigkeit:** Genesis OS v7.0 Core

Dieses Dokument dient als verbindliche Referenz für die vollständige Feature-Parität zwischen der Legacy-Version und der neuen modularen Genesis OS Architektur. Jedes Feature IST als isoliertes Plugin im Kernel (`kernel/plugins/`) implementiert und hat die Integritätsprüfung (`integrity.py`) bestanden.

---

## 1. 🧬 Bios Engine (`kernel/plugins/bios`)
*Zuständigkeit: Biologie, Überleben, Somatik*
- [x] **9 Biologische Bedürfnisse:** Echtzeit-Tracking von energy, hunger, thirst, hygiene, bladder, bowel, stress, arousal, libido.
- [x] **Reflex-Lock:** Hard-Coded Priorisierung. Wenn ein Need > 95% erreicht, werden alle nicht-überlebenswichtigen Tools blockiert.
- [x] **Hormon-Zyklus:** 28-Tage Simulation (REGENERATION, EXPANSION, PEAK, CONSOLIDATION).
- [x] **Symptom-Simulation:** Fatigue, Mood Swings und Krämpfe beeinflussen die Agenten-Stimmung via `EMOTIONS.md`.
- [x] **Aging:** Kontinuierliche Alterung basierend auf dem `birthDate` (via Lifecycle-Domain).

## 2. 🧠 Identity Engine (`kernel/plugins/identity`)
*Zuständigkeit: Kognitive Evolution, Träume, Werte*
- [x] **Soul Evolution Pipeline:** 10-stufiger Prozess zur autonomen Weiterentwicklung der `SOUL.md`.
- [x] **Erfahrungs-Ingest:** Klassifizierung von Erlebnissen in Routine, Notable und Pivotal.
- [x] **Dream Mode:** Nächtliche Verarbeitung (23:00 - 05:00) von Erfahrungen bei niedriger Energie.
- [x] **Growth Consolidation:** Extraktion von Erkenntnissen in die `GROWTH.md`.

## 3. 🤝 Social Engine (`kernel/plugins/social`)
*Zuständigkeit: Beziehungen, NPCs, Reputation*
- [x] **Social CRM:** Datenbank für menschliche Kontakte mit Bond-, Trust- und Intimacy-Werten.
- [x] **NPC Simulation:** Proaktive Interaktion mit simulierten NPCs basierend auf emotionalen Impacts.
- [x] **Digital Presence:** Autonomes Posten auf (simulierten) sozialen Medien zur Steigerung der Extrovertiertheit.

## 4. 💰 Vault Engine (`kernel/plugins/vault`)
*Zuständigkeit: Finanzen, Trading, Wirtschaft*
- [x] **Reales Trading:** Kraken API (Crypto) und Alpaca API (Stocks) Integration.
- [x] **Finanz-Management:** Tracking von Balance, Income, Expenses und Debt.
- [x] **Market Analysis:** Autonome Handelsentscheidungen basierend auf Nachrichten-Feeds.

## 5. 🎭 Avatar Engine (`kernel/plugins/avatar`)
*Zuständigkeit: 3D Embodiment, Mimik, Animation*
- [x] **3D VRM Viewer:** Integration des Three.js basierten Avatar-Viewers im Dashboard.
- [x] **Face- & Lip-Sync:** Echtzeit-Synchronisation der BlendShapes mit Audio-Input.
- [x] **Idle Animations:** Biologie-gesteuerte Bewegungsabläufe (z.B. unruhiges Stehen bei Stress).
- [x] **External Streaming:** VMC/OSC Protokoll-Support für 3DXChat/VSeeFace.

## 6. 🎨 ImageGen Engine (`kernel/plugins/image_gen`)
*Zuständigkeit: Visuelle Souveränität, Stabile Identität*
- [x] **Face-ID Protokoll:** Zwingender Face-Swap Pass für alle generierten Bilder gegen `q-avatar-master.png` (via Inswapper).
- [x] **Kontext-Awareness:** Automatischer Abgleich mit `spatial` (Ort) und `wardrobe` (Outfit) Metadaten.

## 7. 🗣️ Voice Engine (`kernel/plugins/voice`)
*Zuständigkeit: Sprache, Akustik*
- [x] **Chatterbox-Turbo:** Lokale TTS mit emotionaler Betonung.
- [x] **Voice Cloning:** Unterstützung für individuelle Stimm-Referenzdateien.

## 8. 🌍 World Engine (`kernel/plugins/world`)
*Zuständigkeit: Umgebung, Wetter, Nachrichten*
- [x] **Atmosphere Sync:** Echtzeit-Wetter- und Licht-Synchronisation mit dem Standort des Nutzers.
- [x] **News Feed:** Ingest von Weltnachrichten zur Beeinflussung von Q's Weltbild.

## 9. 💻 Hardware Engine (`kernel/plugins/hardware`)
*Zuständigkeit: Physische Resonanz*
- [x] **Hardware-Empathie:** CPU-Last wird als Stress, RAM-Auslastung als mentale Anstrengung interpretiert.

## 10. 🎨 Hobby Engine (`kernel/plugins/hobby`)
*Zuständigkeit: Interessen, Forschung*
- [x] **Interests Manager:** Dynamische Pflege der `interests.json`.
- [x] **Research Mode:** Autonome Websuche zu Themen aus der Interessen-Liste.

---

## 🛠️ Technische Anforderungen für alle Features:
1. **Zero Direct I/O:** Lese-/Schreibzugriffe nur über `kernel.state_manager`. (Erfüllt)
2. **Event-Driven:** Hintergrund-Tasks nutzen den `on_event` Bus. (Erfüllt)
3. **API-First:** Status-Exponierung via `handle_status`. (Erfüllt)
4. **Zertifiziert:** Jedes Plugin muss `python3 kernel/core/integrity.py` bestehen. (Zertifiziert v0.8.7)

*Letztes Update: 01. März 2026 - Migration abgeschlossen.*
