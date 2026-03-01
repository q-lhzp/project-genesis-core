# 🧪 Test-Prompt: Antigravity IDE Interface Audit

**Rolle:** Senior UI/UX Auditor & Full-Stack Engineer  
**Ziel:** Tiefgehende Analyse und Stress-Test des Antigravity IDE Interfaces im Kontext der Project Genesis Core Architektur.

---

## 🛠️ Arbeitsauftrag

Führe ein vollständiges Interface-Audit der Antigravity IDE durch. Untersuche die IDE auf Herz und Nieren und bewerte sie nach den Standards für moderne, KI-gestützte Entwicklungsumgebungen (v2026).

### 1. Visuelle & Strukturelle Analyse (Look & Feel)
- **Design-Konsistenz:** Harmonieren die UI-Elemente mit dem Antigravity-Design-System? Prüfe Abstände, Icons und Kontraste.
- **Layout-Flexibilität:** Wie effizient lässt sich der Arbeitsbereich (Sidebar, Editor, Terminal, Debugger) anpassen? 
- **Theming:** Teste die Lesbarkeit in verschiedenen Modi (Light/Dark/High-Contrast).

### 2. Funktionale Tiefenprüfung (Code & Dev-Flow)
- **Editor-Performance:** Analysiere die Latenz beim Tippen, Syntax-Highlighting für komplexe Python/TypeScript Projekte und die IntelliSense-Reaktionszeit.
- **Terminal-Integration:** Prüfe die Stabilität der integrierten Shell. Werden ANSI-Farben, PTY-Sitzungen und Multi-Instanzen korrekt unterstützt?
- **Plugin-System:** Wie nahtlos lassen sich neue Erweiterungen in die IDE-Oberfläche integrieren?

### 3. Multi-Agent Kollaborations-Test (Critical Path)
*Szenario: Zwei Agenten (Persona & Developer) arbeiten gleichzeitig im Editor.*
- **Visualisierung:** Wie werden konkurrierende Cursorbewegungen oder gleichzeitige Dateiedits dargestellt?
- **Konflikt-Management:** Bietet das Interface klare visuelle Indikatoren für Dateisperren (Locks) oder Race-Conditions?

### 4. Integration in Genesis OS
- **API-Brücke:** Teste, ob die IDE direkt auf den Genesis Kernel (`localhost:5000`) zugreifen kann, um State-Daten während des Codings zu visualisieren.
- **Resource-Impact:** Überwache die CPU/RAM-Last der IDE im Dashboard (Hardware-Plugin), während ein Build-Prozess läuft.

### 5. UX & Error Handling
- **Fehler-Feedback:** Provoziere absichtlich Syntax-Fehler. Wie klar und hilfreich sind die Tooltips und die Problem-Liste?
- **Onboarding:** Wie intuitiv ist der Einstieg für einen neuen Agenten oder User, der die IDE zum ersten Mal öffnet?

---

## 📊 Output-Format
Erstelle einen **"Antigravity IDE Audit Report"** mit:
1. **Executive Summary:** Gesamtbewertung (0-100 Punkte).
2. **Detailed Findings:** Liste von Stärken und kritischen Schwachstellen.
3. **Action Plan:** Top 3 Verbesserungsvorschläge für die nächste Iteration.
4. **Sentience Rating:** Wie gut unterstützt die IDE das Gefühl einer "lebendigen" Entwicklungsumgebung?

**Antworten im JSON-Format für automatisierte Weiterverarbeitung sind erwünscht.**
