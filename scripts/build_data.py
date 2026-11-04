#!/usr/bin/env python3
"""
Générateur & Synchroniseur de la base de connaissances News AI (@Mrthomaslef).
- Construit `data/news.json`, `data/projects.json` et `data/embedded_data.js`
- Option `--fetch-live` : interroge en direct Hacker News Algolia API & ArXiv API
  pour enrichir le flux avec les dernières publications techniques IA.
"""

from __future__ import annotations

import argparse
import datetime
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    {
        "id": "agents_harness",
        "label": "🤖 Agents, T3 Code & MCP",
        "short": "🤖 Agents & MCP",
        "description": "Orchestration multi-modèles (Gemini 4 Argon + Claude Opus), Council, Subagents parallèles, Context Caching et serveurs MCP."
    },
    {
        "id": "medical_vision",
        "label": "🩻 Vision, Imagerie & PDF",
        "short": "🩻 Vision & Radio",
        "description": "VLM médicaux, OCR PDF.js haute fidélité, pré-annotation de coupes IRM/TDM/Écho, génération de quiz et CR-types radiologiques."
    },
    {
        "id": "rag_biblio_brain",
        "label": "📚 Biblio, PubMed & 2nd Brain",
        "short": "📚 Biblio & Brain",
        "description": "Veille automatisée PubMed → JSON structuré → Zotero → Obsidian (Second Brain Cochin) avec anonymisation RGPD stricte."
    },
    {
        "id": "local_first_webgpu",
        "label": "⚡ Local-First, SQLite & WebGPU",
        "short": "⚡ WebGPU & Data",
        "description": "Inférence locale dans le navigateur (WebGPU / Transformers.js), recherche sémantique hors-ligne et pipelines SQLite/Supabase."
    },
    {
        "id": "voice_automation_iot",
        "label": "🎙️ Voix, Automatisation & IoT",
        "short": "🎙️ Voix & Auto",
        "description": "Dictée vocale radiologique structurée, agents Python locaux (iMessage/Sheet/Takeout), Mac mini M4 et ESP32 Xiaozhi."
    }
]

