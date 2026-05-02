# VoiceLingo - Package Showcase LinkedIn + Portfolio

---

## POST 1 - Annonce officielle du projet

```
🎬 J'ai construit VoiceLingo - une application de bureau Python qui traduit 
des vidéos de cours en français, 100% en local, sans aucune API payante.

En tant qu'étudiant L3 Informatique, j'ai souvent du mal avec les cours 
YouTube en anglais. Alors j'ai décidé de coder ma propre solution.

Ce que fait l'app :
→ Importe une vidéo locale (jusqu'à 2 Go, 22h de contenu)
→ Transcrit la parole avec Whisper large-v3 (qualité YouTube)
→ Détecte automatiquement le domaine (Python, maths, médecine...)
→ Traduit intelligemment en gardant les termes techniques intacts
   (function, class, API, Docker, gradient... ne sont PAS traduits)
→ Génère un fichier .srt complet et synchronisé

Tech stack :
🐍 Python 3.10 + tkinter
🎙 faster-whisper (Whisper large-v3)
🌐 NLLB-200 (Hugging Face - 200 langues)
🔊 XTTS-v2 (Coqui TTS - doublage vocal)
⚙️ FFmpeg (extraction et assemblage vidéo)

Le vrai défi : les vidéos de 4h, 8h, 16h.
J'ai dû implémenter un système de tranches de 1h avec
timestamps glissants pour reconstituer un SRT complet.

Et une traduction contextuelle qui comprend les domaines 
techniques → les termes restent cohérents sur toute la vidéo.

Premier vrai projet Python. Beaucoup appris. Beaucoup de bugs. 
Beaucoup de nuits tardives. Mais ça fonctionne ✅

Code disponible sur GitHub ↓

#Python #MachineLearning #OpenSource #Informatique #Etudiant #NLP #Whisper
```

---

## POST 2 - Deep-dive technique (1 semaine après)

```
🔍 Deep-dive technique : VoiceLingo

La partie la plus difficile n'était pas la transcription Whisper.
C'était la traduction intelligente.

❌ Problème découvert : NLLB-200 traduit aussi les séparateurs
   qu'on insère pour grouper les segments. Résultat : seul
   le premier sous-titre était traduit. Les autres restaient en anglais.

✅ Solution : traduction segment par segment + fenêtre de contexte glissante.
   Chaque segment reçoit les 3 sous-titres précédents déjà traduits
   comme contexte. Résultat : cohérence terminologique sur toute la vidéo.

Autre défi : les termes techniques.
"function", "class", "API", "Docker", "gradient"...
Ces mots ne doivent PAS être traduits dans un cours d'informatique.

J'ai implémenté un système de protection par tokens :
  "use a function" 
  → protect : "use a __TK0__"  
  → NLLB : "utiliser un __TK0__"  
  → restore : "utiliser un function" ✅

Le glossaire couvre 80+ termes techniques par domaine.

Ce que j'ai appris :
• Threading Python pour ne pas geler l'UI
• subprocess vs os.system (sécurité)
• Singleton pattern pour les modèles IA (chargement unique)
• VAD (Voice Activity Detection) pour couper sur les vraies pauses
• UTF-8 BOM pour la compatibilité SRT sur Windows

#Python #NLP #HuggingFace #Whisper #MachineLearning #DeepLearning
```

---

## POST 3 - Retour d'expérience étudiant

```
📚 Ce que ce projet m'a réellement appris

6 semaines. Premier vrai projet Python. Voilà ce que personne ne dit 
dans les cours :

1. Le code qui marche sur les exemples de cours ≠ code qui marche 
   sur des vraies vidéos de 8h

2. Les bugs les plus longs à trouver : 
   → Variable qui stockait "Français" au lieu de "fr"
   → Bug silencieux → SRT 100% en anglais → 2h de debug

3. La documentation officielle est ton amie.
   J'ai passé plus de temps sur les docs faster-whisper 
   que sur tous mes cours réunis.

4. Tester tôt. J'ai écrit 47 commits dont 13 étaient des "fix:"
   pour des bugs que j'aurais trouvés avec des tests unitaires dès le début.

5. Les modèles IA ne sont pas magiques.
   Whisper "tiny" donnait des résultats catastrophiques.
   Whisper "large-v3" avec les bons paramètres = niveau YouTube.
   La différence ? beam_size, best_of, vad_parameters, initial_prompt.

Prochain objectif : packager l'app en .exe Windows avec PyInstaller
pour que n'importe qui puisse l'utiliser sans installer Python.

#Etudiant #Python #Apprentissage #Informatique #Portfolio #OpenSource
```

