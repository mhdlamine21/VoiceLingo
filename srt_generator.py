"""
srt_generator.py - Generation et validation de fichiers de sous-titres SRT.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Transforme les segments ou mots horodates en sous-titres SRT conformes aux standards.
"""

import os
import re

# Nombre maximum de caracteres par ligne (norme de lisibilite standard)
MAX_CHARS_PAR_LIGNE = 42

# Durees minimale et maximale d'un sous-titre en secondes
DUREE_MIN = 0.8
DUREE_MAX = 7.0
MIN_DURATION = DUREE_MIN
MAX_DURATION = DUREE_MAX

# Pause minimale entre deux sous-titres consecutifs (en secondes)
PAUSE_MIN = 0.04
MIN_PAUSE = PAUSE_MIN


def _to_srt_time(secondes: float) -> str:
    """
    Convertit un horodatage en secondes en chaine SRT HH:MM:SS,mmm.
    Exemple: 65.3 -> "00:01:05,300"
    """
    if secondes < 0:
        secondes = 0.0

    heures = int(secondes // 3600)
    minutes = int((secondes % 3600) // 60)
    secs = int(secondes % 60)
    millisecondes = int(round((secondes % 1) * 1000))
    if millisecondes >= 1000:
        secs += 1
        millisecondes -= 1000
        if secs >= 60:
            minutes += 1
            secs -= 60
            if minutes >= 60:
                heures += 1
                minutes -= 60

    return f"{heures:02d}:{minutes:02d}:{secs:02d},{millisecondes:03d}"


secondes_vers_srt = _to_srt_time


def words_to_segments(liste_mots):
    """
    Regroupe les mots en segments de sous-titres.
    On coupe quand :
    - la ligne est trop longue (> 42 caracteres)
    - la pause entre deux mots est grande (> 350ms)
    - la duree du segment depasse 7 secondes
    - il y a de la ponctuation forte (. ! ?)
    """
    if not liste_mots:
        return []

    segments = []
    mots_segment_actuel = []
    debut_segment = liste_mots[0]["start"]

    for i, mot in enumerate(liste_mots):
        mots_segment_actuel.append(mot["word"])

        texte_actuel = " ".join(mots_segment_actuel).strip()
        duree_actuelle = mot["end"] - debut_segment

        # verifier si on doit couper apres ce mot
        doit_couper = False

        # couper si ligne trop longue
        if len(texte_actuel) > MAX_CHARS_PAR_LIGNE * 2:
            doit_couper = True

        # couper si duree trop longue
        elif duree_actuelle > DUREE_MAX:
            doit_couper = True

        # couper si ponctuation forte en fin de mot
        elif mot["word"].rstrip().endswith((".", "!", "?", "...", "…")):
            doit_couper = True

        # couper si grande pause avant le prochain mot
        elif i + 1 < len(liste_mots):
            pause = liste_mots[i + 1]["start"] - mot["end"]
            if pause > 0.35:
                doit_couper = True

        # dernier mot
        elif i == len(liste_mots) - 1:
            doit_couper = True

        if doit_couper and mots_segment_actuel:
            fin_segment = mot["end"]

            # verifier duree minimale
            if fin_segment - debut_segment < DUREE_MIN:
                fin_segment = debut_segment + DUREE_MIN

            segments.append({
                "start": debut_segment,
                "end": fin_segment,
                "text": texte_actuel,
            })

            # reinitialiser pour le segment suivant
            mots_segment_actuel = []
            if i + 1 < len(liste_mots):
                debut_segment = liste_mots[i + 1]["start"]

    return segments


def _couper_ligne_longue(texte):
    """
    Coupe un texte long en 2 lignes de 42 caracteres max.
    Coupe sur le dernier espace avant la limite.
    """
    if len(texte) <= MAX_CHARS_PAR_LIGNE:
        return texte

    # trouver le meilleur endroit pour couper
    milieu = len(texte) // 2
    espace_avant = texte.rfind(" ", 0, milieu + 10)
    espace_apres = texte.find(" ", milieu)

    if espace_avant == -1 and espace_apres == -1:
        return texte  # pas d'espace, on laisse comme ca

    # choisir le point de coupure le plus proche du milieu
    if espace_avant == -1:
        point_coupe = espace_apres
    elif espace_apres == -1:
        point_coupe = espace_avant
    elif abs(espace_avant - milieu) <= abs(espace_apres - milieu):
        point_coupe = espace_avant
    else:
        point_coupe = espace_apres

    ligne1 = texte[:point_coupe].strip()
    ligne2 = texte[point_coupe:].strip()

    return f"{ligne1}\n{ligne2}"


def _corriger_chevauchements(segments):
    """
    Corrige les cas ou un sous-titre chevauche le suivant.
    On raccourcit le premier pour laisser une pause minimum.
    """
    for i in range(len(segments) - 1):
        seg_actuel = segments[i]
        seg_suivant = segments[i + 1]

        if seg_actuel["end"] >= seg_suivant["start"]:
            # chevauchement detecte - on corrige
            nouvelle_fin = seg_suivant["start"] - PAUSE_MIN
            if nouvelle_fin > seg_actuel["start"]:
                segments[i]["end"] = nouvelle_fin

    return segments


def generate_srt(segments, chemin_sortie):
    """
    Ecrit le fichier .srt a partir des segments.
    Encodage UTF-8 BOM pour la compatibilite Windows et VLC.
    """
    if not segments:
        raise ValueError("Aucun segment a ecrire dans le SRT")

    # corriger les chevauchements avant d'ecrire
    segments = _corriger_chevauchements(segments)

    with open(chemin_sortie, "w", encoding="utf-8-sig") as f:
        for numero, segment in enumerate(segments, start=1):
            debut_str = secondes_vers_srt(segment["start"])
            fin_str = secondes_vers_srt(segment["end"])
            texte = _couper_ligne_longue(segment.get("translated_text") or segment["text"])

            # format SRT standard
            f.write(f"{numero}\n")
            f.write(f"{debut_str} --> {fin_str}\n")
            f.write(f"{texte}\n")
            f.write("\n")

    return chemin_sortie


def validate_srt(chemin_srt):
    """
    Verifie que le fichier SRT genere est valide et bien structure.
    Retourne une liste d'erreurs trouvees (vide = tout est conforme).
    """
    erreurs = []

    if not os.path.exists(chemin_srt):
        return ["Le fichier SRT n'existe pas"]

    with open(chemin_srt, "r", encoding="utf-8-sig") as f:
        contenu = f.read()

    blocs = [b for b in contenu.strip().split("\n\n") if b.strip()]

    time_pattern = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")

    def parse_ts(ts_str):
        m = time_pattern.match(ts_str.strip())
        if not m:
            return None
        h, m_val, s, ms = m.groups()
        return int(h) * 3600 + int(m_val) * 60 + int(s) + int(ms) / 1000.0

    for i, bloc in enumerate(blocs):
        lignes = bloc.strip().split("\n")

        if len(lignes) < 3:
            erreurs.append(f"Bloc {i+1}: structure incomplete (< 3 lignes)")
            continue

        # Verification format timestamps
        if " --> " not in lignes[1]:
            erreurs.append(f"Bloc {i+1}: separateur ' --> ' manquant dans le timestamp")
            continue

        parts = lignes[1].split(" --> ")
        if len(parts) != 2:
            erreurs.append(f"Bloc {i+1}: ligne de timestamp mal formee")
            continue

        t_start = parse_ts(parts[0])
        t_end = parse_ts(parts[1])

        if t_start is None or t_end is None:
            erreurs.append(f"Bloc {i+1}: format de timestamp invalide ({lignes[1]})")
        elif t_start >= t_end:
            erreurs.append(
                f"Bloc {i+1}: timestamp debut ({parts[0].strip()}) superieur ou egal a fin ({parts[1].strip()})")

    return erreurs
