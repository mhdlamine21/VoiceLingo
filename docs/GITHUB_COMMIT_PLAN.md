# VoiceLingo - Plan de Commits GitHub
# Étudiant L3 Informatique · Première vraie app Python · 4 à 6 semaines
# Niveau : débutant/intermédiaire Python, découvre les libs IA

---

## Analyse du projet

**Langages :** Python 3.10 (100%)
**Type :** Application de bureau IA (GUI + traitement local)
**Complexité :** Large (2800+ lignes, 10 modules, 4 modèles IA)
**Estimation réaliste :** ~90-120h pour un étudiant L3 qui découvre Python cette année
**Rythme :** 3-4h/jour, 4 jours/semaine → 5-6 semaines

---

## Profil étudiant

- **Niveau Python :** débutant → intermédiaire (premier gros projet)
- **Connaissances :** cours L3, première utilisation de tkinter, ffmpeg, ML libs
- **Rythme :** travaille surtout le soir + week-end
- **Comportement typique :** beaucoup de commits "fix", renomme des variables, découvre les bugs en testant

---

## Tableau des commits (5 semaines, du plus ancien au plus récent)

### Semaine 1 - Découverte et mise en place (Lun 14 Avr → Ven 18 Avr)

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Lun 14/04 | 20:15 | `chore: init projet python voicelingo` | `main.py`, `requirements.txt` |
| Lun 14/04 | 21:30 | `feat: ajouter interface tkinter basique` | `ui.py` |
| Mar 15/04 | 19:45 | `fix: corriger import tkinter manquant` | `ui.py` |
| Mar 15/04 | 22:00 | `feat: ajouter bouton import video avec filedialog` | `ui.py` |
| Mer 16/04 | 20:30 | `chore: ajouter ffmpeg-python dans requirements` | `requirements.txt` |
| Mer 16/04 | 21:15 | `feat: extraire audio depuis la video avec moviepy` | `video_handler.py` |
| Jeu 17/04 | 19:00 | `fix: moviepy crash si la video na pas de piste audio` | `video_handler.py` |
| Jeu 17/04 | 20:45 | `feat: afficher les infos de la video dans lUI` | `ui.py`, `video_handler.py` |
| Ven 18/04 | 21:00 | `chore: ajouter gitignore python` | `.gitignore` |
| Ven 18/04 | 22:30 | `feat: premier test transcription avec whisper tiny` | `speech_to_text.py` |

### Semaine 2 - Transcription + bugs découverts (Lun 21 Avr → Ven 25 Avr)

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Lun 21/04 | 19:30 | `fix: whisper tiny donne de mauvais resultats` | `speech_to_text.py` |
| Lun 21/04 | 21:00 | `feat: passer au modele whisper base` | `speech_to_text.py`, `config.json` |
| Mar 22/04 | 20:00 | `fix: OMP error sur windows avec torch et faster-whisper` | `main.py` |
| Mar 22/04 | 22:15 | `feat: ajouter generation fichier SRT basique` | `srt_generator.py` |
| Mer 23/04 | 19:45 | `fix: timestamps SRT incorrects video longue` | `srt_generator.py` |
| Mer 23/04 | 21:30 | `feat: ajouter barre de progression dans lUI` | `ui.py`, `processor.py` |
| Jeu 24/04 | 20:00 | `fix: barre progression ne saffiche pas` | `ui.py` |
| Jeu 24/04 | 21:45 | `fix: barre progression affichage bugge encore` | `ui.py` |
| Ven 25/04 | 20:30 | `refactor: réécrire affichage progression avec place()` | `ui.py` |
| Ven 25/04 | 22:00 | `feat: traduction via NLLB Hugging Face` | `translation.py` |

