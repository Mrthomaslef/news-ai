#!/usr/bin/env python3
"""
Générateur & Synchroniseur de la base News AI (@Mrthomaslef) — Vraies Avancées Technologiques & Nouvelles Méthodes IA.
- Construit `data/news.json`, `data/projects.json`, `data/categories.json` et `data/embedded_data.js`
- Option `--fetch-live` : interroge en direct :
  1. Hugging Face Daily Papers API (`https://huggingface.co/api/daily_papers`)
  2. ArXiv API (`cs.AI`, `cs.CL`, `cs.CV`, `eess.IV`)
  3. Hacker News Algolia API filtré strictement sur les publications IA / ML / LLM / Papers.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    {
        "id": "rl_reasoning_methods",
        "label": "🧠 Raisonnement, RL & Post-Training (GRPO, Test-Time Compute)",
        "short": "🧠 RL & Raisonnement",
        "description": "Algorithmes d'apprentissage par renforcement à récompenses vérifiables (GRPO, RLVR), émergence de la chaîne de pensée sans SFT et mise à l'échelle du calcul à l'inférence."
    },
    {
        "id": "multimodal_rag_graphs",
        "label": "📚 RAG Visuel & Graphes de Mémoire (ColPali, HippoRAG 2, LightRAG)",
        "short": "📚 ColPali & GraphRAG",
        "description": "Indexation tardive de patchs visuels (ColBERT + VLM sans OCR) et mémoire associative sur graphe via Personalized PageRank."
    },
    {
        "id": "medical_foundation_vlm",
        "label": "🩻 Modèles Fondations Médicaux 2D/3D (MedSAM 2, MedGemma)",
        "short": "🩻 MedSAM 2 & MedGemma",
        "description": "Segmentation volumétrique 3D TDM/IRM par mémoire d'attention streaming et VLM cliniques entraînés par RL multimodal."
    },
    {
        "id": "inference_grammar_edge",
        "label": "⚡ Inférence, Décodage & Edge (EAGLE-3, XGrammar-2, Kokoro WebGPU, MLX)",
        "short": "⚡ Décodage & WebGPU",
        "description": "Décodage spéculatif par fusion de couches cachées (EAGLE-3), automates à pile pour JSON/outils (XGrammar-2) et synthèse/inférence locale Apple Silicon & WebGPU."
    },
    {
        "id": "agentic_protocols_swe",
        "label": "🤖 Ingénierie Agentique & Protocoles (Agentless, SWE-bench, CA-MCP)",
        "short": "🤖 Agentless & MCP",
        "description": "Localisation hiérarchique déterministe vs agents autonomes (Agentless), Context-Aware MCP et Context Rot en fenêtre longue."
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
                "title": "Recherche fédérée Omnibox (⌘K) hybride (BM25 + Synonymes Médicaux)",
                "impact": "Quick Win",
                "detail": "Appliquer la méthode de recherche hybride lexicale + expansion de synonymes sur les 75 fiches du Guide Infiltrations, l'Annuaire Cochin et BiblioOstéo depuis un champ unique.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/guide-interne-cochin-os, ajoute une barre de recherche universelle (Omnibox ⌘K et bouton mobile) utilisant un score BM25 + dictionnaire de synonymes ostéo-articulaires qui indexe en local les postes de ./annuaire/, les 75 fiches de ./infiltrations/guide-data.json et les articles de BiblioOstéo."
            },
            {
                "title": "Assistant « Garde & Prise de Poste » déterministe (Arbre Anticoagulants & RI)",
                "impact": "Haute Valeur",
                "detail": "Arbre de décision instantané hors-ligne pour l'interne (fenêtres d'arrêt Eliquis/Plavix avant geste RI profonde vs superficielle, prémédication allergie iode, numéros DECT Achard/Ollier).",
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
                "title": "Décodage contraint par grammaire (JSON Schema strict type XGrammar / Outlines) dans add_article.py",
                "impact": "Quick Win",
                "detail": "Forcer l'extraction d'un PMID ou d'un PDF médical selon un schéma Pydantic/JSON Schema strict garantissant 0 erreur sur les champs cliniques (`protocol_fr`, `cochin_link`, `key_points_fr`) et la création simultanée de la fiche Obsidian.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblioosteo/scripts/add_article.py, implante un validateur de schéma JSON strict (style Constrained Decoding / Pydantic) qui prend un PMID ou PDF local, récupère PubMed E-Utilities, génère la fiche structurée sans hallucination de format, reconstruit data/embedded_data.js et crée la note reliée dans /Users/thomaslefevre/2nd brain/05 - Biblio, Zotero & Enseignement."
            },
            {
                "title": "Matrice comparative des paramètres opératoires RI extraits de la littérature",
                "impact": "Moyen Terme",
                "detail": "Vue tableau synthétique croisant les 24+ articles sur les paramètres physiques exacts (puissance RF, cycles d'argon cryoablation, fenêtre bléomycine 8–40 min, calibre trocart).",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblioosteo/index.html, ajoute un onglet « ⚡ Matrice Protocoles RI » qui synthétise sous forme de tableau filtrable les paramètres techniques extraits de chaque article (indication, matériel, protocole thermique/chimique, suivi)."
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
                "title": "Synthèse vocale neuronale locale Kokoro-82M WebGPU / TTS (« Podcast Biblio 2 min »)",
                "impact": "Quick Win",
                "detail": "Intégrer la lecture audio fluide de la synthèse française et du bloc « En pratique » dans le lecteur d'article (via Kokoro-82M ONNX WebGPU ou Web Speech API en fallback instantané).",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblio-marie/index.html, ajoute dans la barre du lecteur d'article un bouton « 🎧 Écouter la synthèse » qui lit le titre, le résumé et l'encadré 'En pratique' avec contrôle de vitesse (1x, 1.25x, 1.5x) et intègre le standard Pull-to-Refresh mobile."
            },
            {
                "title": "Scanner automatique PubMed E-Utilities sur les essais randomisés & recos GPIP / SPILF",
                "impact": "Quick Win",
                "detail": "Script Python interrogeant NCBI sur les publications à fort Impact Factor en infectiologie pédiatrique et pré-structurant les fiches dans `data/editorial.json`.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/biblio-marie/scripts/, crée un script discover_pubmed.py qui interroge l'API NCBI E-utilities sur les essais cliniques et guidelines récents en infectiologie pédiatrique (GPIP, SPILF, VRS, sepsis, IOA) et pré-remplit les candidats à valider pour data/editorial.json."
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
                "title": "Indexation Visuelle par Patchs (méthode ColPali / Late Interaction) sur les diapos PDF",
                "impact": "Haute Valeur",
                "detail": "Les diapos de radiologie contiennent souvent des coupes IRM/TDM annotées de flèches ou des tableaux de classification que l'OCR texte classique manque. L'indexation multimodale de la miniature de chaque diapo permet de retrouver visuellement une diapo précise.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/archive-des-internes, enrichis le pipeline d'indexation PDF.js pour extraire à la fois le texte structuré de chaque diapo et permettre d'exporter en 1 clic une diapo d'imagerie recadrée vers /Users/thomaslefevre/.t3/projects/quiz-image-3."
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
                "title": "Évaluation par Récompense Vérifiable (méthode RLVR / DeepSeek-R1) & Décomposition Sémiologique",
                "impact": "Haute Valeur",
                "detail": "Inspiré du paradigme RLVR (Reinforcement Learning with Verifiable Rewards) : décomposer la validation d'un cas en 3 sous-récompenses vérifiables (1. Anomalie élémentaire / signe radiologique, 2. Topographie exacte, 3. Diagnostic étiologique) avec indice progressif si l'interne trouve la lésion mais pas l'éponyme.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/quiz-image-3, enrichis le moteur de validation souple et le Studio (#/studio) pour supporter une validation graduée en 2 paliers : détection des signes sémiologiques clés (indice débloqué si le signe est bon) puis validation du diagnostic final avec génération automatique des synonymes."
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
                "title": "Extraction structurée des paramètres salle (Aiguille, Cible, Produit, Incidence) en bandeau haut",
                "impact": "Quick Win",
                "detail": "Synthétiser en haut de chacune des 75 fiches les 4 constantes opératoires extraites du texte pour une lecture en 2 secondes en salle de radiologie.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/guide-infiltration, ajoute en haut de chaque procédure un encart résumé « Plateau & Paramètres Clés » (Aiguille, Produit, Position, Cible) extrait de guide-data.json."
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
                "title": "Mémoire Associative par Personalized PageRank sur tes [[Wikilinks]] (méthode HippoRAG 2)",
                "impact": "Haute Valeur",
                "detail": "Appliquer l'algorithme de marche aléatoire biaisée (Personalized PageRank de HippoRAG 2, NeurIPS/2025) directement sur le graphe de tes notes Obsidian + articles BiblioOstéo pour retrouver en 1 requête multi-sauts toutes les notes liées à un cas de RCP complexe.",
                "prompt": "Crée un script Python hipporag_obsidian.py dans /Users/thomaslefevre/2nd brain qui construit le graphe d'adjacence de toutes mes notes Markdown ([[Wikilinks]], tags YAML) et des articles de /Users/thomaslefevre/.t3/projects/biblioosteo/data/articles.json, puis exécute un Personalized PageRank pour trouver les notes et références cliniques les plus connectées à une requête médicale."
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
                "title": "Propagation 3D de ROI / Segmentation inter-coupes (méthode MedSAM 2 Memory Attention)",
                "impact": "Haute Valeur",
                "detail": "Lorsqu'on prépare un cas clinique `.tpack` sur un volume scanner ou IRM, pointer une lésion osseuse ou des parties molles sur 1 seule coupe centrale et propager automatiquement le masque ou la boîte englobante sur les coupes adjacentes.",
                "prompt": "Dans /Users/thomaslefevre/Documents/dicomviewer, ajoute un outil d'annotation rapide permettant de pointer une lésion sur une coupe clé, de propager/interpoler le contour sur les coupes adjacentes du volume et d'exporter une coupe annotée vers QUIZ Imagerie."
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
                "title": "Serveur MCP Context-Aware (CA-MCP) exposant Planning RI + Biblio + Second Brain",
                "impact": "Haute Valeur",
                "detail": "Implémenter la spécification Model Context Protocol (JSON-RPC 2.0 + Shared Context) pour que tes agents interrogent directement `sync_sheet.py` et croisent les gestes programmés avec tes fiches techniques RI.",
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
                "title": "Text-to-SQL sécurisé par grammaire SQLite en lecture seule & Snapshots temporels",
                "impact": "Quick Win",
                "detail": "Interroger ta base `data/finance.db` en langage naturel ou via des vues analytiques SQLite déterministes (taux d'épargne mensuel, exposition Cold vs Hot Wallet, plus-values Collectr) sans qu'aucune donnée bancaire ne sorte de ton Mac.",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/finance, ajoute une table SQLite `net_worth_snapshots` qui enregistre automatiquement l'historique quotidien des 3 piliers (Crédit Mutuel, Wallets EVM, Collectr Pokémon) ainsi qu'un moteur de catégorisation automatique des transactions Crédit Mutuel."
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
                "title": "Monitoring du Context Caching Efficiency & Prévention du Context Rot",
                "impact": "Quick Win",
                "detail": "Suivre en direct dans `gemini-ultra` le ratio Cache Hit (actuellement 92,8 % sur ton compte) et alerter quand une session dépasse le seuil où l'attention se dilue (Context Rot).",
                "prompt": "Dans /Users/thomaslefevre/.t3/projects/allinone/projects.json, ajoute l'application News AI (https://mrthomaslef.github.io/news-ai/) et enrichis gemini-ultra/index.html avec un indicateur d'efficacité du cache KV et de Burn Rate avant le reset."
            }
        ]
    },
    {
        "id": "family-daily-apps",
        "title": "Écosystème Famille & Hardware (Agenda Famille, AssMat, Photo, Xiaozhi ESP32)",
        "category": "Finance & Quotidien",
        "emoji": "🏡",
        "path": "/Users/thomaslefevre/Documents/agenda-famille",
        "prodUrl": "https://mrthomaslef.github.io/agenda-famille/",
        "githubUrl": "https://github.com/Mrthomaslef/agenda-famille",
        "stack": "PWA • Python Sync (`sync_family_agenda.py`, `process_takeout.py`) • ESP32-S3 AMOLED (`xiaozhi`)",
        "summary": "Outils familiaux : planning partagé Marie & Thomas + gardes Cochin + Mabrouka, paie AssMat Pajemploi, tri Google Photos APFS et compagnon vocal ESP32.",
        "aiOpportunities": [
            {
                "title": "Serveur MCP WebSocket local pour ton boîtier `xiaozhi-esp32-amoled-1.8`",
                "impact": "Haute Valeur",
                "detail": "Connecter le protocole MCP de ton ESP32-S3 AMOLED directement à `family_data.json` et `cochin_gardes.json` sur ton réseau local.",
                "prompt": "Crée un pont entre /Users/thomaslefevre/Documents/agenda-famille/family_data.json et /Users/thomaslefevre/Assistantematernelle pour pré-remplir automatiquement les horaires et jours de garde du mois dans le calculateur Pajemploi."
            }
        ]
    }
]

NEWS_ITEMS = [
    {
        "id": "deepseek-r1-grpo-verifiable-rewards",
        "category_id": "rl_reasoning_methods",
        "date": "2026-01-22",
        "date_fr": "Nature 2025 / Rév. 2026 • arXiv:2501.12948",
        "paper_ref": "DeepSeek-AI et al. • Nature Vol. 645 (arXiv:2501.12948) + DAPO / Dr. GRPO",
        "maturity": "🔬 Rupture Algorithmique Majeure",
        "setup_time": "Applicable immédiatement",
        "cost_badge": "-50 % VRAM (Suppression du Critic)",
        "source": "DeepSeek-R1, GRPO & RLVR (Verifiable Rewards)",
        "source_url": "https://arxiv.org/abs/2501.12948",
        "title_fr": "GRPO (Group Relative Policy Optimization) & RLVR : comment l'apprentissage par renforcement à récompenses vérifiables a remplacé le SFT classique",
        "summary_fr": "La publication de DeepSeek-R1 dans Nature (et ses extensions 2025–2026 Dr. GRPO et DAPO) a prouvé un résultat fondamental : des capacités complexes de raisonnement clinique et mathématique (auto-vérification, retour en arrière, critique d'hypothèse) émergent spontanément par pur Reinforcement Learning (RLVR — RL with Verifiable Rewards) sans avoir besoin de millions d'exemples de raisonnement annotés à la main (SFT).",
        "technical_breakthrough_fr": "Comment fonctionne la méthode GRPO ? Dans l'algorithme PPO classique (utilisé depuis InstructGPT), il faut maintenir en mémoire un second réseau géant (« Critic / Value Network ») de même taille que le LLM pour estimer la baseline de récompense. GRPO supprime totalement le réseau Critic : pour une question $q$, le modèle génère un groupe de $G$ réponses $\{o_1, \dots, o_G\}$, évalue chacune avec une fonction de récompense déterministe vérifiable $r_i$ (ex. exactitude du diagnostic, conformité JSON, compilation du code), puis calcule l'avantage relatif normalisé intra-groupe : $A_i = (r_i - \text{mean}(r)) / \text{std}(r)$. Résultat : division par 2 de l'empreinte mémoire d'entraînement et alignement direct sur la vérité terrain.",
        "key_points_fr": [
            "Élimination du réseau Critic : GRPO estime la baseline directement par la moyenne du groupe d'échantillons tirés pour un même prompt.",
            "RLVR (Reinforcement Learning with Verifiable Rewards) : dès qu'une tâche possède un vérificateur déterministe (un compilateur, un validateur JSON Schema, ou une grille diagnostique radiologique), le modèle peut s'auto-améliorer ou sélectionner la meilleure trajectoire par vote/vérification à l'inférence (Best-of-N avec vérificateur).",
            "Les variantes récentes (Dr. GRPO, DAPO) corrigent le biais de longueur en supprimant la division par la longueur de séquence dans la perte, évitant que les modèles ne deviennent inutilement verbeux."
        ],
        "target_projects": ["quiz-imagerie", "biblioosteo", "tapp-store-allinone"],
        "workflow_how_to_fr": "Tu peux exploiter directement le principe RLVR (« Verifiable Rewards » + échantillonnage de groupe) dans deux de tes projets : 1) Dans `QUIZ Imagerie (quiz-image-3)`, remplacer le score binaire par une fonction de récompense vérifiable à 3 composantes (Signe sémiologique élémentaire + Topographie anatomique + Diagnostic exact), et 2) Dans tes scripts Python de génération (`BiblioOstéo`, `BiblioMarie`), utiliser une boucle de vérification déterministe qui teste la sortie et rejette/corrige automatiquement toute fiche qui viole tes contraintes.",
        "implementation_steps_fr": [
            "Définir une fonction de score déterministe multi-critères (Verifiable Reward) dans `quiz-image-3` qui évalue séparément la lésion élémentaire, l'os/articulation et le diagnostic final.",
            "Ajouter dans les scripts `build_*.py` de `BiblioOstéo` et `BiblioMarie` un vérificateur de récompense automatique (présence des chiffres statistiques clés, conformité PMID/DOI, longueur des résumés)."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/quiz-image-3, implante un moteur d'évaluation graduée inspiré du paradigme Verifiable Rewards (RLVR) : décompose chaque cas du quiz en 3 récompenses vérifiables (1. Signe sémiologique / lésion élémentaire, 2. Localisation anatomique, 3. Diagnostic final) pour donner un retour pédagogique précis à l'interne lorsqu'il identifie la bonne sémiologie avant même d'avoir l'éponyme exact."
    },
    {
        "id": "colpali-late-interaction-visual-rag",
        "category_id": "multimodal_rag_graphs",
        "date": "2025-05-01",
        "date_fr": "ICLR 2025 / 2026 • arXiv:2407.01449",
        "paper_ref": "Faysse et al. (Illuin / CentraleSupélec) • ICLR 2025 (arXiv:2407.01449)",
        "maturity": "🔥 Nouvelle Méthode Standard en RAG PDF",
        "setup_time": "25 min",
        "cost_badge": "Remplace les pipelines OCR complexes",
        "source": "ColPali & ColQwen2 — Vision-Driven Document Retrieval",
        "source_url": "https://arxiv.org/abs/2407.01449",
        "title_fr": "ColPali & Late-Interaction Visuelle : pourquoi le RAG sur PDF abandonne l'OCR au profit de l'indexation de patchs d'images",
        "summary_fr": "Dans un pipeline RAG classique sur PDF scientifiques ou médicaux, on extrait le texte brut (OCR / PDF.js), on tente de reconstruire les tableaux et on découpe en chunks. Ce pipeline casse systématiquement les arbres décisionnels, les courbes de survie, les tableaux d'Impact Factor et surtout les planches d'imagerie annotées de flèches. La méthode ColPali (ICLR 2025, suivie de ColQwen2) supprime totalement l'étape d'OCR en indexant directement l'image visuelle de chaque page.",
        "technical_breakthrough_fr": "Comment fonctionne la méthode ? Au lieu de compresser toute une page PDF en un seul vecteur global (qui perd les détails fins), ColPali découpe la page rendue en une grille de patchs visuels (ex. $32 \times 32 = 1024$ patchs), les passe dans un Vision-Language Model (PaliGemma / Qwen2-VL) et projette chaque patch dans un espace d'embedding léger (dimension 128, quantifié en int8 ou binaire). Lors d'une recherche, l'opérateur **MaxSim (Late Interaction de ColBERT)** calcule pour chaque mot de ta requête le produit scalaire maximal avec tous les patchs de la page : $\text{Score}(q, d) = \sum_{i \in q} \max_{j \in d} (E_q^{(i)} \cdot E_d^{(j)})$. Un mot comme « vissage ilio-sacré » ou « courbe Kaplan-Meier » matche directement la zone visuelle exacte de la diapo !",
        "key_points_fr": [
            "Indexation 10x plus rapide et fidèle qu'un pipeline OCR + détection de mise en page.",
            "L'opérateur MaxSim permet non seulement de retrouver la bonne page/diapo PDF, mais aussi de générer une carte de chaleur (heatmap) montrant quel patch précis de la diapo a répondu à la requête.",
            "Avec la quantification binaire/int8 des vecteurs multi-patchs, l'index de 500 diapos de staff tient en quelques mégaoctets."
        ],
        "target_projects": ["archive-des-internes", "guide-infiltration", "biblioosteo"],
        "workflow_how_to_fr": "Tes projets `Archives des Internes` (présentations PDF de Bone Club, Cas du mardi, Cours) et `Guide Infiltrations` (213 planches anatomiques et radioguidées) sont les cas d'usage rêvés de cette méthode : beaucoup d'informations cruciales sont dans les schémas d'incidence, les flèches sur les coupes IRM et les tableaux récapitulatifs des diapos.",
        "implementation_steps_fr": [
            "Dans `Archives des Internes`, associer à chaque diapo rendue par PDF.js des descripteurs visuels et structurels (présence d'imagerie, tableaux, région anatomique) en plus du texte OCR.",
            "Permettre dans la recherche de sauter directement à la diapo contenant le schéma ou la coupe radiologique recherchée."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/archive-des-internes et /Users/thomaslefevre/.t3/projects/guide-infiltration, améliore l'indexation et la recherche par page/diapo : combine le texte extrait avec des métadonnées visuelles par planche/diapo et affiche les miniatures des diapos correspondantes avec mise en évidence directe de la planche trouvée."
    },
    {
        "id": "medsam2-medgemma-3d-medical-foundation",
        "category_id": "medical_foundation_vlm",
        "date": "2025-07-08",
        "date_fr": "Avril–Juillet 2025 / 2026 • arXiv:2504.03600 & 2507.05201",
        "paper_ref": "Ma et al. (MedSAM 2, arXiv:2504.03600) & Google Research (MedGemma, arXiv:2507.05201)",
        "maturity": "🩻 État de l'Art Imagerie Médicale",
        "setup_time": "20 min",
        "cost_badge": "Open-Weights (Apache 2.0 / Gemma License)",
        "source": "MedSAM 2 (3D Memory Attention) & MedGemma (Multimodal RL)",
        "source_url": "https://arxiv.org/abs/2504.03600",
        "title_fr": "MedSAM 2 & MedGemma : mémoire d'attention streaming 3D sur volumes TDM/IRM et RL multimodal en radiologie",
        "summary_fr": "Deux avancées majeures ont transformé les modèles fondations ouverts en imagerie médicale : 1) **MedSAM 2** (arXiv:2504.03600) traite un volume scanner ou IRM 3D (ou une boucle d'échographie) comme une séquence vidéo temporelle grâce à un module de *Streaming Memory Attention*, permettant de segmenter une lésion en 3D à partir d'un seul clic sur la coupe centrale (réduisant de 85 % le temps de détourage). 2) **MedGemma** (Google Research, arXiv:2507.05201, 4B et 27B) démontre que le post-training par **Reinforcement Learning multimodal** surpasse nettement le fine-tuning supervisé (SFT) pour le raisonnement sémiologique et la génération de comptes-rendus.",
        "technical_breakthrough_fr": "Pourquoi est-ce une percée méthodologique ? En imagerie 3D classique (ex. U-Net 3D / nnU-Net), chaque pathologie nécessite un modèle spécifique lourd. MedSAM 2 (entraîné sur >455 000 paires de volumes TDM/IRM 3D et >76 000 frames d'échographie) maintient une banque mémoire FIFO des embeddings des coupes précédentes : la coupe $z$ assiste par *cross-attention* aux caractéristiques de la lésion sur les coupes $z-1, z-2, \dots$. De son côté, MedGemma 4B utilise un encodeur visuel SigLIP médicalisé couplé à un entraînement RL qui pénalise les hallucinations de latéralité et de modalité.",
        "key_points_fr": [
            "Propagation 3D one-prompt : 1 boîte ou 1 point sur la coupe clé suffit à propager la région d'intérêt (ROI) sur tout l'empilement DICOM TDM/IRM.",
            "Support natif de l'échographie interventionnelle (suivi temps réel d'une masse des parties molles ou d'un trajet d'aiguille image par image).",
            "MedGemma 4B est suffisamment compact pour tourner localement sur la mémoire unifiée d'un Mac mini M4 (en 4-bit ou 8-bit MLX) pour pré-annoter des cas d'enseignement sans envoyer d'image sur Internet."
        ],
        "target_projects": ["dicomviewer-radio-thomas", "quiz-imagerie", "second-brain"],
        "workflow_how_to_fr": "Dans ta console pédagogique `TPack PACS (dicomviewer)` et dans le Studio de `QUIZ Imagerie`, tu peux implanter une propagation automatique de ROI 3D entre coupes adjacentes lors de la création de dossiers `.tpack`, et utiliser un modèle local (ou l'analyse d'histogramme localisée dans la ROI) pour calculer automatiquement le fenêtrage optimal centré sur la lésion.",
        "implementation_steps_fr": [
            "Dans `dicomviewer`, ajouter un outil « 🎯 ROI Lésionnelle 3D » qui ajuste automatiquement le fenêtrage (Window Width / Window Level) sur les densités Hounsfield (TDM) ou intensités (IRM) de la boîte pointée.",
            "Permettre d'exporter la coupe clé avec sa ROI commutable (affichée à la correction du quiz) vers `quiz-image-3`."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/Documents/dicomviewer et /Users/thomaslefevre/.t3/projects/quiz-image-3, ajoute un outil d'annotation de Région d'Intérêt (ROI) inspiré de MedSAM 2 : un clic-glissé sur la lésion calcule automatiquement le fenêtrage optimal centré sur la ROI, interpole la boîte sur les coupes adjacentes et permet d'afficher le contour de la lésion en correction dans QUIZ Imagerie."
    },
    {
        "id": "hipporag2-lightrag-personalized-pagerank",
        "category_id": "multimodal_rag_graphs",
        "date": "2025-02-20",
        "date_fr": "NeurIPS 2024 & Févr. 2025 • arXiv:2502.14802 & 2410.05779",
        "paper_ref": "Gutiérrez et al. (HippoRAG 2, arXiv:2502.14802) & Guo et al. (LightRAG, arXiv:2410.05779)",
        "maturity": "⚡ Méthode Idéale pour Obsidian & Biblio",
        "setup_time": "15 min",
        "cost_badge": "0 € • Algorithme de Graphe Pur (PageRank)",
        "source": "HippoRAG 2 (Associative Memory) & LightRAG",
        "source_url": "https://arxiv.org/abs/2502.14802",
        "title_fr": "HippoRAG 2 & LightRAG : la mémoire associative par Personalized PageRank remplace le Vector RAG classique",
        "summary_fr": "Le RAG vectoriel standard (découper des notes en chunks et calculer une similarité cosinus) échoue sur les questions cliniques multi-sauts : par exemple, relier une note de RCP Sarcome, la fiche technique d'abord de biopsie du compartiment antérieur de cuisse, la gestion du Plavix et l'article de référence dans BiblioOstéo. **HippoRAG 2** (arXiv:2502.14802) s'inspire de la théorie de l'indexation hippocampique humaine pour combiner vecteurs et marche aléatoire sur graphe via l'algorithme **Personalized PageRank (PPR)**.",
        "technical_breakthrough_fr": "Comment fonctionne la méthode ? Au lieu de ne chercher que les passages textuellement proches de la requête, HippoRAG 2 construit un graphe de connaissances léger (nœuds = entités cliniques, actes RI, molécules, notes, articles PMID ; arêtes = relations et liens `[[Wikilinks]]`). Lors d'une requête, les nœuds détectés dans la question reçoivent une probabilité initiale (seed vector $\vec{p}_0$), puis l'algorithme exécute une diffusion **Personalized PageRank** : $\vec{\pi} = (1 - \alpha) M \vec{\pi} + \alpha \vec{p}_0$. En 10 itérations matricielles (< 2 ms en Python/JS), la probabilité se propage à travers tes `[[Wikilinks]]` et tes tags pour faire remonter les fiches indirectement mais crucialement liées !",
        "key_points_fr": [
            "Gain de +20 à +30 % sur les benchmarks de raisonnement multi-sauts (MuSiQue, 2WikiMultihopQA) par rapport au RAG vectoriel ou BM25 seul.",
            "Contrairement au GraphRAG de Microsoft (qui coûte très cher en tokens pour générer des résumés de communautés), LightRAG et HippoRAG 2 se mettent à jour de façon incrémentale en quelques millisecondes.",
            "Ton `Second Brain` Obsidian (`/Users/thomaslefevre/2nd brain`) possède DÉJÀ une structure de graphe explicite (`[[Wikilinks]]`, propriétés YAML `domaine`, `tags`) : c'est un graphe HippoRAG naturel !"
        ],
        "target_projects": ["second-brain", "biblioosteo", "biblio-marie", "cochin-os"],
        "workflow_how_to_fr": "Implémenter l'algorithme Personalized PageRank (PPR) directement sur le graphe unifié de ton `Second Brain` Obsidian + `BiblioOstéo` + `Guide Infiltrations`. Quand tu prépares une vacation RI ou un staff, l'algorithme active les nœuds de l'acte et diffuse le score vers les protocoles d'anesthésie, les CR-types et les articles PubMed connectés.",
        "implementation_steps_fr": [
            "Parser les fichiers Markdown de `/Users/thomaslefevre/2nd brain` (liens `[[...]]` et tags YAML) et les relier aux tags et catégories de `biblioosteo/data/articles.json`.",
            "Implémenter la fonction `personalized_pagerank(adj_matrix, seed_nodes, alpha=0.15)` en Python standard (zéro dépendance lourde) pour classer contextuellement tes notes et ta biblio."
        ],
        "t3_prompt": "Crée dans /Users/thomaslefevre/2nd brain un moteur de recherche associatif basé sur la méthode HippoRAG 2 (Personalized PageRank, arXiv:2502.14802) : construis le graphe reliant toutes mes notes Obsidian ([[Wikilinks]], tags YAML), mes 75 fiches du Guide Infiltrations et mes articles BiblioOstéo, afin qu'une requête sur un geste RI fasse remonter par diffusion sur le graphe le protocole technique, le CR-type, les règles d'anticoagulants et les PMIDs associés."
    },
    {
        "id": "xgrammar2-outlines-constrained-decoding-pda",
        "category_id": "inference_grammar_edge",
        "date": "2025-11-15",
        "date_fr": "2025–2026 • arXiv:2411.15100 & JSONSchemaBench (2501.10868)",
        "paper_ref": "Dong et al. (XGrammar / XGrammar-2, CMU / MLC) & Willard et al. (Outlines FSM)",
        "maturity": "⚡ Latence Zéro (< 40 µs / token)",
        "setup_time": "15 min",
        "cost_badge": "100 % Fiabilité Schéma & Tool-Calling",
        "source": "XGrammar-2 & Constrained Decoding via Pushdown Automata",
        "source_url": "https://arxiv.org/abs/2411.15100",
        "title_fr": "XGrammar-2 & Décodage Contraint par Automates à Pile (PDA) : comment garantir mathématiquement 0 % d'erreur de format JSON ou d'appel d'outil",
        "summary_fr": "Demander à un LLM dans un prompt « Réponds uniquement en JSON valide » échoue régulièrement sur des schémas imbriqués ou lors d'extractions massives d'articles PubMed. Les méthodes **Outlines** (automates à états finis FSM) et **XGrammar / XGrammar-2** (arXiv:2411.15100, automates à pile au niveau de l'octet avec cache JIT) résolvent ce problème directement dans la boucle d'échantillonnage des logits : à chaque pas de génération, un masque binaire met à $-\infty$ la probabilité de tout token du vocabulaire qui violerait la grammaire JSON Schema ou le typage d'un outil.",
        "technical_breakthrough_fr": "Quelle est l'astuce algorithmique d'XGrammar ? Un vocabulaire LLM contient ~128 000 tokens qui découpent arbitrairement les accolades et les chaînes UTF-8. Calculer la validité de 128 000 tokens à chaque pas sur une grammaire non contextuelle (CFG) prenait des dizaines de millisecondes. XGrammar sépare les tokens en deux ensembles : 1) les **tokens indépendants du contexte** (>99 % des cas), dont les masques binaires sont pré-calculés hors-ligne dans un cache compact, et 2) les rares **tokens dépendants du contexte** (fermetures d'imbrication), évalués à la volée par un automate à pile (Pushdown Automaton) avec compilateur JIT. XGrammar-2 ajoute `TagDispatch` pour basculer dynamiquement entre réflexion libre (`<think>`) et grammaire stricte dès qu'un tag d'outil apparaît.",
        "key_points_fr": [
            "Surcoût de décodage quasi nul (< 40 microsecondes par étape, soit un gain de vitesse jusqu'à 100x sur les moteurs de grammaire de première génération).",
            "Garantie mathématique à 100 % que la sortie respecte les types, les énumérations (`enum` des catégories `BiblioOstéo` / `BiblioMarie`) et les champs obligatoires.",
            "Supporté nativement dans les APIs Gemini (`response_schema`), Claude (Tool Use strict), ainsi qu'en local via `mlx-lm`, `vLLM` et `llama.cpp`."
        ],
        "target_projects": ["biblioosteo", "biblio-marie", "patrimoine-os", "quiz-imagerie"],
        "workflow_how_to_fr": "Remplacer toutes les extractions de texte libre ou regex fragiles dans tes pipelines de données (`BiblioOstéo`, `BiblioMarie`, import CSV/Collectr de `PatrimoineOS`) par des schémas JSON contraints avec énumérations strictes (`category_id`, `design`, `audience`, `modality`).",
        "implementation_steps_fr": [
            "Définir un fichier `schema.json` formel pour `articles.json` (`BiblioOstéo`), `editorial.json` (`BiblioMarie`) et les cas cliniques de `quiz-image-3`.",
            "Intégrer la validation stricte dans les scripts Python de build pour bloquer automatiquement toute entrée mal typée avant la génération de `embedded_data.js`."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/biblioosteo et /Users/thomaslefevre/.t3/projects/biblio-marie, crée des schémas JSON formels (JSON Schema Draft 2020-12 avec enums stricts sur les catégories, modalités et types d'études) et intègre-les dans scripts/build_biblio_database.py et scripts/build.py pour garantir à 100 % l'intégrité des fiches et des exports Zotero."
    },
    {
        "id": "kokoro-82m-styletts2-istftnet-webgpu",
        "category_id": "inference_grammar_edge",
        "date": "2025-02-10",
        "date_fr": "2025–2026 • Apache 2.0 • Kokoro-82M & ONNX WebGPU",
        "paper_ref": "hexgrad (Kokoro-82M) • Architecture StyleTTS 2 + Vocodeur ISTFTNet (Transformée de Fourier Inverse)",
        "maturity": "⚡ 100 % Client-Side / 0 € Serveur",
        "setup_time": "20 min",
        "cost_badge": "Modèle 82M (~86 Mo quantifié q8)",
        "source": "Kokoro-82M & Synthèse Vocale Neuronale WebGPU",
        "source_url": "https://huggingface.co/hexgrad/Kokoro-82M",
        "title_fr": "Kokoro-82M (StyleTTS 2 + ISTFTNet) sous WebGPU : comment un modèle de seulement 82M de paramètres rivalise avec les TTS géants directement dans le navigateur",
        "summary_fr": "Pendant longtemps, obtenir une synthèse vocale (Text-to-Speech) naturelle en français ou en anglais exigeait soit une API cloud payante (ElevenLabs, OpenAI Audio), soit un modèle local de plus de 1 Go. **Kokoro-82M** (Apache 2.0) a prouvé qu'une architecture de 82 millions de paramètres seulement (~86 Mo en ONNX int8) surpasse dans les classements Elo des modèles 10 fois plus lourds, et s'exécute en temps réel dans une simple page web via **WebGPU / WASM** (`kokoro-js` / `Transformers.js`).",
        "technical_breakthrough_fr": "Pourquoi Kokoro-82M est-il si léger et rapide ? Les TTS modernes classiques utilisent des étapes de diffusion itératives lourdes et un vocodeur temporel neuronal (comme HiFi-GAN) qui calcule point par point chaque échantillon audio à 24 kHz. Kokoro-82M combine une architecture **StyleTTS 2** allégée (sans encodeur de diffusion lourd à l'inférence) avec un vocodeur **ISTFTNet** : au lieu de générer l'onde sonore brute échantillon par échantillon par convolutions transposées coûteuses, le réseau prédit la magnitude et la phase dans le domaine fréquentiel, puis applique une simple **Transformée de Fourier Rapide Inverse (iSTFT)** mathématique ! Le coût de calcul chute drastiquement tout en préservant une prosodie ultra-naturelle.",
        "key_points_fr": [
            "Exécution 100 % dans le navigateur (iPhone, iPad, Mac) via ONNX Runtime Web (WebGPU fp16/fp32 ou WebAssembly SIMD) ou en local sur Mac mini M4 via `mlx-audio`.",
            "Support multilingue incluant le français (`ff_siwis`) et l'anglais scientifique/médical.",
            "Zéro serveur, zéro coût par caractère : compatible avec un hébergement statique GitHub Pages."
        ],
        "target_projects": ["biblio-marie", "biblioosteo", "second-brain"],
        "workflow_how_to_fr": "Transformer `BiblioMarie` et `BiblioOstéo` en véritable **revue de presse audio (« Mode Podcast 2 min »)** : en un tap, écouter à la suite les synthèses françaises et les points « En pratique » des nouveaux articles de la semaine pendant les trajets.",
        "implementation_steps_fr": [
            "Ajouter un lecteur audio flottant (« 🎧 Écouter la sélection ») dans `BiblioMarie` et `BiblioOstéo`.",
            "Utiliser une architecture hybride : voix neuronale haute qualité (pré-générée en opus/mp3 via Kokoro local lors du `build.py` ou synthétisée à la volée) avec fallback instantané hors-ligne."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/biblio-marie et /Users/thomaslefevre/.t3/projects/biblioosteo, ajoute un mode « 🎧 Écouter l'article / Mode Podcast » avec barre de lecture flottante (Play/Pause, vitesse 1x/1.25x/1.5x, passage automatique à l'article suivant) permettant d'écouter la synthèse française et les implications pratiques en mains-libres."
    },
    {
        "id": "eagle3-speculative-decoding-apple-silicon-mlx",
        "category_id": "inference_grammar_edge",
        "date": "2025-03-03",
        "date_fr": "Mars 2025 / Études Apple Silicon 2026 • arXiv:2503.01840",
        "paper_ref": "Li et al. (EAGLE-3, arXiv:2503.01840) & Apple Silicon MLX Inference Studies (2026)",
        "maturity": "🔬 Optimisation Inférence & Mac M4",
        "setup_time": "15 min",
        "cost_badge": "Accélération 2.5x à 4x sans perte mathématique",
        "source": "EAGLE-3 (Feature-Level Autoregression) & Apple Silicon MLX",
        "source_url": "https://arxiv.org/abs/2503.01840",
        "title_fr": "EAGLE-3 & Décodage Spéculatif sur Apple Silicon (Mac mini M4 / MLX) : accélérer la génération de 3x sans aucune perte de qualité",
        "summary_fr": "Lorsqu'un LLM génère du texte ou du code token par token, le facteur limitant n'est pas la puissance de calcul brute du GPU, mais la **bande passante mémoire** (il faut relire tous les poids du modèle depuis la RAM à chaque token généré). Le décodage spéculatif et sa percée **EAGLE-3** (arXiv:2503.01840) permettent de proposer 4 à 6 tokens d'un coup via une tête légère et de les vérifier en **une seule passe parallèle** du grand modèle, garantissant mathématiquement exactement la même distribution de sortie que le modèle original.",
        "technical_breakthrough_fr": "Quelle est la nouveauté de la méthode EAGLE-3 par rapport au décodage spéculatif classique ? 1) Au lieu d'utiliser un second petit modèle indépendant (« Draft Model »), EAGLE greffe une tête autorégressive ultra-légère directement sur les représentations internes (hidden states) du modèle cible. 2) Alors qu'EAGLE-1/2 ne lisait que la dernière couche cachée (contrainte par la prédiction du token immédiat), **EAGLE-3 fusionne les vecteurs de caractéristiques des couches basses, moyennes et hautes** du Transformer et entraîne la tête en mode *Training-Time Test* (simulation de plusieurs pas d'auto-alimentation pendant l'entraînement). Sur Apple Silicon (Mac mini M4 avec mémoire unifiée via `mlx-lm`), cela réduit massivement le goulot d'étranglement mémoire lors de la rédaction de longs comptes-rendus ou de patchs de code.",
        "key_points_fr": [
            "Accélération strictement **lossless** (sans perte) : l'algorithme de rejet spéculatif garantit que la sortie finale suit à 100 % la loi de probabilité du grand modèle.",
            "Gain maximal sur le code, le JSON et les comptes-rendus médicaux structurés (où les séquences de tokens sont hautement prévisibles par la tête spéculative).",
            "Sur ton Mac mini M4 (`M4 Gaming` / serveur local `192.168.1.111`), le framework `mlx-lm` d'Apple tire parti de la mémoire unifiée pour faire tourner modèle cible + brouillon spéculatif sans copie CPU↔GPU."
        ],
        "target_projects": ["tapp-store-allinone", "second-brain", "biblioosteo"],
        "workflow_how_to_fr": "Pour toutes tes tâches d'automatisation locale sur ton Mac mini M4 (anonymisation RGPD de notes médicales, pré-classification de lignes bancaires `PatrimoineOS`, ou résumé rapide de mails/planning dans `Agendainterventionnel`), utiliser `mlx-lm` avec décodage spéculatif activé ou des prompts préfixés qui maximisent l'acceptation des tokens spéculatifs.",
        "implementation_steps_fr": [
            "Structurer les modèles de sortie (CR-types, JSON) avec des clés prévisibles dans un ordre fixe pour maximiser le taux d'acceptation spéculatif (Draft Acceptance Rate).",
            "Optionnel : disposer d'un runner local `mlx` sur ton Mac mini M4 pour les traitements sensibles 100 % hors-cloud."
        ],
        "t3_prompt": "Analyse mes scripts d'automatisation locale dans /Users/thomaslefevre/Documents/Agendainterventionnel et /Users/thomaslefevre/2nd brain, et prépare un module Python optionnel utilisant l'inférence locale Apple Silicon (MLX / API locale) avec prompts structurés à préfixe fixe pour traiter hors-ligne les données médicales sensibles."
    },
    {
        "id": "agentless-hierarchical-localization-vs-autonomous-swe",
        "category_id": "agentic_protocols_swe",
        "date": "2025-09-25",
        "date_fr": "FSE / 2025–2026 • arXiv:2407.01489 & 2509.23045",
        "paper_ref": "Xia et al. (Agentless, UIUC, arXiv:2407.01489) & Kimi-Dev (arXiv:2509.23045)",
        "maturity": "🔥 Méthode d'Ingénierie Code Prouvée",
        "setup_time": "Immédiat dans T3 Code",
        "cost_badge": "Divise par 4 le coût et les boucles d'erreur",
        "source": "Agentless & Localisation Hiérarchique sur SWE-bench",
        "source_url": "https://arxiv.org/abs/2407.01489",
        "title_fr": "Méthode « Agentless » (arXiv:2407.01489) : pourquoi la localisation hiérarchique en 3 étapes bat souvent les agents autonomes complexes sur SWE-bench",
        "summary_fr": "Une découverte contre-intuitive mais majeure sur le benchmark de génie logiciel **SWE-bench** a été démontrée par l'article *Agentless* (UIUC) et confirmée par les travaux 2025–2026 (*Kimi-Dev*, arXiv:2509.23045) : laisser un agent autonome boucler librement pendant 40 tours avec des outils shell finit souvent par polluer sa fenêtre de contexte, introduire des régressions et exploser la consommation de tokens. À l'inverse, un pipeline déterministe en **3 phases strictes (1. Localisation hiérarchique → 2. Génération de patchs candidats → 3. Validation par test reproductible)** obtient un taux de résolution supérieur pour une fraction du coût.",
        "technical_breakthrough_fr": "Comment fonctionne la localisation hiérarchique d'Agentless ? Au lieu de faire des `grep` aléatoires dans tout le dépôt, la méthode procède en entonnoir : **Étape 1a** : fournir uniquement l'arbre des fichiers du dépôt (et les résumés `AGENTS.md`) pour sélectionner les $k$ fichiers pertinents. **Étape 1b** : fournir uniquement le squelette (signatures des fonctions, classes, sélecteurs CSS/DOM) de ces $k$ fichiers pour identifier la fonction exacte. **Étape 1c** : ne lire que la plage de lignes `[StartLine, EndLine]` ciblée, générer un diff minimal (`Search/Replace`), et exécuter un vérificateur syntaxique (`node -e` / `python3 -m py_compile` / test unitaire).",
        "key_points_fr": [
            "Réduit de 70 % le nombre de tokens d'entrée consommés par tâche de maintenance ou d'ajout de fonctionnalité.",
            "C'est particulièrement crucial sur tes applications qui reposent sur un gros fichier `index.html` autonome (`allinone` fait 93 Ko, `biblioosteo` fait 42 Ko, `guide-interne-cochin-os`) : lire tout le fichier à chaque tour gaspille le contexte.",
            "En documentant la carte des fonctions et des sections de lignes dans un fichier `AGENTS.md` par projet, tu donnes directement l'Étape 1a et 1b gratuitement à ton agent T3 Code !"
        ],
        "target_projects": ["tapp-store-allinone", "cochin-os", "biblioosteo", "patrimoine-os"],
        "workflow_how_to_fr": "Appliquer la méthode *Hierarchical Localization* d'Agentless à tes 18 dépôts en générant automatiquement dans chaque projet un index structurel léger (`AGENTS.md`) qui cartographie les fichiers, les fonctions clés et la commande de validation syntaxique en 1 ligne.",
        "implementation_steps_fr": [
            "Générer pour chaque dépôt un `AGENTS.md` contenant l'arbre des fichiers, le rôle de chaque script et les points d'entrée JS/Python.",
            "Inclure dans chaque `AGENTS.md` la commande exacte de vérification rapide (ex. validation JS `new Function()` + vérification du build JSON) inspirée de la phase 3 d'Agentless."
        ],
        "t3_prompt": "Applique la méthode de localisation hiérarchique Agentless (arXiv:2407.01489) à mes projets dans /Users/thomaslefevre/.t3/projects/ (allinone, biblioosteo, biblio-marie, guide-interne-cochin-os, guide-infiltration, archive-des-internes, finance, quiz-image-3) : génère dans chacun un fichier AGENTS.md contenant le squelette des fichiers/fonctions clés et la commande de test/validation déterministe en 1 ligne."
    },
    {
        "id": "context-rot-attention-dilution-long-context",
        "category_id": "agentic_protocols_swe",
        "date": "2026-11-01",
        "date_fr": "2025–2026 • arXiv:2611.04169 & RULER / NoLiMa Benchmarks",
        "paper_ref": "Études sur la dégradation de l'attention en contexte long (RULER, NoLiMa, arXiv:2611.04169)",
        "maturity": "🔬 Méthode de Prompting & Context Engineering",
        "setup_time": "Immédiat",
        "cost_badge": "+35 % de précision sur tâches complexes",
        "source": "Context Rot & Dilution d'Attention Softmax en Fenêtre Géante",
        "source_url": "https://arxiv.org/abs/2611.04169",
        "title_fr": "« Context Rot » & Compétition d'Attention : pourquoi une fenêtre de 1M–2M de tokens perd en précision dès 64k tokens si le contexte n'est pas élagué",
        "summary_fr": "Bien que les modèles frontières supportent techniquement 200k à 2 millions de tokens, les benchmarks de raisonnement en contexte long (**RULER**, **NoLiMa** et l'étude récente *Length Is Cheap, Competition Is Not: Attention Predicts Context Rot in Retrieval*, arXiv:2611.04169) démontrent un phénomène critique appelé **Context Rot** : ce n'est pas la longueur brute qui dégrade le modèle, mais la **compétition sémantique dans le dénominateur du Softmax d'attention** lorsque des dizaines de versions de code similaires ou de logs d'outils s'accumulent dans l'historique.",
        "technical_breakthrough_fr": "Quelle est l'explication mathématique ? Dans le mécanisme d'attention $\text{Attention}(Q, K, V) = \text{softmax}(QK^T / \sqrt{d_k})V$, la somme des poids vaut 1. Si ton historique de conversation contient 15 anciens blocs de code HTML/JSON presque identiques au fichier actuel (des « distracteurs à forte similarité cosinus »), la masse de probabilité du Softmax se divise entre les anciennes versions et la version actuelle (entropie d'attention élevée). Cela provoque des régressions où le modèle réintroduit un bug corrigé 10 tours plus tôt !",
        "key_points_fr": [
            "Ce sont les **distracteurs proches** (anciens logs, anciennes versions du même fichier dans un long thread) qui causent le Context Rot, bien plus que du texte non lié.",
            "Déléguer une sous-tâche exploratoire ou une revue à un **sous-agent à contexte vierge** (Subagent / `delegate_task`) isole totalement le bruit de recherche et ne renvoie au thread principal qu'une synthèse propre de 300 tokens.",
            "Pour tes sessions T3 Code : ouvrir un nouveau thread propre par fonctionnalité majeure (ou s'appuyer sur un résumé d'état dans `AGENTS.md` / `HANDOVER.md`) maintient l'entropie d'attention au minimum."
        ],
        "target_projects": ["tapp-store-allinone", "second-brain", "cochin-os"],
        "workflow_how_to_fr": "Mettre en place deux réflexes issus de la recherche sur le *Context Rot* : 1) Utiliser des sous-agents de recherche (`research` subagent) quand il faut fouiller dans de nombreux fichiers afin de garder le thread principal immaculé, et 2) Maintenir un fichier `HANDOVER.md` ou un indicateur de santé de session dans ton dashboard `Agent Tracking (gemini-ultra)`.",
        "implementation_steps_fr": [
            "Dans `Agent Tracking (allinone/gemini-ultra)`, calculer le nombre moyen de steps par prompt pour repérer les threads trop longs sujets au Context Rot.",
            "Utiliser la délégation à des sous-agents spécialisés pour les audits multi-projets."
        ],
        "t3_prompt": "Dans /Users/thomaslefevre/.t3/projects/allinone/gemini-ultra/index.html, ajoute un indicateur « Santé du Contexte & Efficacité Cache » qui analyse le ratio Cache Hit (92.8%) et le ratio Steps/Prompts pour m'indiquer quand mes sessions sont optimales ou quand il est préférable d'ouvrir un thread frais pour éviter le Context Rot."
    },
    {
        "id": "context-aware-mcp-shared-context-stores",
        "category_id": "agentic_protocols_swe",
        "date": "2026-01-19",
        "date_fr": "Spécification MCP 2025–2026 • arXiv:2601.11595",
        "paper_ref": "Anthropic / Linux Foundation (MCP Spec) & CA-MCP (arXiv:2601.11595)",
        "maturity": "🔌 Standard Industriel Universel",
        "setup_time": "25 min",
        "cost_badge": "0 € • JSON-RPC 2.0 Local",
        "source": "Model Context Protocol (MCP) & Context-Aware MCP (CA-MCP)",
        "source_url": "https://arxiv.org/abs/2601.11595",
        "title_fr": "Model Context Protocol (MCP) & Context-Aware MCP (arXiv:2601.11595) : l'architecture à mémoire partagée entre serveurs d'outils",
        "summary_fr": "Inspiré du *Language Server Protocol (LSP)*, le **Model Context Protocol (MCP)** a standardisé la connexion entre les modèles d'IA et les sources de données locales via JSON-RPC 2.0 (en séparant strictement *Resources*, *Prompts* et *Tools*). En 2026, les travaux sur **Context-Aware MCP (CA-MCP, arXiv:2601.11595)** et le *Lazy Tool Loading* ont résolu les deux limites initiales du protocole : l'inflation du prompt par des dizaines de schémas JSON d'outils, et le fait que le LLM devait servir de « passe-plat » coûteux pour copier des données d'un serveur A (ex. PubMed) vers un serveur B (ex. Zotero ou Obsidian).",
        "technical_breakthrough_fr": "Comment fonctionnent le *Lazy Tool Loading* et le *Shared Context Store (SCS)* de CA-MCP ? 1) Avec le chargement paresseux (que ton harnais T3 Code utilise déjà dans `/mcp/`), seuls les noms des outils sont injectés dans le prompt initial ; l'agent ne lit le schéma JSON complet d'un outil que lorsqu'il décide de l'appeler (économie de 85 % des tokens système). 2) Avec un *Shared Context Store*, deux outils MCP locaux partagent un espace d'état local (ex. un fichier SQLite ou un état JSON sur disque) en ne passant au LLM qu'un identifiant de référence léger (`ref_id`) au lieu de faire transiter 20 pages d'abstracts ou de planning brut dans les tokens générés.",
        "key_points_fr": [
            "Passer un `pmid` ou un `ref_id` entre outils locaux plutôt que de faire régénérer tout le texte par le LLM divise par 10 la latence et élimine tout risque de troncature ou d'altération du texte original.",
            "Permet d'exposer ton écosystème médical (`BiblioOstéo`, `BiblioMarie`, `Guide Infiltrations`, `Planning RI Cochin`, `Second Brain`) sous forme d'un serveur MCP unique.",
            "Compatible à la fois avec T3 Code, Claude Code et même le firmware WebSocket de ton boîtier `xiaozhi-esp32-amoled-1.8`."
        ],
        "target_projects": ["agenda-interventionnel", "biblioosteo", "second-brain", "family-daily-apps"],
        "workflow_how_to_fr": "Construire un micro-serveur MCP local en Python qui utilise le pattern *Pass-by-Reference* : quand tu demandes d'ajouter un article à `BiblioOstéo` et Zotero, l'outil récupère l'abstract PubMed et le PDF directement sur disque et ne renvoie au LLM que les champs nécessaires à la synthèse française.",
        "implementation_steps_fr": [
            "Créer un serveur MCP Python exposant tes données Cochin/Biblio/Famille en JSON-RPC.",
            "Utiliser des références locales (`pmid`, `procedure_id`, `date_iso`) pour éviter de faire transiter de gros payloads JSON dans la fenêtre de conversation."
        ],
        "t3_prompt": "Crée un serveur MCP Python local (cochin_mcp_server.py) basé sur l'architecture Context-Aware MCP (arXiv:2601.11595) qui expose en outils typés : 1) la recherche dans les 75 fiches de /Users/thomaslefevre/.t3/projects/guide-infiltration/guide-data.json, 2) l'ingestion directe PubMed → BiblioOstéo / BiblioMarie par référence PMID sans saturer le contexte, et 3) la lecture de /Users/thomaslefevre/Documents/Agendainterventionnel/cochin_planning.json."
    }
]


AI_KEYWORDS_REGEX = re.compile(
    r"\b(ai|llm|llms|gpt|claude|gemini|deepseek|qwen|llama|mistral|transformer|transformers|"
    r"diffusion|rag|graphrag|mcp|agent|agents|agentic|rlhf|grpo|lora|qlora|vlm|vision|"
    r"neural|deep learning|machine learning|webgpu|onnx|mlx|cuda|tensor|pytorch|jax|"
    r"embedding|embeddings|vector|ocr|tts|whisper|speech|benchmark|arxiv|inference|quantization)\b",
    re.IGNORECASE
)


def fetch_live_signals() -> list[dict]:
    """Récupère en direct les vraies publications & actualités IA (Hugging Face Daily Papers + ArXiv + HN filtré IA)."""
    live_items: list[dict] = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Hugging Face Daily Papers API (Les vrais papers IA votés par la communauté chercheur/dev)
    try:
        hf_url = "https://huggingface.co/api/daily_papers?limit=8"
        req = urllib.request.Request(hf_url, headers={"User-Agent": "NewsAI-ThomasLefevre/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            papers = json.loads(resp.read().decode("utf-8"))
            for item in papers[:6]:
                paper = item.get("paper") or {}
                pid = paper.get("id") or ""
                title = " ".join((paper.get("title") or item.get("title") or "").split())
                summary = " ".join((paper.get("summary") or item.get("summary") or "").split())
                upvotes = paper.get("upvotes", 0)
                pub_date = (paper.get("publishedAt") or item.get("publishedAt") or "")[:10]
                if title and pid:
                    live_items.append({
                        "id": f"hf-{pid}",
                        "source": "Hugging Face Daily Paper",
                        "badge": f"🔥 ▲ {upvotes} upvotes · arXiv:{pid}",
                        "date": pub_date,
                        "title": title,
                        "summary": summary[:300] + ("…" if len(summary) > 300 else ""),
                        "url": f"https://huggingface.co/papers/{pid}",
                        "discuss_url": f"https://arxiv.org/abs/{pid}",
                        "fetched_at": now_iso
                    })
    except Exception as exc:
        print(f"[warn] HF Daily Papers fetch skipped: {exc}")

    # 2. ArXiv API (Medical Imaging AI, Multimodal VLMs & Reasoning LLMs)
    try:
        query = urllib.parse.quote('cat:eess.IV OR (cat:cs.CV AND all:"medical") OR (cat:cs.CL AND (all:"reasoning" OR all:"retrieval"))')
        arxiv_url = f"https://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results=6"
        req = urllib.request.Request(arxiv_url, headers={"User-Agent": "NewsAI-ThomasLefevre/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("a:entry", ns):
                title = " ".join((entry.findtext("a:title", "", ns) or "").split())
                summary = " ".join((entry.findtext("a:summary", "", ns) or "").split())
                link = entry.findtext("a:id", "", ns)
                published = (entry.findtext("a:published", "", ns) or "")[:10]
                arxiv_id = link.rsplit("/", 1)[-1] if link else ""
                if title and link:
                    live_items.append({
                        "id": f"arxiv-{arxiv_id}",
                        "source": "ArXiv Preprint (IA & Imagerie)",
                        "badge": f"📄 arXiv:{arxiv_id}",
                        "date": published,
                        "title": title,
                        "summary": summary[:300] + ("…" if len(summary) > 300 else ""),
                        "url": link,
                        "discuss_url": link,
                        "fetched_at": now_iso
                    })
    except Exception as exc:
        print(f"[warn] ArXiv live fetch skipped: {exc}")

    # 3. Hacker News Algolia API — Filtré strictement sur le titre avec mots-clés IA / LLM / ML
    try:
        hn_url = (
            "https://hn.algolia.com/api/v1/search_by_date?"
            "query=LLM&restrictSearchableAttributes=title&tags=story&numericFilters=points%3E25&hitsPerPage=12"
        )
        req = urllib.request.Request(hn_url, headers={"User-Agent": "NewsAI-ThomasLefevre/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for hit in data.get("hits", []):
                title = hit.get("title") or ""
                if not AI_KEYWORDS_REGEX.search(title):
                    continue
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                created = (hit.get("created_at") or "")[:10]
                live_items.append({
                    "id": f"hn-{hit.get('objectID')}",
                    "source": "Hacker News AI",
                    "badge": f"▲ {points} pts · 💬 {comments}",
                    "date": created,
                    "title": title,
                    "summary": "Discussion technique et retours d'ingénierie de la communauté Hacker News.",
                    "url": story_url,
                    "discuss_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "fetched_at": now_iso
                })
    except Exception as exc:
        print(f"[warn] HN live fetch skipped: {exc}")

    return live_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Build News AI data files")
    parser.add_argument("--fetch-live", action="store_true", help="Fetch live HF Papers, ArXiv & HN AI news")
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
    print(f"✓ Base construite : {len(NEWS_ITEMS)} avancées & méthodes scientifiques, {len(PROJECTS)} pôles projets, {len(live_signals)} papers/signaux live.")


if __name__ == "__main__":
    main()
