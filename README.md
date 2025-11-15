# VoiceLingo

> Application de bureau Python pour la transcription, la traduction contextuelle et le doublage de videos 100% en local.
> Aucune API externe, aucun abonnement, aucune donnee envoyee sur des serveurs distants.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-19%20passed-brightgreen)
![Plateforme](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Interface](https://img.shields.io/badge/UI-Tkinter%20Moderne-blue)

---

## Contexte et Origine du Projet

Ce projet est ne d'un besoin personnel concret : en tant qu'apprenant, j'avais regulierement besoin de suivre des tutoriels video techniques sur YouTube et d'autres plateformes. Vu que je ne maitrise pas l'anglais a 100% et que certaines videos didactiques n'avaient aucun sous-titre disponible, j'ai imagine et developpe **VoiceLingo** en 2026.

L'objectif : disposer d'un outil simple, rapide et autonome pour transcrire l'audio des videos, traduire fidelement le propos en francais tout en preservant le jargon technique (`function`, `class`, `API`, `Docker`, `gradient`, `async`, etc.), et generer des fichiers de sous-titres `.srt` ou des doublages audio avec synchronisation.

---

## Fonctionnalites Principales

| Fonctionnalite | Description |
|---|---|
| **Transcription locale** | faster-whisper (tiny, base, medium, large-v3), VAD et gestion des longues videos |
| **Traduction intelligente** | NLLB-200 par Hugging Face, preservation des termes techniques et contextuels |
| **Detection de domaine** | Auto-detection des thematiques (Informatique, Mathematiques, Physique, Medecine...) |
| **Telechargement YouTube** | Integration native de yt-dlp pour importer des videos ou playlists via URL |
| **Sous-titres SRT conformes** | Norme de lecture 42 car/ligne, encodage UTF-8 BOM pour VLC et lecteurs multimedia |
| **Incrustation hardsub** | Gravure directe des sous-titres dans le flux video via FFmpeg |
| **Doublage vocal** | Synthese vocale locale (XTTS-v2 / pyttsx3 / edge-tts) |
| **Mode Sombre / Clair** | Theme ergonomique moderne et commutable a la volee |
| **100% Hors-ligne & Confidentiel** | Aucun envoi de donnees vers l'exterieur |

---

## Installation et Demarrage

### Prerequis
- Python 3.10 ou version superieure
- FFmpeg installe et present dans le PATH ([telechargement](https://ffmpeg.org/download.html))

### Installation rapide

```bash
git clone https://github.com/votre-compte/voicelingo.git
cd voicelingo
python -m venv venv
venv\Scripts\activate          # Sous Windows
# source venv/bin/activate     # Sous Linux/macOS
pip install -r requirements.txt
python main.py
```

### Modeles d'IA (telecharges automatiquement au premier besoin)

| Modele | Poids approximatif | Role |
|---|---|---|
| faster-whisper (base ou large-v3) | ~150 Mo a ~3 Go | Transcription vocale avec horodatage |
| NLLB-200-600M | ~2.4 Go | Traduction neuronale haute fidelite |
| XTTS-v2 / local TTS | ~1.9 Go | Doublage vocal multilingue |

---

## Architecture Logicielle

```
voicelingo/
├── main.py                    # Point d'entree de l'application et verification FFmpeg
├── ui.py                      # Interface graphique moderne, responsive et themable
├── processor.py               # Orchestrateur du pipeline asynchrone (thread securise)
├── video_handler.py           # Traitements video/audio FFmpeg (extraction, sonde, hardsub)
├── speech_to_text.py          # Transcription audio faster-whisper en tranches
├── context_translation_ia.py  # Traduction NLLB et protection des glossaires techniques
├── translation.py             # Module de liaison et retrocompatibilite
├── youtube_handler.py         # Module de capture YouTube via yt-dlp
├── text_to_speech.py          # Moteur de synthese vocale locale
├── srt_generator.py           # Formatage, decoupages et validation standard SRT
├── config_manager.py          # Gestionnaire de configuration JSON securise
├── main_api.py                # API REST locale FastAPI (optionnelle)
├── build.py                   # Script de compilation autonome PyInstaller
├── assets/                    # Identite visuelle et logo SVG du projet
└── tests/test_core.py         # Suite de tests unitaires automatisee
```

---

## Tests Unitaires

Pour executer la suite de tests automatisee :

```bash
python -m pytest tests/ -v
```

---

## Auteur et Contact

- **Auteur** : Mouhamadou Lamine Niang
- **Email** : [mouhamedlniang@gmail.com](mailto:mouhamedlniang@gmail.com)
- **Annee** : 2026
- **Formation** : Etudiant en Informatique, option Genie Logiciel