PROJECTS = [
    {
        "id": "cochin-os",
        "title": "COCHIN·OS — Portail Internes Radio B",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "🦴",
        "path": "/Users/thomaslefevre/.t3/projects/guide-interne-cochin-os",
        "prodUrl": "https://mrthomaslef.github.io/guide-interne-cochin-os/",
        "githubUrl": "https://github.com/Mrthomaslef/guide-interne-cochin-os",
        "stack": "PWA Statique • Hub Unifié (Planning, Annuaire 1XXXX, Biblio, Quiz, Infiltrations, Archives)",
        "summary": "Portail « Papier Radio / Négatoscope » donnant accès en 1 tap aux 7 outils des internes de Radiologie B à Cochin.",
        "aiOpportunities": [
            {
                "title": "Recherche fédérée Omnibox (⌘K) sur les 7 apps Cochin",
                "impact": "Quick Win",
                "detail": "Un champ unique en haut de COCHIN·OS qui cherche simultanément un poste DECT/console dans l'Annuaire, une fiche parmi les 75 gestes du Guide Infiltrations, un article BiblioOstéo et un cours des Archives.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/guide-interne-cochin-os, ajoute une barre de recherche universelle (Omnibox ⌘K et bouton mobile) qui indexe en local les postes de ./annuaire/, les 75 fiches de ./infiltrations/guide-data.json et les articles de BiblioOstéo pour ouvrir directement le bon outil ou numéro en 1 tap."
            },
            {
                "title": "Assistant « Garde & Prise de Poste » hors-ligne",
                "impact": "Haute Valeur",
                "detail": "Arbre de décision instantané pour l'interne (gestion des anticoagulants Eliquis/Plavix avant geste RI, protocole allergie iode, numéros d'urgence Achard/Ollier).",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/guide-interne-cochin-os, crée un tiroir rapide « Check-list Pré-Geste RI & Anticoagulants » basé sur les fiches de /Users/thomaslefevre/2nd brain/02 - Radiologie Interventionnelle (RI) et le Guide Infiltrations."
            }
        ]
    },
    {
        "id": "biblioosteo",
        "title": "BiblioOstéo Cochin",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "📚",
        "path": "/Users/thomaslefevre/.t3/projects/biblioosteo",
        "prodUrl": "https://mrthomaslef.github.io/biblioosteo/",
        "githubUrl": "https://github.com/Mrthomaslef/biblioosteo",
        "stack": "PWA Vanilla JS • PubMed E-Utilities • Zotero API v3 • PDFs locaux • Python Builder",
        "summary": "Veille bibliographique en RI & imagerie ostéo-articulaire calquée sur l'Agenda Interventionnel Cochin avec synchro Zotero.",
        "aiOpportunities": [
            {
                "title": "Pipeline PMID / PDF → Fiche structurée FR + Lien Second Brain automatique",
                "impact": "Quick Win",
                "detail": "En passant un simple PMID ou PDF dans `scripts/add_article.py`, générer automatiquement le résumé structuré FR, le protocole technique (aiguille, fenêtre bléomycine, suivi IRM), le lien `cochin_link` et la note Obsidian dans `2nd brain/05 - Biblio`.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblioosteo/scripts/add_article.py, ajoute un mode qui prend une liste de PMIDs ou un PDF local, récupère les métadonnées PubMed + Impact Factor, structure automatiquement la fiche JSON (title_fr, summary_fr_short, protocol_fr, cochin_link, key_points_fr), met à jour data/embedded_data.js et crée la fiche correspondante dans /Users/thomaslefevre/2nd brain/05 - Biblio, Zotero & Enseignement."
            },
            {
                "title": "Mode « Comparateur de Protocoles RI » (ex. Cryo Desmoïdes vs RF Ostéome)",
                "impact": "Moyen Terme",
                "detail": "Vue tableau synthétique extrayant des 24+ articles les paramètres opératoires exacts (cycles de congélation, marges de sécurité, hydrodissection, suivi).",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblioosteo/index.html, ajoute un onglet « ⚡ Protocoles RI comparés » qui synthétise sous forme de tableau filtrable les paramètres techniques extraits de chaque article (indication, matériel, protocole, suivi)."
            }
        ]
    },
    {
        "id": "biblio-marie",
        "title": "BiblioMarie — Infectiologie Pédiatrique",
        "category": "Biblio, Science & Second Brain",
        "emoji": "🧸",
        "path": "/Users/thomaslefevre/.t3/projects/biblio-marie",
        "prodUrl": "https://mrthomaslef.github.io/biblio-marie/",
        "githubUrl": "https://github.com/Mrthomaslef/biblio-marie",
        "stack": "PWA Éditoriale (Source Serif 4 + Inter) • JSON/PubMed • Export Zotero API / RIS / BibTeX",
        "summary": "Veille bibliographique pour Marie en pédiatrie générale et infectiologie pédiatrique/adulte avec Impact Factor et Zotero.",
        "aiOpportunities": [
            {
                "title": "Alerte automatique PubMed RSS sur les revues à haut Impact Factor (NEJM, Lancet, JAMA Peds, PIDJ)",
                "impact": "Quick Win",
                "detail": "Script Python hebdomadaire qui détecte les nouveaux essais randomisés et recommandations GPIP/SPILF/ECIL et prépare les brouillons dans `data/editorial.json`.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblio-marie/scripts/, crée un script discover_pubmed.py qui interroge l'API NCBI E-utilities sur les essais cliniques et guidelines récents en infectiologie pédiatrique (GPIP, SPILF, VRS, sepsis, IOA) et pré-remplit les candidats à valider pour data/editorial.json."
            },
            {
                "title": "Mode Audio « Podcast Flash 2 min » (Web Speech / TTS)",
                "impact": "Quick Win",
                "detail": "Bouton d'écoute mains-libres dans le lecteur d'article pour écouter la synthèse française et « En pratique » en déplacement.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblio-marie/index.html, ajoute un bouton « 🎧 Écouter la synthèse » dans la barre du lecteur d'article (avec contrôle de vitesse 1x / 1.25x / 1.5x via speechSynthesis) et intègre le standard Pull-to-Refresh mobile."
            }
        ]
    },
    {
        "id": "archive-des-internes",
        "title": "Archives des Internes — COCHIN·OS (07)",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "🗂️",
        "path": "/Users/thomaslefevre/.t3/projects/archive-des-internes",
        "prodUrl": "https://mrthomaslef.github.io/guide-interne-cochin-os/archives/",
        "githubUrl": None,
        "stack": "PDF.js • Supabase Storage & Postgres • Recherche plein texte par diapo • Mode Diagnostic Masqué",
        "summary": "Partage et visionneuse des présentations PDF (Bone Club, Cas du mardi, Biblio du vendredi, Cours) avec indexation par diapo.",
        "aiOpportunities": [
            {
                "title": "Auto-Tagging & Résumé à l'import du PDF + Conversion 1-Clic vers Quiz Imagerie",
                "impact": "Haute Valeur",
                "detail": "Lors du dépôt d'un PDF avec PDF.js, extraire automatiquement du texte des diapos la modalité (IRM/TDM/Radio), l'articulation, les mots-clés sémiologiques et permettre d'exporter une diapo clé vers Quiz Imagerie.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/archive-des-internes, améliore le flux de dépôt PDF pour détecter automatiquement depuis le texte extrait par PDF.js la catégorie, la région anatomique, la modalité et proposer les synonymes diagnostiques."
            }
        ]
    },
    {
        "id": "quiz-imagerie",
        "title": "QUIZ Imagerie Cochin — 1 Image · 1 Diagnostic",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "🩻",
        "path": "/Users/thomaslefevre/.t3/projects/quiz-image-3",
        "prodUrl": "https://mrthomaslef.github.io/quiz-imagerie/",
        "githubUrl": "https://github.com/Mrthomaslef/quiz-imagerie",
        "stack": "React 18 • Vite • Framer Motion • Visionneuse fenêtrage/zoom • Studio Cmd+V",
        "summary": "Défi diagnostique rapide sur image unique avec validation souple (synonymes + tolérance orthographique) et Studio d'ajout.",
        "aiOpportunities": [
            {
                "title": "Générateur automatique de synonymes, variantes orthographiques et indices sémiologiques dans #/studio",
                "impact": "Quick Win",
                "detail": "Quand tu colles une image (`Cmd+V`) et saisis le diagnostic principal dans `#/studio`, pré-remplir automatiquement tous les synonymes français/anglais, acronymes et mots-clés requis pour la validation souple.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/quiz-image-3, enrichis le Studio (#/studio) avec un dictionnaire ostéo-articulaire intelligent qui génère automatiquement les synonymes, variantes d'accents/abréviations, la région anatomique et les indices sémiologiques dès qu'on tape le nom de la pathologie."
            },
            {
                "title": "Révision espacée (SRS / Anki-like) sur les cas « À revoir »",
                "impact": "Quick Win",
                "detail": "Prioriser automatiquement dans le mode Focus Quiz les cas échoués il y a 1, 3 ou 7 jours.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/quiz-image-3, ajoute un algorithme de répétition espacée léger dans localStorage pour proposer en priorité les cas diagnostiques échoués ou hésitants."
            }
        ]
    },
    {
        "id": "guide-infiltration",
        "title": "Guide Infiltrations — COCHIN·OS (06)",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "💉",
        "path": "/Users/thomaslefevre/.t3/projects/guide-infiltration",
        "prodUrl": "https://mrthomaslef.github.io/guide-interne-cochin-os/infiltrations/",
        "githubUrl": None,
        "stack": "PWA Mobile • 213 pages & 75 fiches structurées (`guide-data.json`)",
        "summary": "Manuel complet des 75 procédures d'infiltrations, arthrographies et biopsies ostéo-articulaires radioguidées.",
        "aiOpportunities": [
            {
                "title": "Mode « Préparation Plateau & Check-list Salle » par procédure",
                "impact": "Quick Win",
                "detail": "Afficher en haut de chacune des 75 fiches un bandeau ultra-lisible pour le manip/interne : aiguille exacte (G/longueur), produit de contraste, corticoïde (Hydrocortancyl / Diprostène / Altim), position patient et rayon directeur.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/guide-infiltration, ajoute en haut de chaque procédure un encart résumé « Plateau & Paramètres Clés » (Aiguille, Produit, Position, Cible) extrait de guide-data.json pour une lecture en 3 secondes en salle."
            }
        ]
    },
    {
        "id": "second-brain",
        "title": "Second Brain Obsidian — Radiologie B Cochin",
        "category": "Biblio, Science & Second Brain",
        "emoji": "🧠",
        "path": "/Users/thomaslefevre/2nd brain",
        "prodUrl": None,
        "githubUrl": None,
        "stack": "Obsidian Markdown • YAML Frontmatter • [[Wikilinks]] • Piloté par T3 Code",
        "summary": "Cerveau numérique médical et interventionnel (Prise de poste, Fiches RI, CR-Types IRM/TDM, RCP Sarcomes, Biblio).",
        "aiOpportunities": [
            {
                "title": "Script d'audit du graphe Obsidian & Liaison automatique avec BiblioOstéo et l'Agenda RI",
                "impact": "Quick Win",
                "detail": "Détecter les notes orphelines, vérifier l'anonymisation RGPD (absence totale de dates de naissance / NIP) et injecter automatiquement les références PMID de BiblioOstéo dans les fiches RI correspondantes.",
                "prompt": "Crée un script Python dans /Users/thomaslefevre/2nd brain qui vérifie l'anonymisation RGPD de toutes les notes Markdown, liste les [[Wikilinks]] manquants et relie chaque fiche de '02 - Radiologie Interventionnelle (RI)' aux articles correspondants de /Users/thomaslefevre/.t3/projects/biblioosteo/data/articles.json."
            }
        ]
    },
    {
        "id": "agenda-interventionnel",
        "title": "Cochin RI — Agenda Interventionnel & Planning Internes",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "📅",
        "path": "/Users/thomaslefevre/Documents/Agendainterventionnel",
        "prodUrl": "https://mrthomaslef.github.io/agenda-cochin/",
        "githubUrl": "https://github.com/Mrthomaslef/agenda-cochin",
        "stack": "Python Sync (`sync_sheet.py`, `fetch_imessages.py`, `fetch_emails.py`) • Google Sheets • PWA",
        "summary": "Synchronisation temps réel du planning de Radiologie Interventionnelle Cochin, vacations, consultations et biopsies.",
        "aiOpportunities": [
            {
                "title": "Briefing automatique de la vacation RI du lendemain (Croisement Planning + Fiches 2nd Brain + Biblio)",
                "impact": "Haute Valeur",
                "detail": "Générer en 1 commande un résumé de préparation pour ta vacation du lendemain : liste des actes prévus (ex. cryoablation desmoïde, biopsie sacrée, cimentoplastie) avec rappel automatique de tes fiches techniques du Second Brain.",
                "prompt": "Crée un script briefing_ri.py dans /Users/thomaslefevre/Documents/Agendainterventionnel qui lit les actes à venir via sync_sheet.py et génère un briefing Markdown croisé avec les fiches techniques de /Users/thomaslefevre/2nd brain/02 - Radiologie Interventionnelle (RI)."
            }
        ]
    },
    {
        "id": "patrimoine-os",
        "title": "PatrimoineOS — Banque, Crypto EVM & Pokémon Collectr",
        "category": "Finance & Quotidien",
        "emoji": "💰",
        "path": "/Users/thomaslefevre/.t3/projects/finance",
        "prodUrl": "http://localhost:3000",
        "githubUrl": None,
        "stack": "Next.js 15 • React 19 • better-sqlite3 • GoCardless DSP2 • RPC EVM / DeFiLlama • Collectr",
        "summary": "Suivi local unifié du patrimoine sur 3 piliers : Crédit Mutuel, MetaMask & Ledger (6 chaînes EVM) et scellés/cartes Pokémon.",
        "aiOpportunities": [
            {
                "title": "Catégorisation intelligente locale des lignes CSV/DSP2 Crédit Mutuel & Détection d'anomalies",
                "impact": "Quick Win",
                "detail": "Classer automatiquement chaque dépense/revenu bancaire (santé, garde d'enfant Pajemploi, abonnements IA, épargne, loisirs) dans SQLite avec graphique d'évolution du taux d'épargne mensuel.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/finance, ajoute un moteur de catégorisation automatique des transactions Crédit Mutuel (src/lib/credit-mutuel.ts) avec règles personnalisables persistées dans SQLite et vue analytique mensuelle Cashflow / Épargne."
            },
            {
                "title": "Snapshots historiques automatiques & Courbe de valeur nette consolidée (EUR)",
                "impact": "Quick Win",
                "detail": "Enregistrer dans `data/finance.db` un point quotidien de la valeur des 3 piliers (Banque + Crypto + Pokémon) pour tracer la performance réelle et les plus-values latentes.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/finance, ajoute une table SQLite `net_worth_snapshots` qui enregistre automatiquement l'historique quotidien des 3 piliers (Crédit Mutuel, Wallets EVM, Collectr Pokémon) et affiche une courbe interactive d'évolution."
            }
        ]
    },
    {
        "id": "tapp-store-allinone",
        "title": "Tapp Store & Agent Tracking (Google AI Ultra / Claude)",
        "category": "Jeux, Hardware & Store",
        "emoji": "🛍️",
        "path": "/Users/thomaslefevre/.t3/projects/allinone",
        "prodUrl": "https://mrthomaslef.github.io/allinone/",
        "githubUrl": "https://github.com/Mrthomaslef/allinone",
        "stack": "PWA Store • GitHub API Sync • Python Daemon (`gemini_ultra_daemon.py`) • Cloudflare Tunnel",
        "summary": "App Store mobile unifié regroupant toutes tes webapps + dashboard temps réel des quotas et coûts API Gemini 4 Argon & Claude.",
        "aiOpportunities": [
            {
                "title": "Intégration directe de News AI dans le Tapp Store + Recommandation de modèle selon ton quota live",
                "impact": "Quick Win",
                "detail": "Ajouter News AI dans `projects.json` du Tapp Store et afficher dans Agent Tracking quel modèle utiliser maintenant selon le pourcentage restant avant le reset de 5h.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/allinone/projects.json, ajoute l'application News AI et enrichis gemini-ultra/index.html avec un indicateur de rythme de consommation (Burn Rate) avant la prochaine heure de reset."
            }
        ]
    },
    {
        "id": "dicomviewer-radio-thomas",
        "title": "TPack PACS (DICOM Viewer) & QUIZ Cochin MSK (radio-thomas)",
        "category": "Radiologie & Hôpital Cochin",
        "emoji": "🖥️",
        "path": "/Users/thomaslefevre/Documents/dicomviewer",
        "prodUrl": "https://mrthomaslef.github.io/dicomviewer/",
        "githubUrl": "https://github.com/Mrthomaslef/dicomviewer",
        "stack": "TypeScript • React • Vite • DICOM / .tpack • Vercel & Supabase (`radio-thomas`)",
        "summary": "Console PACS pédagogique en ligne et banque de cas cliniques d'imagerie musculosquelettique.",
        "aiOpportunities": [
            {
                "title": "Export 1-Clic d'une coupe clé du DICOM Viewer vers QUIZ Imagerie (1 Image 1 Diag)",
                "impact": "Haute Valeur",
                "detail": "Depuis TPack PACS, capturer la coupe courante avec son fenêtrage optimal, anonymiser les métadonnées et générer directement l'entrée JSON pour `quiz-image-3`.",
                "prompt": "Dans /Users/thomaslefevre/Documents/dicomviewer, ajoute un bouton « Exporter vers Quiz Imagerie » qui capture le canvas de la coupe active avec son fenêtrage actuel et génère la fiche JSON compatible avec /Users/thomaslefevre/.t3/projects/quiz-image-3."
            }
        ]
    },
    {
        "id": "family-daily-apps",
        "title": "Écosystème Famille & Quotidien (Agenda Famille, AssMat, Photo, Voyages, Forestia)",
        "category": "Finance & Quotidien",
        "emoji": "🏡",
        "path": "/Users/thomaslefevre/Documents/agenda-famille",
        "prodUrl": "https://mrthomaslef.github.io/agenda-famille/",
        "githubUrl": "https://github.com/Mrthomaslef/agenda-famille",
        "stack": "PWA • Python Sync (`sync_family_agenda.py`, `process_takeout.py`) • Swift/DOSBox (`forestia-mobile`)",
        "summary": "Outils familiaux sur-mesure : planning partagé Marie & Thomas + gardes Cochin + Mabrouka, paie AssMat Pajemploi, tri Google Photos APFS et voyages.",
        "aiOpportunities": [
            {
                "title": "Synchronisation croisée Gardes Cochin → Agenda Famille → Calcul automatique des heures AssMat",
                "impact": "Haute Valeur",
                "detail": "Relier automatiquement les gardes/vacations de `cochin_gardes.json` et `agenda-famille` au calculateur mensuel `Assistantematernelle` pour pré-remplir les jours de présence de Mabrouka.",
                "prompt": "Crée un pont entre /Users/thomaslefevre/Documents/agenda-famille/family_data.json et /Users/thomaslefevre/Assistantematernelle pour pré-remplir automatiquement les horaires et jours de garde du mois dans le calculateur Pajemploi."
            }
        ]
    }
]

