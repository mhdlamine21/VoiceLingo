# VoiceLingo - Brief Projet Complet (Grill + Plan + Architecture + Sécurité)

---

## PARTIE 1 - GRILL PROJECT [DEEP]

### Shared Understanding - Résultat de l'analyse complète

**Project goal:** Application de bureau Python 100% locale qui traduit des vidéos longues (jusqu'à 22h, 2 Go) en générant des fichiers SRT ou des vidéos doublées, avec une IA de traduction contextuelle qui comprend le domaine (informatique, maths, médecine...).

**Primary user:** Étudiant en informatique qui regarde des cours/tutoriels en anglais et veut les comprendre en français sans dépendre de services en ligne.

**Secondary users:** Développeurs, chercheurs, étudiants d'autres filières.

**Platform:** Application de bureau Windows (priorité) + Linux/macOS (compatible)

**Deployment target:** Distribution via ZIP (Phase 1) → PyInstaller .exe (Phase 2) → PyPI package (Phase 3)

**Tech stack:** Python 3.10+ / tkinter / faster-whisper / NLLB-200 / XTTS-v2 / ffmpeg

---

### Must-have features (v1 - LIVRÉES):
1. Import vidéo locale (MP4, AVI, MOV, MKV) jusqu'à 2 Go
2. Transcription locale Whisper large-v3 avec VAD
3. Traduction contextuelle NLLB-200 avec protection des termes techniques
4. Génération SRT complet (toute la durée, UTF-8 BOM)
5. Support vidéos longues (tranches de 1h, jusqu'à 22h)

### Should have (v1.1 - PARTIELLEMENT LIVRÉES):
- Détection automatique du domaine
- Doublage vocal IA (XTTS-v2)
- API FastAPI locale optionnelle
- Fenêtre de contexte glissante pour la traduction

### Deferred (v2):
- Intégration APIs cloud (Whisper API OpenAI, DeepL, ElevenLabs)
- Interface web (remplacement tkinter)
- Multi-langue UI
- Packaging .exe Windows one-click

---

### Probable Holes identifiés (non prévus initialement)

| Trou | Impact | Statut |
|------|--------|--------|
| Pas de validation du format vidéo avant traitement | Crash silencieux | 🔴 À corriger |
| Pas de gestion de l'espace disque avant extraction | Crash sur disque plein | 🔴 À corriger |
| Modèles non téléchargés → pas de message clair | UX bloquante | 🟠 À améliorer |
| Pas de bouton "Pause" pendant traitement | UX frustrante | 🟡 Futur |
| Pas de historique des traitements récents | UX basique | 🟡 Futur |
| Pas de prévisualisation SRT dans l'app | Besoin utilisateur fort | 🟡 v1.1 |
| Pas de progress persistant en cas de crash | Perte de travail | 🟡 v2 |
| Fichier SRT sorti sans validation (timestamps) | Qualité SRT | 🟠 À corriger |
| Pas de test de la piste audio avant traitement | Crash silencieux | 🔴 À corriger |
| OpenMP conflit Windows non géré partout | Crash démarrage | ✅ Corrigé main.py |
| Pas de .gitignore / .env | Sécurité repo | 🔴 Manquant |
| Pas de tests unitaires | Qualité code | 🟠 À ajouter |
| config.json peut contenir des chemins sensibles | Sécurité | 🟡 Faible risque |
| Pas de mode sombre UI | UX moderne | 🟡 Futur |
| Encodage Windows (cp1252) sur certains chemins | Crash Windows | 🔴 À corriger |

---

### Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| large-v3 trop lent sur CPU modeste | High | High | Proposer base/medium en config |
| XTTS-v2 ne tourne pas sans GPU | High | Medium | Fallback pyttsx3 déjà implémenté |
| NLLB traduit mal certains domaines | Medium | High | Fenêtre contexte + glossaire |
| ffmpeg absent sur machine utilisateur | High | Critical | Vérification au démarrage + message |
| Espace disque insuffisant (22h audio) | Medium | High | Vérification espace avant extraction |
| Windows path avec caractères spéciaux | High | High | Encoder tous les chemins en UTF-8 |
| Modèles HF bloqués (réseau entreprise) | Low | Medium | Cache local configurable |

---

## PARTIE 2 - PLAN PROJECT [FULL]

### Phase 0 - Fondations et corrections critiques
**Durée : 3 jours**

Tâches :
1. Ajouter `.gitignore` complet (Python, IDE, modèles HF)
2. Vérifier ffmpeg au démarrage → message d'erreur clair si absent
3. Vérifier espace disque avant extraction audio
4. Corriger encodage Windows (chemins UTF-8)
5. Ajouter validation format vidéo avant traitement
6. Ajouter tests unitaires de base (srt_generator, context_translation_ia)

Exit criteria :
- [ ] `python main.py` affiche une erreur claire si ffmpeg absent
- [ ] Import d'un chemin avec espaces/accents fonctionne sur Windows
- [ ] `.gitignore` en place, aucun modèle committé

---

### Phase 1 - Qualité SRT et robustesse
**Durée : 4 jours**

Tâches :
1. Valider les timestamps SRT avant export (start < end, pas de négatifs)
2. Vérifier la présence d'une piste audio avant traitement
3. Améliorer les messages d'erreur dans processor.py
4. Ajouter logging structuré (fichier voicelingo.log)
5. Tester sur vidéos de 1h, 4h, 8h

Exit criteria :
- [ ] Aucun SRT généré avec timestamps invalides
- [ ] Vidéo sans audio → message clair "la vidéo ne contient pas de piste audio"
- [ ] Log fichier créé à chaque run

---

### Phase 2 - UX améliorée
**Durée : 3 jours**

Tâches :
1. Afficher la taille requise disque estimée avant de démarrer
2. Afficher le modèle Whisper actif + avertissement si "tiny" ou "base"
3. Prévisualisation des 10 premiers sous-titres SRT dans l'UI
4. Mode sombre optionnel
5. Mémoriser le dernier dossier de sortie

Exit criteria :
- [ ] L'utilisateur voit "Whisper large-v3 - ~10 Go RAM requis" avant de démarrer
- [ ] Prévisualisation SRT visible dans le panneau droit

---

### Phase 3 - Scalabilité API
**Durée : 5 jours**

Tâches :
1. Finaliser main_api.py (FastAPI)
2. Ajouter un provider abstrait : LocalProvider + CloudProvider (interface)
3. Permettre d'utiliser OpenAI Whisper API ou DeepL à la place des modèles locaux
4. Documenter l'API dans /docs/api.md

Exit criteria :
- [ ] `uvicorn main_api:app` fonctionne et répond sur /docs
- [ ] Interface TranscriptionProvider permet d'ajouter un provider sans modifier processor.py

---

### Phase 4 - Packaging Windows
**Durée : 5 jours**

Tâches :
1. Créer `build.py` avec PyInstaller
2. Bundler ffmpeg dans le .exe
3. Tester sur machine Windows sans Python installé
4. Créer un installateur NSIS ou Inno Setup

Exit criteria :
- [ ] `VoiceLingo.exe` tourne sur Windows 10 propre
- [ ] Les modèles se téléchargent au premier lancement

---

## PARTIE 3 - IMPROVE ARCHITECTURE [DEEP]

### Orientation Summary

**Domain:** Traduction vidéo locale - STT → NMT → TTS + SRT
**Stack:** Python 3.10 / tkinter / faster-whisper / NLLB / XTTS / ffmpeg
**Module count:** 10 fichiers Python, ~2500 lignes
**Test coverage:** Aucun test automatique (risque élevé)
**Existing patterns:** Pipeline (Orchestrator), Singleton (modèles IA), Wrapper (translation.py)

---

### Candidats d'amélioration architecturale

#### Candidat 1 - TranscriberProvider (Priorité HAUTE)

**Friction actuelle:** `speech_to_text.py` parle directement à faster-whisper. Impossible d'ajouter un autre backend (OpenAI Whisper API, AssemblyAI, Deepgram) sans modifier le fichier.

**Interface proposée:**
```python
from abc import ABC, abstractmethod

class TranscriberProvider(ABC):
    @abstractmethod
    def transcribe(
        self,
        wav_path: str,
        src_lang: str,
        chunk_progress_cb=None,
    ) -> tuple[str, str, list[dict]]:
        """Retourne (transcript, detected_lang, words[])."""

class WhisperLocalProvider(TranscriberProvider):
    """Implémentation faster-whisper locale."""

class OpenAIWhisperProvider(TranscriberProvider):
    """Implémentation via OpenAI Whisper API (futur)."""
```

**Effort:** M (3 jours)

---

#### Candidat 2 - TranslatorProvider (Priorité HAUTE)

**Friction actuelle:** `translation.py` est un wrapper mais `context_translation_ia.py` parle directement à NLLB. Impossible d'ajouter DeepL ou Google Translate sans tout réécrire.

**Interface proposée:**
```python
class TranslatorProvider(ABC):
    @abstractmethod
    def translate_segments(
        self,
        segments: list[dict],
        domain: str,
        lang_src: str,
        lang_tgt: str,
        progress_cb=None,
    ) -> list[dict]:
        """Retourne segments enrichis avec 'translated_text'."""

class NLLBLocalProvider(TranslatorProvider):
    """NLLB-200 local."""

class DeepLProvider(TranslatorProvider):
    """DeepL API (futur)."""
```

**Effort:** M (3 jours)

---

#### Candidat 3 - SRTValidator (Priorité MOYENNE)

**Friction actuelle:** `srt_generator.py` produit le SRT sans aucune validation post-génération. Des timestamps invalides peuvent passer silencieusement.

**Validation à ajouter:**
```python
def validate_srt(srt_path: str) -> list[str]:
    """Vérifie le SRT et retourne une liste d'erreurs. [] = valide."""
    errors = []
    # vérifier start < end pour chaque entrée
    # vérifier pas de chevauchement entre entrées consécutives
    # vérifier encodage UTF-8
    # vérifier index séquentiel
    return errors
```

**Effort:** S (1 jour)

---

#### Candidat 4 - DiskSpaceChecker (Priorité HAUTE)

**Friction actuelle:** Aucune vérification de l'espace disque disponible avant extraction. Une vidéo de 22h produit un WAV de ~2.5 Go. Sur un disque presque plein → crash silencieux.

**Solution:**
```python
def check_disk_space(video_path: str, output_dir: str) -> dict:
    """
    Estime l'espace nécessaire et vérifie la disponibilité.
    Retourne {'ok': bool, 'needed_gb': float, 'available_gb': float}
    """
    import shutil
    video_size = os.path.getsize(video_path)
    # WAV = ~10x la taille vidéo pour 16kHz mono
    needed = video_size * 2.5
    free = shutil.disk_usage(output_dir).free
    return {
        "ok": free > needed,
        "needed_gb": needed / (1024**3),
        "available_gb": free / (1024**3),
    }
```

**Effort:** S (0.5 jour)

---

#### Candidat 5 - ModelDownloadChecker (Priorité HAUTE)

**Friction actuelle:** Si les modèles ne sont pas téléchargés, l'application plante au milieu du traitement sans message clair. L'utilisateur ne sait pas ce qui se passe.

**Solution:**
```python
def check_models_available(config: dict) -> list[dict]:
    """
    Vérifie si les modèles configurés sont disponibles localement.
    Retourne une liste de {'model': str, 'available': bool, 'size_gb': float}
    """
```

**Effort:** S (1 jour)

---

## PARTIE 4 - SECURITY CODEGUARD [AUDIT + FIX]

### Project Security Profile
- **Type:** Desktop CLI/GUI - Python application
- **Stack:** Python 3.10 / tkinter / faster-whisper / transformers / ffmpeg subprocess
- **Attack surface:** Chemins de fichiers locaux, appels subprocess ffmpeg, config.json
- **Sensitivity level:** Low (pas de données utilisateur réseau, tout local)
- **Deployment target:** Distribution ZIP / PyInstaller .exe

---

### 🟠 [HIGH] - Injection de commande via chemins ffmpeg

**File:** `video_handler.py` - fonctions `extract_audio`, `burn_subtitles`
**Description:** Les chemins passés à `subprocess.run` via une liste ne sont pas vulnérables à l'injection shell, MAIS si un chemin contient des caractères spéciaux sur Windows et est construit en string (mode shell=True), il devient exploitable.
**Statut actuel:** La v7 utilise une liste → correct. Mais `burn_subtitles` construit encore un filtre ffmpeg avec f-string → risque résiduel.

**Correction:**
```python
# AVANT (risque résiduel)
cmd = ["ffmpeg", "-y", "-i", original_video,
       "-vf", f"subtitles='{srt_safe}'",  # ← construction f-string
       "-c:a", "copy", output_path]

# APRÈS (sécurisé)
# Utiliser des guillemets doubles et échappement correct
srt_filter = _build_safe_subtitle_filter(srt_path)
cmd = ["ffmpeg", "-y", "-i", original_video,
       "-vf", srt_filter,
       "-c:a", "copy", output_path]
```

---

### 🟠 [HIGH] - Path traversal sur chemins de sortie

**File:** `processor.py`, `srt_generator.py`
**Description:** Le chemin `output_dir` vient de l'utilisateur (via filedialog). Pas de validation que le chemin est dans un répertoire autorisé. Sur une interface API (main_api.py), ce vecteur devient réel.
**Correction:**
```python
def validate_output_path(output_dir: str) -> str:
    """Normalise et valide le chemin de sortie."""
    path = Path(output_dir).resolve()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    # sur l'API : vérifier que le chemin est dans un répertoire autorisé
    return str(path)
```

---

### 🟡 [MEDIUM] - config.json sans validation de schéma

**File:** `config_manager.py`
**Description:** config.json est chargé sans validation de type. Une valeur corrompue (ex: `"whisper_model_size": null`) peut causer un crash difficile à diagnostiquer.
**Correction:**
```python
SCHEMA = {
    "whisper_model_size": (str, ["tiny","base","small","medium","large-v2","large-v3"]),
    "whisper_device": (str, ["cpu", "cuda"]),
    "whisper_compute_type": (str, ["int8","float16","float32"]),
}

def validate_config(config: dict) -> dict:
    """Valide et corrige le config. Retourne config valide."""
    for key, (expected_type, allowed_values) in SCHEMA.items():
        val = config.get(key)
        if not isinstance(val, expected_type) or val not in allowed_values:
            config[key] = DEFAULTS[key]  # fallback valeur par défaut
    return config
```

---

### 🟡 [MEDIUM] - Pas de .gitignore → risque de commit accidentel de modèles

**Description:** Sans .gitignore, les dossiers `~/.cache/huggingface/` ou un `config.json` avec un chemin sensible pourraient être commités.

---

### 🟢 [LOW] - Fichiers temporaires non supprimés en cas de crash brutal

**File:** `processor.py`
**Description:** Les fichiers WAV temporaires sont nettoyés dans le bloc `finally`, mais un kill -9 ou une coupure d'alimentation laisse des fichiers `/tmp/*.wav` (potentiellement 2.5 Go).
**Correction:** Utiliser `atexit.register()` pour nettoyer les fichiers temporaires connus au démarrage.

---

### Security Checklist Pre-Deployment

```
✅ Aucune clé API hardcodée
✅ subprocess avec liste (pas shell=True)
✅ config.json dans .gitignore
⬜ Valider le schéma config.json
⬜ Valider les chemins de sortie
⬜ Vérifier espace disque avant traitement
⬜ Nettoyer fichiers temp au crash
⬜ Ajouter .gitignore complet
⬜ Tester sur chemin Windows avec espaces et accents
```

---

### Security Score: 72/100 - ⚠️ Mineur requis avant distribution publique

| Domain | Score | Status |
|--------|-------|--------|
| Secrets management | 10/10 | ✅ Aucun secret hardcodé |
| Input validation | 5/10 | ⚠️ Chemins non validés |
| Subprocess security | 7/10 | ⚠️ burn_subtitles f-string |
| Temporary files | 5/10 | ⚠️ Nettoyage incomplet |
| Config security | 5/10 | ⚠️ Pas de validation schéma |
| Dependency security | 8/10 | ✅ Dépendances récentes |
| Error handling | 7/10 | ⚠️ Pas de logging fichier |
| Infrastructure | 10/10 | ✅ 100% local, pas de réseau |
