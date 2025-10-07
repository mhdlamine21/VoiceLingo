"""
video_handler.py - Gestion des operations video et audio via FFmpeg.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Extraction audio, sondage ffprobe des metadonnees, incrustation de sous-titres
             et remplacement de piste audio sans re-encodage video inutile.
"""

import os
import json
import shutil
import subprocess


def get_video_info(chemin_video):
    """
    Lit les informations d'une video (duree, taille, format)
    sans charger tout le fichier en memoire.
    Utilise ffprobe pour ca.
    """
    # commande ffprobe pour avoir les infos en JSON
    commande = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        chemin_video
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"ffprobe a echoue: {resultat.stderr}")

    donnees = json.loads(resultat.stdout)

    # extraire la duree depuis le format
    duree_secondes = float(donnees.get("format", {}).get("duration", 0))
    taille_octets = os.path.getsize(chemin_video)

    # convertir la duree en string lisible
    heures = int(duree_secondes // 3600)
    minutes = int((duree_secondes % 3600) // 60)
    secondes = int(duree_secondes % 60)

    if heures > 0:
        duree_str = f"{heures}h {minutes}m {secondes}s"
    else:
        duree_str = f"{minutes}m {secondes}s"

    # taille en Mo
    taille_mo = round(taille_octets / (1024 * 1024), 1)

    # format du conteneur
    format_nom = donnees.get("format", {}).get("format_long_name", "Video")
    if "mp4" in format_nom.lower():
        format_court = "MP4"
    elif "avi" in format_nom.lower():
        format_court = "AVI"
    elif "matroska" in format_nom.lower():
        format_court = "MKV"
    else:
        format_court = format_nom[:10]

    return {
        "name":         os.path.basename(chemin_video),
        "duration":     duree_secondes,
        "duration_str": duree_str,
        "size_mb":      taille_mo,
        "format":       format_court,
    }


def check_has_audio(chemin_video):
    """
    Verifie qu'il y a bien une piste audio dans la video.
    Renvoie True si oui, False sinon.
    """
    commande = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        chemin_video
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        return False

    donnees = json.loads(resultat.stdout)
    streams = donnees.get("streams", [])

    # chercher une piste audio parmi les streams
    for stream in streams:
        if stream.get("codec_type") == "audio":
            return True

    return False


def check_disk_space(chemin_video, dossier_sortie):
    """
    Verifie qu'il y a assez d'espace disque pour traiter la video.
    On estime qu'il faut environ 2.5x la taille de la video.
    """
    taille_video = os.path.getsize(chemin_video)
    espace_necessaire = int(taille_video * 2.5)
    espace_disponible = shutil.disk_usage(dossier_sortie).free

    return {
        "ok":                espace_disponible >= espace_necessaire,
        "necessaire_mo":     round(espace_necessaire / (1024 * 1024), 1),
        "disponible_mo":     round(espace_disponible / (1024 * 1024), 1),
        "needed_gb":         round(espace_necessaire / (1024 * 1024 * 1024), 4),
        "available_gb":      round(espace_disponible / (1024 * 1024 * 1024), 4),
    }


def extract_audio(chemin_video, chemin_sortie):
    """
    Extrait la piste audio de la video en WAV 16kHz mono.
    16kHz et mono c'est ce que Whisper attend en entree.
    """
    commande = [
        "ffmpeg",
        "-y",                   # ecraser si le fichier existe deja
        "-i", chemin_video,
        "-vn",                  # pas de video dans la sortie
        "-ar", "16000",         # 16000 Hz = 16kHz
        "-ac", "1",             # 1 canal = mono
        "-acodec", "pcm_s16le", # format WAV standard
        chemin_sortie
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Extraction audio echouee:\n{resultat.stderr}")


def get_audio_duration(chemin_audio):
    """Retourne la duree d'un fichier audio en secondes."""
    commande = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        chemin_audio
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        return 0.0

    donnees = json.loads(resultat.stdout)
    return float(donnees.get("format", {}).get("duration", 0))


def extract_audio_chunk(chemin_audio, chemin_sortie, debut, duree):
    """
    Extrait un morceau du fichier audio (pour les videos longues).
    debut et duree sont en secondes.
    """
    commande = [
        "ffmpeg",
        "-y",
        "-i", chemin_audio,
        "-ss", str(debut),      # debut de l'extrait
        "-t", str(duree),       # duree de l'extrait
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        chemin_sortie
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Extraction tranche echouee:\n{resultat.stderr}")


def replace_audio_track(chemin_video, chemin_audio_nouveau, chemin_sortie):
    """
    Remplace la piste audio d'une video par un nouvel audio.
    -c:v copy = on copie la video sans la re-encoder (rapide)
    """
    commande = [
        "ffmpeg",
        "-y",
        "-i", chemin_video,
        "-i", chemin_audio_nouveau,
        "-map", "0:v:0",        # prendre la video du 1er fichier
        "-map", "1:a:0",        # prendre l'audio du 2eme fichier
        "-c:v", "copy",         # copier la video sans re-encoder
        "-c:a", "aac",          # encoder l'audio en AAC
        chemin_sortie
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Remplacement audio echoue:\n{resultat.stderr}")


def burn_subtitles(chemin_video, chemin_srt, chemin_sortie):
    """
    Incruste les sous-titres dans la video (hardcoded subtitles).
    """
    # echapper le chemin pour le filtre subtitles de ffmpeg
    chemin_srt_echappe = chemin_srt.replace("\\", "/").replace(":", "\\:")

    commande = [
        "ffmpeg",
        "-y",
        "-i", chemin_video,
        "-vf", f"subtitles='{chemin_srt_echappe}'",
        "-c:a", "copy",
        chemin_sortie
    ]

    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Incrustation sous-titres echouee:\n{resultat.stderr}")
