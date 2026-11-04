<img src="assets/icon.svg" width="64" height="64" alt="News AI">

# News AI — Veille Technique IA & Implantation Workflow (`@Mrthomaslef`)

Portail de veille technique sur les **avancées en Intelligence Artificielle** et **guide d'implantation directe** dans l'écosystème de projets de **Thomas Lefèvre** (Radiologie Ostéo-Articulaire & Interventionnelle à l'Hôpital Cochin, Biblio, Second Brain Obsidian, PatrimoineOS & Outils Quotidien).

---

## 🎯 Architecture & Fonctionnement

Site statique **PWA Mobile & Desktop** (`index.html` unique + `data/embedded_data.js`), installable sur l'écran d'accueil iPhone/iPad/Mac et fonctionnant **100 % hors-ligne** comme en direct :

1. **📰 Flux Tech & Implantations (`11 Playbooks prêts à l'emploi`)**
   - Décryptage sans blabla marketing des avancées techniques : Orchestration multi-modèles (`Council` Gemini 4 Argon + Claude Opus & Subagents en `worktree`), Context Caching 2M tokens (`AGENTS.md`), Serveurs MCP locaux, Vision-Language Models & extraction PDF.js vers Quiz, recherche sémantique hors-ligne par synonymes médicaux, CR-Types dynamiques, catégorisation locale SQLite, et compagnon vocal ESP32.
   - **Bouton `📋 Copier le prompt T3 Code` en 1 clic** sur chaque fiche, contenant déjà les chemins absolus exacts de tes projets locaux (`/Users/thomaslefevre/...`).
   - **Suivi d'implantation personnel** (`🎯 À tester`, `🚧 En cours`, `✅ Implanté`, `★ Favori`) mémorisé sur l'appareil.
2. **🗺️ Audit & Radar de Mes Projets (`12 pôles / 24 applications analysées`)**
   - Cartographie complète de tes dépôts locaux :
     - **Radiologie & Hôpital Cochin** : `COCHIN·OS`, `BiblioOstéo Cochin`, `Archives des Internes`, `QUIZ Imagerie (1 Image 1 Diag)`, `Guide Infiltrations (213 pages)`, `Cochin RI Agenda`, `TPack PACS (DICOM Viewer)`, `QUIZ Cochin MSK (radio-thomas)`.
     - **Biblio, Science & Second Brain** : `BiblioMarie (Infectiologie Pédiatrique)`, `Second Brain Obsidian (/Users/thomaslefevre/2nd brain)`.
     - **Finance, Famille & Store** : `PatrimoineOS (Next.js + SQLite)`, `Tapp Store & Agent Tracking (Google AI Ultra / Claude)`, `Agenda Famille`, `AssMat`, `Photo Takeout`, `Forestia Mobile`, `Xiaozhi ESP32`.
   - Propose pour chaque projet les **prochaines évolutions IA concrètes** avec leur prompt T3 Code prêt à coller.
3. **⚡ Radar Live Web (`Hacker News Algolia` & `ArXiv Imagerie / Agents`)**
   - Scanner temps réel côté navigateur et via Python (`scripts/build_data.py --fetch-live`) qui récupère les dernières discussions techniques (`LLM`, `MCP`, `WebGPU`, `Claude`, `Gemini`) et les preprints ArXiv (`eess.IV`, `cs.CV`, `cs.AI`), avec générateur automatique de prompt d'analyse.
4. **🧠 Export Direct vers Obsidian (`Second Brain`)**
   - Export en 1 clic de n'importe quelle fiche (ou du Playbook complet) en Markdown formaté pour `/Users/thomaslefevre/2nd brain` avec en-tête YAML (`tags`, `domaine`, `date`, `statut`), callouts `> [!IMPORTANT]` et `[[Wikilinks]]`.
5. **🔄 Standard Pull-to-Refresh (`mobile-pull-to-refresh`)**
   - Tirer vers le bas au doigt ou à la souris en haut de page actualise en direct les fichiers JSON et le flux Hacker News avec retour haptique.

---

## 🛠️ Mise à jour de la base et des flux Live

```bash
python3 scripts/build_data.py --fetch-live
```

Ce script met à jour :
- `data/news.json` : les fiches techniques et playbooks d'implantation
- `data/projects.json` : l'audit des projets locaux et opportunités IA
- `data/live_signals.json` : les signaux Hacker News & ArXiv en direct
- `data/embedded_data.js` : le bundle embarqué pour un chargement instantané