---

## README.md complet (GitHub)

```markdown
# VoiceLingo 🎬

> Application de bureau Python pour traduire des vidéos de cours
> 100% en local - aucune API externe, aucun abonnement.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey)

## Pourquoi ce projet ?

J'étudie l'informatique en L3 et beaucoup de ressources de qualité
sont uniquement en anglais. J'ai construit VoiceLingo pour traduire
automatiquement les cours vidéo en français, avec une traduction
qui comprend les termes techniques et les garde intacts.

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🎙 Transcription Whisper | large-v3 · qualité YouTube · VAD optimisé |
| 🌐 Traduction contextuelle | NLLB-200 · 200 langues · glossaire technique |
| 🔒 Termes techniques protégés | function, class, API, Docker... intacts |
| ⏱ Vidéos longues | jusqu'à 22h · tranches de 1h · SRT complet |
| 🎤 Doublage vocal IA | XTTS-v2 · 17 langues · clonage de voix |
| 💻 100% local | aucune API · aucun abonnement · données privées |

## Installation

### Prérequis

- Python 3.10+
- FFmpeg ([télécharger](https://ffmpeg.org/download.html))

### Étapes

```bash
git clone https://github.com/votre-username/voicelingo
cd voicelingo
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

### Modèles (téléchargés automatiquement au premier lancement)

| Modèle | Taille | Usage |
|---|---|---|
| Whisper large-v3 | ~3 Go | Transcription |
| NLLB-200-600M | ~2.4 Go | Traduction |
| XTTS-v2 | ~1.9 Go | Doublage vocal |

## Configuration

Éditer `config.json` ou utiliser ⚙ Paramètres dans l'interface :

```json
{
  "whisper_model_size": "large-v3",
  "whisper_device": "cpu",
  "nllb_model": "facebook/nllb-200-distilled-600M"
}
```

## Architecture

```
voicelingo/
├── main.py                    # Point d'entrée + vérification FFmpeg
├── ui.py                      # Interface tkinter (3 panneaux)
├── processor.py               # Pipeline orchestrateur (threads)
├── video_handler.py           # Extraction audio (ffmpeg)
├── speech_to_text.py          # Transcription Whisper (tranches 1h)
├── context_translation_ia.py  # IA traduction contextuelle + glossaires
├── translation.py             # Wrapper
├── text_to_speech.py          # XTTS-v2 synthèse vocale
├── srt_generator.py           # Génération + validation SRT
├── config_manager.py          # Config avec validation schéma
└── tests/test_core.py         # Tests unitaires
```

## Domaines supportés

L'application détecte automatiquement le domaine et adapte la traduction :

- 💻 **Informatique** : 80+ termes protégés (Python, Docker, API, gradient...)
- 📐 **Mathématiques** : matrix, vector, eigenvalue...
- 🔬 **Physique** : quantum, electron, thermodynamics...
- 🏥 **Médecine** : diagnosis, treatment, PCR...
- 🌍 **Général** : traduction standard

## Auteur

Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
```

---

## Description profil GitHub (bio)

```
🎓 Étudiant L3 Informatique
🐍 Python · Machine Learning · Applications de bureau
🛠 Projet principal : VoiceLingo - traduction vidéo IA 100% locale
📍 France
```

---

## Tags et mots-clés pour visibilité

**GitHub topics à ajouter sur le repo :**
`python` `machine-learning` `whisper` `speech-to-text` `translation`
`nllb` `faster-whisper` `subtitle-generator` `srt` `tkinter` `ffmpeg`
`huggingface` `transformers` `local-ai` `video-translation`
`text-to-speech` `xtts` `french` `open-source` `desktop-app`