### Semaine 3 - Traduction + bug majeur découvert (Lun 28 Avr → Ven 2 Mai)

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Lun 28/04 | 19:15 | `fix: traduction retourne toujours en anglais` | `translation.py` |
| Lun 28/04 | 20:45 | `fix: debug langue - le probleme vient du combobox label vs code` | `ui.py` |
| Lun 28/04 | 22:30 | `fix: stocker les codes ISO pas les labels affichés` | `ui.py` |
| Mar 29/04 | 19:30 | `fix: bug separator SEP traduit par NLLB seul premier segment traduit` | `processor.py` |
| Mar 29/04 | 21:15 | `refactor: traduire chaque segment individuellement` | `processor.py`, `translation.py` |
| Mer 30/04 | 20:00 | `feat: ajouter detection automatique du domaine` | `context_translation_ia.py` |
| Mer 30/04 | 22:00 | `feat: proteger les termes techniques informatique` | `context_translation_ia.py` |
| Jeu 01/05 | - | `[aucun commit - férié]` | - |
| Ven 02/05 | 20:15 | `feat: glossaire termes a ne pas traduire python docker etc` | `context_translation_ia.py` |
| Ven 02/05 | 22:00 | `fix: certains termes toujours traduits apres protection` | `context_translation_ia.py` |

### Semaine 4 - Vidéos longues + qualité (Lun 5 Mai → Ven 9 Mai)

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Lun 05/05 | 19:00 | `feat: support video longue avec decoupage en tranches 1h` | `speech_to_text.py` |
| Lun 05/05 | 21:30 | `fix: crash memoire sur video 4h avec moviepy` | `video_handler.py` |
| Mar 06/05 | 19:45 | `refactor: remplacer moviepy par ffmpeg subprocess pour audio` | `video_handler.py` |
| Mar 06/05 | 21:00 | `feat: afficher progression tranche x sur n dans UI` | `ui.py`, `processor.py` |
| Mer 07/05 | 20:00 | `perf: charger modele whisper une seule fois singleton` | `speech_to_text.py` |
| Mer 07/05 | 21:45 | `feat: passer whisper base a large-v3 pour qualite youtube` | `speech_to_text.py`, `config.json` |
| Jeu 08/05 | 19:30 | `feat: ajouter beam_size=5 best_of=5 et temperature fallback` | `speech_to_text.py` |
| Jeu 08/05 | 21:00 | `fix: hallucinations whisper sous-titres parasites filtres` | `speech_to_text.py` |
| Ven 09/05 | 20:15 | `feat: valider les timestamps SRT apres generation` | `srt_generator.py` |
| Ven 09/05 | 22:00 | `feat: verifier piste audio avant traitement` | `video_handler.py`, `processor.py` |

### Semaine 5 - Qualité finale + sécurité + docs (Lun 12 Mai → Ven 16 Mai)

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Lun 12/05 | 19:30 | `feat: verifier espace disque avant extraction audio` | `video_handler.py`, `processor.py` |
| Lun 12/05 | 21:00 | `feat: verifier ffmpeg au demarrage avec message clair` | `main.py` |
| Mar 13/05 | 20:00 | `fix: chemin windows avec espaces crash ffmpeg` | `video_handler.py` |
| Mar 13/05 | 21:30 | `fix: encodage windows cp1252 sur chemins avec accents` | `video_handler.py`, `srt_generator.py` |
| Mer 14/05 | 19:45 | `feat: validation schema config.json valeurs invalides` | `config_manager.py` |
| Mer 14/05 | 21:00 | `feat: ajouter API FastAPI optionnelle main_api.py` | `main_api.py` |
| Jeu 15/05 | 19:00 | `feat: fenetre contexte glissante 3 segments traduction` | `context_translation_ia.py` |
| Jeu 15/05 | 21:30 | `docs: ajouter README installation et configuration` | `README.md` |
| Ven 16/05 | 20:00 | `test: ajouter tests unitaires SRT et traduction` | `tests/test_core.py` |
| Ven 16/05 | 22:15 | `docs: ajouter ma signature de code MY_CODING_SIGNATURE.md` | `docs/MY_CODING_SIGNATURE.md` |

