# 🛡️ Project Genesis: Masterplan für Stabilität & Plugin-Architektur (v6.0.0)

## 1. Das Problem: Die "Kontext-Kollision"
Bisher müssen Agenten für jedes neue Feature zentrale Dateien (index.html, handlers_get.py) ändern. Wenn zwei Agenten gleichzeitig arbeiten, überschreibt einer die Änderungen des anderen. Dies führt zu Codeverlust und instabilem Systemverhalten.

## 2. Die Lösung: Strikte Isolation (Plugin-System)
Wir stellen das System auf eine **mikro-modulare Architektur** um. Ein Feature ist ein autarker Ordner. Das Hinzufügen eines Features erfolgt **ohne Änderung am Core-Code**.

### A. Geplante Struktur
- **/core/**: Enthält den stabilen Kernel (Server, Template-Engine, Plugin-Manager).
- **/plugins/[feature-name]/**: Enthält alles, was das Feature braucht (Manifest, Backend, Frontend).

### B. Automatisierung
- **Backend-Mounting**: Der Server scannt `/plugins/` und registriert Routen automatisch.
- **Frontend-Injektion**: Die Sidebar wird zur Laufzeit aus den Plugin-Manifesten generiert.

## 3. Protokoll gegen Codeverlust (Agent Rules)
1. **Scope-Lock**: Feature-Agenten arbeiten NUR in ihrem Plugin-Ordner.
2. **Core-Protection**: Die `index.html` und der Main-Server sind für Feature-Agenten tabu.
3. **Integrity-Bot**: Ein automatisches Script validiert die Integrität des Cores nach jeder Änderung.

## 4. Nächste Schritte (v6.0.0)
1. **Plugin-Loader**: `soul-viz.py` so umbauen, dass sie Plugins dynamisch erkennt.
2. **Dynamic UI**: `index.html` auf einen dynamischen Tab-Renderer umstellen.
3. **Migration**: Bestehende Features (Vault, Avatar) als Plugins kapseln.
