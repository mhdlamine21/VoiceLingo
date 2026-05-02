# MY_CODING_SIGNATURE.md
# Signature de code personnelle - VoiceLingo / Lamine
# À lire avant d'écrire la moindre ligne de code

## Identité du projet
- **Projet** : VoiceLingo - application de bureau Python, traduction vidéo 100% locale
- **Développeur** : Étudiant L3 Informatique, première année sérieuse de Python
- **Style** : Lisible > court. Explicit > clever. Simple > abstrait.

---

## 1. Nommage

### Variables et fonctions → snake_case, noms complets
```python
# ✅ BON
video_path = "..."
total_segments = 0
detected_language = "fr"
is_processing = False
has_audio_track = True
can_process_video = False

# ❌ MAUVAIS
vp = "..."
tot_segs = 0
det_lang = "fr"
proc = False
```

### Classes → PascalCase
```python
class ProcessingPipeline:     # ✅
class VoiceLingoApp:          # ✅
class processingpipeline:     # ❌
```

### Constantes → UPPER_SNAKE_CASE en haut du fichier
```python
CHUNK_DURATION = 3600         # ✅
MAX_CHARS_PER_LINE = 42       # ✅
chunk_duration = 3600         # ❌ (constante → majuscules)
```

### Booléens → toujours préfixés
```python
is_long_video = True          # ✅
has_audio = False             # ✅
can_translate = True          # ✅
should_burn_subs = False      # ✅
long = True                   # ❌
```

---

## 2. Commentaires

### Style : minuscule, sans ponctuation, seulement si non-évident
```python
# extraire l'audio avant transcription
wav_path = extract_audio(video_path)

# whisperlarge-v3 a besoin de 16kHz mono pour la qualité max
audio_settings = {"fps": 16000, "channels": 1}

# ❌ NE PAS FAIRE
# This function extracts audio from the video.  (évident)
# Extraire l'audio.  (évident)
# TODO: fix this later  (trop vague)
```

### Commentaires acceptés
```python
# NOTE: le modèle est chargé une seule fois (singleton) pour éviter les recharges
# FIXME: sur Windows, KMP_DUPLICATE_LIB_OK doit être avant tous les imports
# TODO: ajouter le support GPU CUDA quand le setup NVIDIA est documenté
# HACK: separator batché traduit par NLLB → on traduit segment par segment
```

---

## 3. Indentation et espacement

- **4 espaces** (Python standard, pas de tabs)
- **1 ligne vide** entre les blocs logiques
- **2 lignes vides** entre les fonctions de module
- **Accolade/parenthèse ouvrante sur la même ligne** (Python natif)

```python
def transcribe(wav_path, src_lang="auto"):
    model = _get_model()
    
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"fichier audio introuvable: {wav_path}")
    
    segments, info = model.transcribe(wav_path)
    
    return segments, info.language
```

---

## 4. Gestion des erreurs

### Pattern standard : try/except avec message lisible
```python
# ✅ toujours un message utile pour l'utilisateur
try:
    info = get_video_info(video_path)
except Exception as e:
    raise RuntimeError(
        f"impossible de lire la vidéo '{Path(video_path).name}':\n{e}\n"
        "vérifiez que FFmpeg est installé et dans le PATH."
    ) from e

# ❌ except trop large sans message
try:
    info = get_video_info(video_path)
except:
    pass
```

### Toujours valider les entrées en début de fonction
```python
def translate_segment(text, lang_src, lang_tgt, model_name):
    if not text or not text.strip():
        return ""
    if lang_src == lang_tgt:
        return text  # pas de traduction nécessaire
    # ... suite du traitement
```

---

## 5. Return anticipé (early return)

```python
# ✅ early return - évite l'imbrication
def process_segment(text, glossary):
    if not text.strip():
        return ""
    if not glossary:
        return text
    
    protected, tokens = protect_terms(text, glossary)
    translated = _nllb_translate(protected)
    return restore_terms(translated, tokens)

# ❌ nested hell
def process_segment(text, glossary):
    if text.strip():
        if glossary:
            protected, tokens = protect_terms(text, glossary)
            translated = _nllb_translate(protected)
            return restore_terms(translated, tokens)
        else:
            return text
    else:
        return ""
```

---

## 6. Imports

### Ordre : standard → externe → local, avec ligne vide entre groupes
```python
# standard library
import os
import sys
import math
import threading
import tempfile
from pathlib import Path
from typing import Callable, Optional

# externe (pip)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# local (fichiers du projet)
from config_manager import load_config, save_config
from processor import ProcessingPipeline
```