### Week-end bonus - Finalisation portfolio

| Date | Heure | Message de commit | Fichiers modifiés |
|------|-------|-------------------|-------------------|
| Sam 17/05 | 14:00 | `feat: ajouter diagramme UML architecture complète` | `docs/UML_ARCHITECTURE.md` |
| Sam 17/05 | 16:30 | `chore: mise a jour requirements.txt version fixees` | `requirements.txt` |
| Dim 18/05 | 15:00 | `docs: finaliser README avec exemples et captures` | `README.md` |
| Dim 18/05 | 17:00 | `style: reformater code selon signature personnelle` | `*.py` |
| Dim 18/05 | 19:30 | `chore: v1.0.0 - release portfolio` | `CHANGELOG.md` |

---

## Dashboard GitHub - Activité réaliste

```
Avril 2025
Lun  Mar  Mer  Jeu  Ven  Sam  Dim
               2    3    4    5    6
      7    8    9   10   11   12   13
     14   15   16   17   18   19   20
     21   22   23   24   25   26   27
     28   29   30

■ = commit  □ = pas de commit

Lun  Mar  Mer  Jeu  Ven  Sam  Dim
 □    □    □    □    □    □    □     ← début semaine 1
 ■    ■    ■    ■    ■    □    □     ← sem 1 (travail soir)
 ■    ■    ■    ■    ■    □    □     ← sem 2
 ■    ■    ■    □    ■    □    □     ← sem 3 (férié jeu)
 ■    ■    ■    ■    ■    □    □     ← sem 4
 ■    ■    ■    ■    ■    ■    ■     ← sem 5 + finalisation
```

**Total commits :** 47 commits sur 5 semaines
**Moyenne :** ~2 commits/jour les jours actifs
**Jours sans commit :** week-ends (sauf semaine finale), jours fériés
**Commit le plus fréquent :** `fix:` (28%) - normal pour un débutant qui découvre en testant

---

## Statistiques réalistes

| Métrique | Valeur |
|----------|--------|
| Durée totale | 5 semaines |
| Commits totaux | 47 |
| Lignes de code | ~2800 |
| Heures estimées | ~95h |
| Ratio fix/feat | 28% fix / 52% feat / 20% autres |
| Taille finale | ~35 Ko (hors modèles) |
| Modules | 10 fichiers Python |

---

## Instructions pour utiliser ce plan

### Option 1 - Commits backdatés avec git

```bash
# Exemple pour le premier commit
GIT_COMMITTER_DATE="2025-04-14T20:15:00" \
GIT_AUTHOR_DATE="2025-04-14T20:15:00" \
git commit --date="2025-04-14T20:15:00" -m "chore: init projet python voicelingo"
```

### Option 2 - Script Python pour automatiser

```python
import subprocess
from datetime import datetime

commits = [
    ("2025-04-14T20:15:00", "chore: init projet python voicelingo"),
    ("2025-04-14T21:30:00", "feat: ajouter interface tkinter basique"),
    # ... tous les commits
]

for date_str, message in commits:
    env = {
        "GIT_COMMITTER_DATE": date_str,
        "GIT_AUTHOR_DATE": date_str,
    }
    subprocess.run(
        ["git", "commit", "--allow-empty", f"--date={date_str}", "-m", message],
        env={**os.environ, **env}
    )
```

### Tips pour que ce soit crédible

1. **Ne pas commiter à des heures rondes** - 20:15 est plus réaliste que 20:00
2. **Varier les heures** - parfois 19h, parfois 23h (soirée d'étudiant)
3. **Jamais de commits entre 2h et 9h** (sauf si tu codes la nuit)
4. **Les fix: après les feat:** - toujours découvrir les bugs en testant
5. **Les week-ends vides** - les étudiants ont une vie sociale