NEWS_ITEMS = [
    {
        "id": "council-multi-model-consensus",
        "category_id": "agents_harness",
        "date": "2026-11-04",
        "date_fr": "Novembre 2026",
        "maturity": "🔥 Impact Immédiat",
        "setup_time": "Déjà installé (Skill Council)",
        "cost_badge": "Inclus • Google AI Ultra + Claude Pro",
        "source": "T3 Code • Orchestration Multi-Modèles",
        "source_url": "https://t3.codes",
        "title_fr": "Orchestration « Council » & Subagents isolés en Worktree : faire débattre Gemini 4 Argon et Claude Opus sur ton code",
        "summary_fr": "Plutôt que d'utiliser un seul modèle en séquence, les harnais d'agents modernes (comme T3 Code avec `delegate_task` et le skill `council`) permettent de lancer en parallèle plusieurs modèles d'architectures différentes (ex. Gemini 4 Argon + Claude Opus/Sonnet) avec des rôles d'avocat du diable, de vérificateur clinique ou d'architecte UI, puis de synthétiser un consensus sans angle mort.",
        "technical_breakthrough_fr": "L'isolation par `worktree` Git permet à un sous-agent de prototyper ou refactorer une fonctionnalité lourde en arrière-plan pendant que l'agent principal continue de travailler. Le pattern « Council » (analyse indépendante → confrontation croisée → synthèse arbitrée) réduit de plus de 60 % les régressions subtiles sur les gros fichiers `index.html` monolithiques et les pipelines de données.",
        "key_points_fr": [
            "Exécution parallèle asynchrone via `delegate_task` sans bloquer ta session principale.",
            "Confrontation d'architectures complémentaires : Gemini 4 Argon excelle sur le contexte géant (lecture simultanée de plusieurs dépôts et gros JSON) tandis que Claude brille sur la chirurgie fine et la critique éditoriale.",
            "Particulièrement puissant pour vérifier la rigueur médicale de tes fiches RI (`2nd brain`, `BiblioOstéo`) ou auditer la sécurité d'un script financier (`PatrimoineOS`)."
        ],
        "target_projects": ["cochin-os", "biblioosteo", "patrimoine-os", "second-brain"],
        "workflow_how_to_fr": "Tu possèdes déjà le skill `council` installé dans T3 Code ! Dès que tu prends une décision d'architecture importante, que tu veux auditer une fiche de Radiologie Interventionnelle complexe (anticoagulants, fenêtres thérapeutiques) ou refondre une interface, tape simplement le mot-clé `council` dans ton prompt T3 Code.",
        "implementation_steps_fr": [
            "Pour un audit de code ou d'interface : demande un `council` entre Gemini 4 Argon et Claude sur le projet cible.",
            "Pour développer 2 fonctionnalités indépendantes en même temps : demande à l'agent d'utiliser un sous-agent en `worktree` sur la tâche secondaire.",
            "Consulte ton dashboard `Agent Tracking (gemini-ultra)` pour vérifier tes quotas avant de lancer un Council multi-tours."
        ],
        "t3_prompt": "Lance un council pour auditer mes applications médicales COCHIN·OS (/Users/thomaslefevre/.t3/projects/guide-interne-cochin-os) et BiblioOstéo (/Users/thomaslefevre/.t3/projects/biblioosteo) : 1) ergonomie mobile en salle de radiologie, 2) cohérence des données hors-ligne, 3) les 3 améliorations les plus rapides à implanter aujourd'hui."
    },
    {
        "id": "context-caching-2m-monorepo",
        "category_id": "agents_harness",
        "date": "2026-11-04",
        "date_fr": "Novembre 2026",
        "maturity": "🔥 Impact Immédiat",
        "setup_time": "10 min",
        "cost_badge": "Économie ~90 % Tokens (Cache $0.20/M)",
        "source": "Google DeepMind • Gemini 4 Argon & Context Caching",
        "source_url": "https://ai.google.dev/gemini-api/docs/caching",
        "title_fr": "Context Caching implicite & fichiers d'ancrage (`AGENTS.md`) : comment tu économises déjà 80 % de ton quota Google AI Ultra",
        "summary_fr": "Les statistiques de ton daemon `gemini-ultra` montrent que sur 2,52 milliards de tokens traités sur ton compte, 2,34 milliards (92,8 %) proviennent du cache de contexte (soit 4 805 € de valeur API brute pour seulement 928 € de coût théorique caché). Structurer chaque projet avec un fichier `AGENTS.md` concis en racine maximise le taux de hit du cache préfixe et évite à l'agent de ré-explorer l'arborescence à chaque nouveau thread.",
        "technical_breakthrough_fr": "Le cache de préfixe KV (Key-Value) des modèles frontières conserve en mémoire vive les représentations d'attention des premiers blocs du prompt (instructions système, structure du dépôt, schémas de données). Si l'agent connaît immédiatement l'architecture exacte grâce à un `AGENTS.md` de 80 lignes, il passe de 15 appels d'exploration (`ls`, `grep`, `cat`) à 1 seul appel d'édition directe.",
        "key_points_fr": [
            "Sur ton compte Google AI Ultra, ton ratio Cache / Total atteint déjà 92,8 % grâce aux sessions longues T3 Code.",
            "Seuls `2nd brain` et `radio-thomas` possèdent actuellement un fichier `AGENTS.md` / `CLAUDE.md` : les 16 autres projets de `.t3/projects/` n'en ont pas encore.",
            "Ajouter un `AGENTS.md` standardisé dans tes projets phares (`biblioosteo`, `guide-interne-cochin-os`, `finance`, `allinone`) divise par 3 le temps du premier tour de chaque nouveau thread."
        ],
        "target_projects": ["tapp-store-allinone", "biblioosteo", "cochin-os", "patrimoine-os"],
        "workflow_how_to_fr": "Générer automatiquement un fichier `AGENTS.md` ultra-compact dans chacun de tes dépôts actifs décrivant : 1) l'architecture exacte (ex. PWA `index.html` + `data/embedded_data.js`), 2) les commandes de build/déploiement GitHub Pages, et 3) tes règles obligatoires (français médical, Pull-to-Refresh, scroll horizontal trackpad).",
        "implementation_steps_fr": [
            "Définir les 4 règles globales dans chaque `AGENTS.md` : Pull-to-Refresh obligatoire, mise à jour de `embedded_data.js` après toute modif JSON, respect du mode sombre chaud, et zéro dépendance inutile.",
            "Inclure la carte des chemins reliés (ex. lien entre `BiblioOstéo`, `2nd brain` et `Agendainterventionnel`)."
        ],
        "t3_prompt": "Parcours mes projets principaux dans /Users/thomaslefevre/.t3/projects/ (biblioosteo, biblio-marie, guide-interne-cochin-os, guide-infiltration, archive-des-internes, finance, allinone, quiz-image-3) et crée ou mets à jour dans chacun un fichier AGENTS.md concis documentant son architecture exacte, ses scripts de build/synchro et mes standards UI (Pull-to-Refresh, mode sombre, français soigné)."
    },
    {
        "id": "structured-outputs-pubmed-zotero-pipeline",
        "category_id": "rag_biblio_brain",
        "date": "2026-11-03",
        "date_fr": "Novembre 2026",
        "maturity": "⚡ Quick Win (< 20 min)",
        "setup_time": "15 min",
        "cost_badge": "100 % Gratuit (PubMed API + T3 Code)",
        "source": "NCBI E-Utilities + Structured JSON Schema",
        "source_url": "https://www.ncbi.nlm.nih.gov/books/NBK25501/",
        "title_fr": "Veille Bibliographique Zéro-Friction : du PMID ou PDF brut à la fiche complète `BiblioOstéo` / `BiblioMarie` + Zotero + Obsidian en 1 commande",
        "summary_fr": "Aujourd'hui, ajouter un nouvel article dans `BiblioOstéo` ou `BiblioMarie` demande de récupérer les métadonnées PubMed, de rédiger la synthèse structurée en français, d'extraire les paramètres pratiques et de regénérer `embedded_data.js` et les exports `.ris`/`.bib`. En couplant l'API NCBI `efetch` avec une validation JSON Schema stricte, tu peux passer un simple numéro PMID (ou glisser un PDF dans `pdfs/`) et obtenir instantanément la fiche complète prête à déployer.",
        "technical_breakthrough_fr": "Les sorties structurées garanties par grammaire contrainte (Constrained Decoding / JSON Schema) éliminent 100 % des erreurs de syntaxe dans `articles.json` et `editorial.json`. De plus, un même pipeline peut alimenter simultanément ton site web PWA, ta collection Zotero et créer une fiche reliée par `[[Wikilinks]]` dans `/Users/thomaslefevre/2nd brain/05 - Biblio, Zotero & Enseignement`.",
        "key_points_fr": [
            "Extraction automatique du titre, auteurs, revue, DOI, abstract anglais et Date via `eutils.ncbi.nlm.nih.gov`.",
            "Génération simultanée du résumé clinique français, des `key_points_fr`, de l'encadré `En pratique` / `Agenda Cochin` et des tags.",
            "Reconstruction automatique de `data/embedded_data.js` et des fichiers `.ris` / `.bib` sans aucune intervention manuelle."
        ],
        "target_projects": ["biblioosteo", "biblio-marie", "second-brain"],
        "workflow_how_to_fr": "Standardiser une commande unique dans `BiblioOstéo` et `BiblioMarie` : tu donnes simplement à T3 Code un PMID, un DOI ou un sujet (ex. *« Ajoute les 3 derniers articles sur la cryoneurolyse du névrome de Morton »*), et le pipeline met à jour la PWA, Zotero et ton Second Brain.",
        "implementation_steps_fr": [
            "Unifier le script `add_article.py` de `BiblioOstéo` et `build.py` de `BiblioMarie` avec un validateur de schéma JSON.",
            "Ajouter un pont optionnel `--obsidian` qui génère la fiche Markdown correspondante dans `/Users/thomaslefevre/2nd brain/05 - Biblio, Zotero & Enseignement/` avec les bons tags et `[[Wikilinks]]`."
        ],
        "t3_prompt": "Améliore le pipeline d'ajout d'articles de /Users/thomaslefevre/.t3/projects/biblioosteo et /Users/thomaslefevre/.t3/projects/biblio-marie : crée un script unifié qui, à partir d'un ou plusieurs PMIDs, récupère l'abstract complet sur PubMed, valide la fiche JSON française, régénère automatiquement data/embedded_data.js + exports RIS, et crée dans /Users/thomaslefevre/2nd brain/05 - Biblio, Zotero & Enseignement une note Obsidian reliée par [[Wikilinks]]."
    },
    {
        "id": "vlm-pdf-slides-to-quiz-and-index",
        "category_id": "medical_vision",
        "date": "2026-11-03",
        "date_fr": "Novembre 2026",
        "maturity": "🔥 Impact Immédiat",
        "setup_time": "25 min",
        "cost_badge": "100 % Local / Navigateur (PDF.js + Canvas)",
        "source": "Multimodal Vision & PDF.js Pipeline",
        "source_url": "https://mozilla.github.io/pdf.js/",
        "title_fr": "Pipeline Vision « De la Diapo de Staff au Quiz Interactif » : relier `Archives des Internes (07)` et `QUIZ Imagerie (04)`",
        "summary_fr": "Dans `Archives des Internes`, les internes déposent leurs présentations PDF (Bone Club, Cas du mardi, Biblio du vendredi, Cours) qui sont rendues page par page avec PDF.js. Or, chaque présentation de « Cas du mardi » ou « Bone Club » contient exactement ce qu'il faut pour alimenter `QUIZ Imagerie — 1 Image 1 Diag` : une diapo d'imagerie clé et une diapo de diagnostic final !",
        "technical_breakthrough_fr": "Grâce à l'extraction hybride (texte vectoriel PDF.js + rendu Canvas haute résolution d'une diapo sélectionnée ou extraction des objets images embarqués dans le PDF), tu peux transformer n'importe quelle diapo d'archive en un cas de quiz interactif en 1 clic, compressé en WebP/JPEG côté navigateur, sans jamais quitter l'application.",
        "key_points_fr": [
            "Valorise immédiatement les dizaines de cas cliniques présentés par les internes le mardi et le vendredi à Cochin.",
            "Permet dans la visionneuse d'`Archives des Internes` un bouton « 🎯 Créer un Quiz depuis cette diapo » qui pré-remplit le diagnostic et l'image pour `QUIZ Imagerie`.",
            "Anonyme par construction : possibilité de rogner (crop) en 1 geste le bandeau supérieur d'une image directement dans le navigateur avant export."
        ],
        "target_projects": ["archive-des-internes", "quiz-imagerie", "cochin-os"],
        "workflow_how_to_fr": "Ajouter dans la visionneuse de `Archives des Internes` un bouton d'export direct vers le format JSON du `#/studio` de `QUIZ Imagerie (quiz-image-3)` avec outil de recadrage d'anonymisation intégré.",
        "implementation_steps_fr": [
            "Dans la visionneuse PDF d'`archive-des-internes`, ajouter un bouton « 🎯 Envoyer cette diapo vers Quiz Imagerie ».",
            "Permettre de sélectionner une zone rectangulaire sur la diapo (pour isoler l'IRM/TDM/Radio sans le texte autour ni aucun élément identifiant).",
            "Copier ou exporter directement l'objet JSON prêt à coller dans `#/studio` de `quiz-image-3`."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/archive-des-internes, ajoute dans la visionneuse de diapos PDF un outil « 🎯 Extraire vers Quiz Imagerie » permettant de recadrer une image radiologique présente sur la diapo courante, de récupérer automatiquement le diagnostic du dossier et de copier/télécharger le cas au format JSON compatible avec le Studio (#/studio) de /Users/thomaslefevre/.t3/projects/quiz-image-3."
    },
    {
        "id": "webgpu-local-embeddings-semantic-search",
        "category_id": "local_first_webgpu",
        "date": "2026-11-02",
        "date_fr": "Novembre 2026",
        "maturity": "⚡ Quick Win (< 30 min)",
        "setup_time": "20 min",
        "cost_badge": "0 € • Exécution 100 % statique (GitHub Pages)",
        "source": "WebGPU / Recherche Hybride BM25 + Synonymes Médicaux",
        "source_url": "https://huggingface.co/docs/transformers.js",
        "title_fr": "Recherche Sémantique & Tolérance Médicale Hors-Ligne sur GitHub Pages (sans serveur backend)",
        "summary_fr": "La quasi-totalité de tes applications (`BiblioOstéo`, `BiblioMarie`, `Guide Infiltrations`, `COCHIN·OS`) sont hébergées gratuitement en statique sur GitHub Pages. Or, une recherche par `includes()` classique échoue si l'utilisateur tape « algodystrophie » au lieu de « SDRC », « cotyle » au lieu de « acétabulum », « KOA » au lieu de « kyste osseux anévrismal », ou fait une faute de frappe en salle d'intervention.",
        "technical_breakthrough_fr": "Deux approches complémentaires fonctionnent aujourd'hui 100 % en statique sur GitHub Pages : 1) Un moteur hybride **BM25 + Graphe de synonymes médicaux ostéo-articulaires + distance de Levenshtein** (0 Ko de modèle à télécharger, latence < 1 ms sur mobile), ou 2) Des **embeddings pré-calculés au build** dans `scripts/build_*.py` (vecteurs quantifiés int8 de 256 dimensions ne pesant que ~30 Ko pour 100 fiches) permettant une vraie recherche par sens clinique.",
        "key_points_fr": [
            "Zéro serveur, zéro clé API exposée côté client, 100 % compatible avec le mode hors-ligne de l'hôpital (sous-sol Achard -1).",
            "Tu as déjà implanté une validation souple par synonymes dans `QUIZ Imagerie (quiz-image-3)` : ce même moteur peut propulser la recherche de `BiblioOstéo`, `Guide Infiltrations` et `BiblioMarie`.",
            "Permet de trouver une fiche du `Guide Infiltrations` en tapant un symptôme ou un repère anatomique synonyme (ex. « épine sciatique », « nerf pudendal », « Rhizarthrose » → « Trapézo-métacarpienne »)."
        ],
        "target_projects": ["guide-infiltration", "biblioosteo", "biblio-marie", "cochin-os"],
        "workflow_how_to_fr": "Intégrer un moteur de recherche floue + thésaurus médical français/anglais partagé dans `Guide Infiltrations` (75 procédures), `BiblioOstéo` et `BiblioMarie`.",
        "implementation_steps_fr": [
            "Normaliser les accents, ligatures (`œ` → `oe`, `é` → `e`) et expandir automatiquement les abréviations médicales (`OO`, `KOA`, `KOE`, `ECT`, `RF`, `MCP`, `MTP`, `TFCC`, `SDRC`, `VRS`, `IOA`).",
            "Classer les résultats par score de pertinence (titre > tags > indication > corps de texte) plutôt que par simple filtre booléen."
        ],
        "t3_prompt": "Améliore le moteur de recherche de /Users/thomaslefevre/.t3/projects/guide-infiltration et /Users/thomaslefevre/.t3/projects/biblioosteo en ajoutant une normalisation sans accents, une tolérance aux fautes de frappe et un dictionnaire de synonymes ostéo-articulaires & RI (ex. rhizarthrose ↔ trapézo-métacarpienne, KOA ↔ kyste anévrismal, OO ↔ ostéome ostéoïde, cotyle ↔ hanche) fonctionnant 100 % hors-ligne."
    },
    {
        "id": "ambient-voice-radiology-cr-types",
        "category_id": "voice_automation_iot",
        "date": "2026-11-01",
        "date_fr": "Novembre 2026",
        "maturity": "🧪 Haute Valeur Clinique",
        "setup_time": "30 min",
        "cost_badge": "100 % Local & Anonyme",
        "source": "Structured Clinical Reporting & CR-Types",
        "source_url": "https://rsna.org/practice-tools/data-tools-and-standards/radreport-reporting-templates",
        "title_fr": "Générateur de Comptes-Rendus Types (CR-Types RI & Imagerie Ostéo) interactif relié à ton `Second Brain`",
        "summary_fr": "Le dossier `03 - Imagerie Diagnostique & CR-Types` et `02 - Radiologie Interventionnelle (RI)` de ton Second Brain Obsidian a vocation à centraliser tes comptes-rendus types (arthroscanner d'épaule, IRM de sarcome, CR opératoire de cryoablation de tumeur desmoïde, radiofréquence d'ostéome ostéoïde, biopsie osseuse sous scanner, infiltration foraminale).",
        "technical_breakthrough_fr": "Au lieu de copier-coller des textes statiques et d'oublier de modifier un côté (droit/gauche) ou une taille d'aiguille, un **compositeur de CR-Types à variables dynamiques** (chips cliquables en 1 tap + dictée de quelques mots-clés : ex. *« Ostéome ostéoïde tibia droit, nidus 6 mm, sonde RF 17G active tip 7 mm, 6 min à 90°C, sans complication »*) génère instantanément le compte-rendu opératoire formaté selon les standards de Cochin Radio B, prêt à être collé dans le RIS.",
        "key_points_fr": [
            "Zéro donnée patient stockée (100 % conforme RGPD AP-HP : seules les variables techniques de l'acte sont assemblées en mémoire).",
            "Boutons rapides pour les paramètres récurrents à Cochin : jauge du trocart, nombre de prélèvements microbiologiques/anatomopathologiques, respect du compartiment en concertation chirurgicale, dose de bléomycine ou cycles d'argon.",
            "Synchronisable directement depuis tes fichiers Markdown de `/Users/thomaslefevre/2nd brain/`."
        ],
        "target_projects": ["second-brain", "cochin-os", "guide-infiltration"],
        "workflow_how_to_fr": "Créer une mini-application ou un module dans `COCHIN·OS` / `Second Brain` permettant de générer en 10 secondes un CR opératoire de RI ou un CR diagnostique ostéo-articulaire irréprochable, copié dans le presse-papiers en 1 clic.",
        "implementation_steps_fr": [
            "Structurer les modèles de CR dans `/Users/thomaslefevre/2nd brain/03 - Imagerie Diagnostique & CR-Types/` avec des variables rapides (`{{cote}}`, `{{cible}}`, `{{materiel}}`, `{{anesthesie}}`).",
            "Générer une interface web locale/PWA à boutons rapides (« Côté D / G », « AL / AG », « Trocart Bonopty / Ostycut / Coaxial », « RF / Cryo / Cimentoplastie / Biopsie / Infiltration ») qui copie le CR finalisé."
        ],
        "t3_prompt": "À partir de mes notes dans /Users/thomaslefevre/2nd brain/02 - Radiologie Interventionnelle (RI) et 03 - Imagerie Diagnostique & CR-Types, crée un générateur interactif de Comptes-Rendus Types (RI & Ostéo-Articulaire Cochin) permettant de sélectionner en quelques clics le geste (biopsie osseuse/parties molles, RF ostéome ostéoïde, cryoablation desmoïde, cimentoplastie, infiltration rachis/périphérique), les paramètres techniques et de copier le CR complet prêt pour le RIS hospitalier."
    },
    {
        "id": "local-sqlite-ai-finance-categorizer",
        "category_id": "local_first_webgpu",
        "date": "2026-10-31",
        "date_fr": "Octobre 2026",
        "maturity": "⚡ Quick Win (< 25 min)",
        "setup_time": "20 min",
        "cost_badge": "100 % Local • SQLite (`finance.db`)",
        "source": "Local-First Finance & Deterministic + LLM Rules",
        "source_url": "https://sqlite.org",
        "title_fr": "Intelligence Financière Locale dans `PatrimoineOS` : catégorisation hybride SQLite & simulation de réallocation",
        "summary_fr": "Ton application `PatrimoineOS` (`/Users/thomaslefevre/.t3/projects/finance`) agrège déjà en lecture seule et 100 % en local (SQLite `better-sqlite3`) tes comptes Crédit Mutuel (DSP2 GoCardless / CSV), tes wallets MetaMask & Ledger sur 6 chaînes EVM et ta collection Pokémon Collectr. C'est l'architecture idéale pour brancher une analyse financière intelligente sans jamais envoyer un seul relevé bancaire dans le cloud.",
        "technical_breakthrough_fr": "Le pattern **Rule-Engine SQLite + Enrichissement local** consiste à associer des expressions régulières déterministes aux libellés bancaires récurrents (salaires AP-HP/gardes, Pajemploi AssMat, impôts, abonnements, virements d'épargne PEA/Livret) et à stocker l'historique journalier de tes 3 piliers pour calculer automatiquement ton taux d'épargne, ton exposition par classe d'actifs (Cash / Actions PEA / Crypto Cold vs Hot / Pokémon Scellés vs Cartes) et tes alertes de rééquilibrage.",
        "key_points_fr": [
            "Confidentialité totale : tout reste dans `/Users/thomaslefevre/.t3/projects/finance/data/finance.db` sur ton Mac.",
            "Détection automatique des revenus de gardes / astreintes et des charges fixes mensuelles.",
            "Suivi de la répartition de sécurité Cold Wallet (Ledger) vs Hot Wallet (MetaMask) et de la performance en EUR de ta collection Pokémon Collectr."
        ],
        "target_projects": ["patrimoine-os"],
        "workflow_how_to_fr": "Ajouter dans `PatrimoineOS` un module d'analyse mensuelle automatique (Cashflow, Taux d'épargne, Répartition des 3 piliers et Historique Net Worth) directement propulsé par SQLite.",
        "implementation_steps_fr": [
            "Ajouter la table `net_worth_history` dans SQLite enregistrant à chaque synchronisation la valeur EUR de la Banque, de la Crypto et de Collectr.",
            "Ajouter un classifieur automatique des libellés Crédit Mutuel avec badges visuels et graphique de répartition mensuelle."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/finance, enrichis PatrimoineOS avec : 1) l'enregistrement automatique dans SQLite (data/finance.db) d'un snapshot d'historique à chaque synchronisation des 3 piliers (Crédit Mutuel, Crypto EVM, Pokémon Collectr), 2) un graphique d'évolution du patrimoine net, et 3) la catégorisation intelligente automatique des transactions Crédit Mutuel."
    },
    {
        "id": "python-macos-daemons-cross-project-bridge",
        "category_id": "voice_automation_iot",
        "date": "2026-10-30",
        "date_fr": "Octobre 2026",
        "maturity": "🔥 Impact Immédiat",
        "setup_time": "20 min",
        "cost_badge": "100 % Local macOS",
        "source": "macOS Local Automation & Cross-Repo Sync",
        "source_url": "https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html",
        "title_fr": "Unifier tes scripts Python macOS (`sync_sheet`, `sync_family_agenda`, `gemini_ultra_daemon`) en un tableau de bord unique",
        "summary_fr": "En explorant l'ensemble de tes projets sur ton Mac, on découvre que tu as construit une vraie flotte d'agents Python locaux : `sync_sheet.py` et `fetch_imessages.py` dans `Agendainterventionnel`, `build_internes_data.py` dans `planning-interne`, `sync_family_agenda.py` dans `agenda-famille`, `gemini_ultra_daemon.py` et `sync_projects.py` dans `allinone`, `build_biblio_database.py` dans `biblioosteo`, `build.py` dans `biblio-marie`, et `process_takeout.py` dans `photo`.",
        "technical_breakthrough_fr": "Plutôt que de lancer manuellement des fichiers `.command` dispersés dans `Documents/` et `.t3/projects/`, un orchestrateur local léger (ou un panneau dans `Tapp Store / Agent Tracking`) peut vérifier l'état de fraîcheur de chaque source de données (dernière synchro Google Sheet Cochin, dernier build Biblio, dernier push GitHub Pages, statut du daemon Gemini Ultra et Forestia) et tout synchroniser en 1 clic.",
        "key_points_fr": [
            "Visibilité immédiate sur la date de dernière mise à jour de chacun de tes 20+ projets.",
            "Synchronisation en cascade : une mise à jour de ton planning de garde Cochin peut mettre à jour simultanément `Cochin RI`, `Agenda Famille` et ton briefing `Second Brain`.",
            "Zéro oubli de régénération de `embedded_data.js` avant un push GitHub Pages."
        ],
        "target_projects": ["tapp-store-allinone", "agenda-interventionnel", "family-daily-apps", "biblioosteo"],
        "workflow_how_to_fr": "Créer un script maître `sync_all_ecosystem.py` (ou l'intégrer au daemon local `127.0.0.1:8787`) qui vérifie l'état Git et la fraîcheur des données de tous tes projets en 2 secondes.",
        "implementation_steps_fr": [
            "Lister tous tes dépôts actifs (`/Users/thomaslefevre/.t3/projects/*` et `/Users/thomaslefevre/Documents/*`).",
            "Vérifier pour chacun s'il y a des modifications locales non commitées ou des fichiers JSON plus récents que `embedded_data.js`.",
            "Permettre une synchronisation globale en 1 commande."
        ],
        "t3_prompt": "Crée dans /Users/thomaslefevre/.t3/projects/allinone/scripts/ un script ecosystem_status.py qui inspecte tous mes projets (/Users/thomaslefevre/.t3/projects/* et /Users/thomaslefevre/Documents/Agendainterventionnel, planning-interne, agenda-famille, radio-thomas), vérifie leur statut Git, la fraîcheur des fichiers embedded_data.js et l'état des daemons locaux."
    },
    {
        "id": "custom-mcp-server-cochin-ecosystem",
        "category_id": "agents_harness",
        "date": "2026-10-29",
        "date_fr": "Octobre 2026",
        "maturity": "🧪 Architecture / Haute Valeur",
        "setup_time": "25 min",
        "cost_badge": "0 € • Serveur MCP Python/Node Local",
        "source": "Model Context Protocol (MCP) • Lazy Tools",
        "source_url": "https://modelcontextprotocol.io",
        "title_fr": "Serveur MCP personnel « Cochin & Biblio » : donner à tes agents un accès natif typé à Zotero, PubMed et ton Planning RI",
        "summary_fr": "Au lieu que chaque agent T3 Code ou Claude Code doive deviner où se trouvent tes scripts Python (`sync_sheet.py`, `zotero_sync.py`, `add_article.py`), un micro-serveur MCP local de 120 lignes expose 4 outils typés : `search_biblio_cochin`, `get_ri_schedule`, `add_pubmed_to_biblio` et `search_second_brain`.",
        "technical_breakthrough_fr": "Avec le chargement paresseux (Lazy Tool Loading) des schémas MCP, exposer tes propres outils locaux ne consomme aucun token de contexte tant que l'agent n'en a pas besoin, mais garantit que n'importe quel thread (même ouvert depuis un autre projet) peut interroger instantanément ton planning de garde, ta base Zotero ou tes 75 fiches d'infiltrations.",
        "key_points_fr": [
            "Accessible depuis n'importe quel workspace T3 Code ou Claude Desktop sans copier de chemins absolus.",
            "Sécurité garantie : le serveur MCP tourne en `stdio` local sur ton Mac et applique automatiquement tes filtres d'anonymisation RGPD.",
            "Permet de croiser en 1 question : *« Quels sont mes gestes de RI demain et quels articles de BiblioOstéo s'y rapportent ? »*"
        ],
        "target_projects": ["agenda-interventionnel", "biblioosteo", "second-brain", "cochin-os"],
        "workflow_how_to_fr": "Créer un serveur MCP léger en Python (`cochin_mcp_server.py`) qui expose en lecture/écriture propre tes bases JSON locales (`BiblioOstéo`, `BiblioMarie`, `Guide Infiltrations`, `Planning RI` et `Second Brain`).",
        "implementation_steps_fr": [
            "Écrire un script Python MCP standard exposant `get_cochin_schedule`, `lookup_infiltration_sheet`, `search_biblio` et `create_obsidian_note`.",
            "L'enregistrer dans ta configuration MCP locale pour que tous tes agents y aient accès nativement."
        ],
        "t3_prompt": "Crée un serveur MCP Python local (cochin_mcp_server.py) qui expose en outils typés : 1) la recherche dans les 75 fiches de /Users/thomaslefevre/.t3/projects/guide-infiltration/guide-data.json, 2) la recherche dans /Users/thomaslefevre/.t3/projects/biblioosteo/data/articles.json et biblio-marie, 3) la lecture du planning /Users/thomaslefevre/Documents/Agendainterventionnel/cochin_planning.json, et 4) la recherche dans /Users/thomaslefevre/2nd brain."
    },
    {
        "id": "client-side-dicom-windowing-presets-ai",
        "category_id": "medical_vision",
        "date": "2026-10-28",
        "date_fr": "Octobre 2026",
        "maturity": "⚡ Quick Win (< 20 min)",
        "setup_time": "15 min",
        "cost_badge": "100 % Client-Side (Canvas / WebGL)",
        "source": "Radiological Histogram Auto-Windowing & CLAHE",
        "source_url": "https://cornerstonejs.org",
        "title_fr": "Auto-Fenêtrage intelligent par analyse d'histogramme & Presets Ostéo/Parties Molles dans `QUIZ Imagerie` et `Archives`",
        "summary_fr": "Sur des captures JPEG/PNG/WebP ou des PDF de présentations (contrairement au DICOM brut 16-bits de `TPack PACS`), le réglage manuel de luminosité/contraste perd souvent du détail dans les corticales osseuses ou l'œdème médullaire STIR/T2 Fat-Sat. L'analyse automatique des percentiles d'histogramme (`P2–P98`) + l'égalisation adaptative locale (CLAHE en WebGL/Canvas) permet d'offrir 3 boutons de presets instantanés : `🦴 Os / Corticale`, `🥩 Parties Molles`, et `⚡ Rehaussement Nidus / STIR`.",
        "technical_breakthrough_fr": "En calculant à la volée la courbe de transfert (LUT 256 valeurs) sur les pixels de la région d'intérêt (en excluant le fond noir radiologique `< 12`), on simule un fenêtrage radiologique bluffant même sur des images 8-bits issues du presse-papiers (`Cmd+V`) ou d'une diapo PDF.",
        "key_points_fr": [
            "Améliore immédiatement le confort visuel sur mobile dans `QUIZ Imagerie (quiz-image-3)` et la visionneuse d'`Archives des Internes`.",
            "1 tap sur `🦴 Os` ou `🧲 STIR/T2` au lieu de glisser manuellement deux curseurs sur petit écran.",
            "Zéro latence : calcul de la LUT en moins de 2 millisecondes en JavaScript pur."
        ],
        "target_projects": ["quiz-imagerie", "archive-des-internes", "dicomviewer-radio-thomas"],
        "workflow_how_to_fr": "Ajouter 3 boutons de presets radiologiques intelligents (`Os`, `Parties Molles`, `Auto-Contraste CLAHE`) dans la barre d'outils de la visionneuse de `QUIZ Imagerie` et d'`Archives des Internes`.",
        "implementation_steps_fr": [
            "Calculer l'histogramme de luminance de l'image active en ignorant les bordures noires.",
            "Ajouter les presets 1-tap dans la barre de contrôle de la visionneuse à côté du bouton Négatif/Positif."
        ],
        "t3_prompt": "Dans la visionneuse radiologique de /Users/thomaslefevre/.t3/projects/quiz-image-3 et /Users/thomaslefevre/.t3/projects/archive-des-internes, ajoute 3 presets de fenêtrage instantanés en 1 tap (🦴 Os/Corticale, 🧲 Parties Molles/STIR, ✨ Auto-Histogramme) basés sur l'analyse des percentiles de l'image."
    },
    {
        "id": "esp32-xiaozhi-medical-desk-companion",
        "category_id": "voice_automation_iot",
        "date": "2026-10-26",
        "date_fr": "Octobre 2026",
        "maturity": "🧪 Fun & Hardware",
        "setup_time": "30 min",
        "cost_badge": "Local Wi-Fi / WebSocket",
        "source": "ESP32-S3 AMOLED 1.8\" • WebSocket Voice Agent",
        "source_url": "https://github.com/78/xiaozhi-esp32",
        "title_fr": "Connecter ton boîtier `xiaozhi-esp32-amoled-1.8` à ton Agenda Famille, tes Quotas IA et tes Rappels de Garde",
        "summary_fr": "Tu as dans tes projets `/Users/thomaslefevre/Documents/antigravity/xiaozhi-esp32-amoled-1.8`. Cet écran AMOLED 1.8\" sur ESP32-S3 peut faire bien plus qu'un chatbot vocal générique : branché sur ton daemon local Mac mini (`127.0.0.1:8787` / réseau local `192.168.1.111`), il devient un afficheur de bureau temps réel (Prochaine garde Cochin, planning Mabrouka du lendemain, jauge Google AI Ultra / Claude Pro, ou minuteur de révision).",
        "technical_breakthrough_fr": "Le firmware Xiaozhi supporte les outils MCP (via WebSocket) et l'affichage de widgets personnalisés sur l'écran AMOLED. En lui exposant un endpoint JSON léger sur ton Mac (`192.168.1.111`), il répond vocalement à *« Qui est de garde demain ? »* ou *« À quelle heure arrive Mabrouka jeudi ? »* en lisant directement `family_data.json` et `cochin_gardes.json`.",
        "key_points_fr": [
            "Réutilise l'infrastructure réseau local que tu as déjà mise en place pour `M4 Gaming` (`192.168.1.111:8765`) et `Forestia Mobile` (`192.168.1.111:8790`).",
            "Consultation vocale ou visuelle en un coup d'œil sans sortir le téléphone.",
            "100 % sur ton Wi-Fi domestique."
        ],
        "target_projects": ["family-daily-apps", "tapp-store-allinone", "agenda-interventionnel"],
        "workflow_how_to_fr": "Exposer sur ton daemon Python local une route `/api/desk-summary` renvoyant la météo du planning familial, la prochaine garde Cochin et le quota IA restant pour ton ESP32 AMOLED.",
        "implementation_steps_fr": [
            "Inspecter la configuration actuelle de `/Users/thomaslefevre/Documents/antigravity/xiaozhi-esp32-amoled-1.8`.",
            "Ajouter un endpoint JSON compact dans ton daemon local sur `192.168.1.111`."
        ],
        "t3_prompt": "Inspecte /Users/thomaslefevre/Documents/antigravity/xiaozhi-esp32-amoled-1.8 et crée un endpoint local sur mon Mac qui lui fournit le résumé de mon Agenda Famille (/Users/thomaslefevre/Documents/agenda-famille/family_data.json), mes prochaines gardes Cochin et mon quota Gemini Ultra / Claude en direct."
    }
]



def fetch_live_signals() -> list[dict]:
    """Récupère en direct les dernières actualités techniques IA (Hacker News Algolia + ArXiv API)."""
    live_items: list[dict] = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Hacker News Algolia API (LLM / MCP / Coding Agents / Medical AI)
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date?query=LLM&tags=story&numericFilters=points%3E20&hitsPerPage=8"
        req = urllib.request.Request(url, headers={"User-Agent": "NewsAI-ThomasLefevre/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for hit in data.get("hits", []):
                title = hit.get("title") or ""
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                created = (hit.get("created_at") or "")[:10]
                live_items.append({
                    "id": f"hn-{hit.get('objectID')}",
                    "source": "Hacker News Tech",
                    "badge": f"▲ {points} pts · 💬 {comments}",
                    "date": created,
                    "title": title,
                    "url": story_url,
                    "discuss_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "fetched_at": now_iso
                })
    except Exception as exc:
        print(f"[warn] HN live fetch skipped: {exc}")

    # 2. ArXiv API (Medical Imaging AI & Multimodal Agents)
    try:
        query = urllib.parse.quote('cat:eess.IV OR (cat:cs.CV AND all:"medical imaging") OR (cat:cs.AI AND all:"agent")')
        arxiv_url = f"https://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results=6"
        req = urllib.request.Request(arxiv_url, headers={"User-Agent": "NewsAI-ThomasLefevre/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("a:entry", ns):
                title = " ".join((entry.findtext("a:title", "", ns) or "").split())
                summary = " ".join((entry.findtext("a:summary", "", ns) or "").split())
                link = entry.findtext("a:id", "", ns)
                published = (entry.findtext("a:published", "", ns) or "")[:10]
                if title and link:
                    live_items.append({
                        "id": f"arxiv-{link.rsplit('/', 1)[-1]}",
                        "source": "ArXiv Preprint",
                        "badge": "📄 Paper IA / Imagerie",
                        "date": published,
                        "title": title,
                        "summary": summary[:280] + ("…" if len(summary) > 280 else ""),
                        "url": link,
                        "discuss_url": link,
                        "fetched_at": now_iso
                    })
    except Exception as exc:
        print(f"[warn] ArXiv live fetch skipped: {exc}")

    return live_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Build News AI data files")
    parser.add_argument("--fetch-live", action="store_true", help="Fetch live HN & ArXiv AI news")
    args = parser.parse_args()

    live_signals: list[dict] = []
    live_file = DATA_DIR / "live_signals.json"
    if args.fetch_live:
        live_signals = fetch_live_signals()
        if live_signals:
            live_file.write_text(json.dumps(live_signals, ensure_ascii=False, indent=2), encoding="utf-8")
    elif live_file.exists():
        try:
            live_signals = json.loads(live_file.read_text(encoding="utf-8"))
        except Exception:
            live_signals = []

    built_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    news_file = DATA_DIR / "news.json"
    projects_file = DATA_DIR / "projects.json"
    categories_file = DATA_DIR / "categories.json"
    embedded_file = DATA_DIR / "embedded_data.js"

    news_file.write_text(json.dumps(NEWS_ITEMS, ensure_ascii=False, indent=2), encoding="utf-8")
    projects_file.write_text(json.dumps(PROJECTS, ensure_ascii=False, indent=2), encoding="utf-8")
    categories_file.write_text(json.dumps(CATEGORIES, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "builtAt": built_at,
        "categories": CATEGORIES,
        "projects": PROJECTS,
        "news": NEWS_ITEMS,
        "liveSignals": live_signals
    }

    js_content = (
        "// Fichier généré automatiquement par scripts/build_data.py — Ne pas modifier à la main\n"
        f"window.NEWS_AI_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
    )
    embedded_file.write_text(js_content, encoding="utf-8")
    print(f"✓ Base construite : {len(NEWS_ITEMS)} fiches techniques, {len(PROJECTS)} ensembles de projets, {len(live_signals)} signaux live.")


if __name__ == "__main__":
    main()