---

## 7. Longueur de ligne

- **Max 100 caractères**
- Couper les longues chaînes avec `(` `)`

```python
# ✅ coupure propre
error_message = (
    f"impossible d'extraire l'audio de '{video_name}':\n{e}\n"
    "vérifiez que FFmpeg est installé et accessible depuis le terminal."
)

# ❌ ligne trop longue
error_message = f"impossible d'extraire l'audio de '{video_name}':\n{e}\nvérifiez que FFmpeg est installé et accessible depuis le terminal."
```

---

## 8. Strings

- **Double quotes** partout
- **f-strings** pour l'interpolation (jamais `.format()` ni `%`)

```python
model_name = "large-v3"                          # ✅
label = f"tranche {chunk_idx}/{total_chunks}"    # ✅
label = "tranche " + str(chunk_idx)              # ❌
label = "tranche {}".format(chunk_idx)           # ❌
```

---

## 9. Fonctions

- **Petites fonctions** pour les utilitaires réutilisables (< 20 lignes)
- **Fonctions moyennes** pour les orchestrateurs (20-60 lignes)
- **Pas de fonctions géantes** - découper si > 60 lignes
- **Type hints** sur les signatures publiques

```python
def extract_audio(
    video_path: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> str:
    """Extrait la piste audio en WAV 16kHz mono. Retourne le chemin du WAV."""
    ...
```

---

## 10. Docstrings

- **Toutes les fonctions publiques** ont une docstring courte
- **Format** : une ligne si simple, multi-lignes si paramètres/retour importants

```python
def detect_domain(text_sample: str) -> str:
    """Détecte le domaine du texte (informatique, maths, médecine...).
    
    Analyse les 3000 premiers caractères par comptage de mots-clés.
    Retourne le code du domaine dominant (ex: 'informatique').
    """
```

---

## 11. Conventions Git (Conventional Commits)

```
feat: ajouter la détection automatique du domaine
fix: corriger le bug de traduction partielle (séparateur NLLB)
refactor: extraire protect_terms dans context_translation_ia
docs: documenter les paramètres VAD dans speech_to_text
style: reformater ui.py selon la signature de code
chore: mettre à jour requirements.txt avec faster-whisper 1.0.3
test: ajouter les tests de segmentation SRT
perf: charger le modèle Whisper une seule fois (cache singleton)
```

---

## 12. Structure des fichiers

```
voicelingo/
├── main.py                    # point d'entrée UNIQUEMENT (< 30 lignes)
├── ui.py                      # interface graphique (tkinter)
├── processor.py               # orchestration pipeline (thread)
├── video_handler.py           # extraction / assemblage (ffmpeg)
├── speech_to_text.py          # transcription (Whisper)
├── context_translation_ia.py  # IA traduction contextuelle
├── translation.py             # wrapper compatibilité
├── text_to_speech.py          # synthèse vocale (XTTS)
├── srt_generator.py           # génération SRT
├── config_manager.py          # config (load/save)
├── config.json                # paramètres utilisateur
├── docs/                      # documentation
├── tests/                     # tests unitaires
├── glossaries/                # glossaires CSV par domaine
└── assets/                    # icônes, ressources UI
```

---

## 13. Ce que Claude code vs ce que je code

### Claude code intégralement :
- Boilerplate, structure, imports
- Fonctions utilitaires (wrap_text, fix_timing, etc.)
- Interface tkinter (widgets, layout)
- Logique de fichiers (load/save config)

### Claude scaffold, je code :
- Algorithmes critiques de traitement audio
- Logique de segmentation métier (word_to_segments)
- Paramètres VAD (à tuner selon mes tests réels)

### Je décide toujours :
- Les paramètres Whisper (beam_size, temperature array)
- Les seuils de segmentation SRT
- La logique de détection de domaine

---

## 14. Ce que je n'accepte pas

```python
# ❌ ternaire
lang = "fr" if detected else "en"
# ✅ if/else clair
if detected:
    lang = "fr"
else:
    lang = "en"

# ❌ walrus operator
if (n := len(words)) > 10:
    ...
# ✅ lisible
n = len(words)
if n > 10:
    ...

# ❌ list comprehension complexe
result = [_clean(s["text"]) for s in segs if s["text"].strip() and len(s["text"]) > 2]
# ✅ loop explicite
result = []
for seg in segments:
    text = seg["text"].strip()
    if text and len(text) > 2:
        result.append(_clean(text))
```
