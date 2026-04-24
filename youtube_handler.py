"""
youtube_handler.py - Telechargement et extraction de videos YouTube avec yt-dlp.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Telechargement securise de videos ou pistes audio YouTube pour le traitement local.
"""

import os
import re


def is_youtube_url(url):
    """Verifie si l'URL est une URL YouTube valide."""
    patterns = [
        r"youtube\.com/watch\?v=",
        r"youtube\.com/playlist\?list=",
        r"youtu\.be/",
        r"youtube\.com/shorts/",
    ]
    for pattern in patterns:
        if re.search(pattern, url.strip()):
            return True
    return False


def get_video_info_youtube(url):
    """
    Recupere les infos d'une video ou playlist YouTube.
    Ne telecharge rien - juste les metadonnees.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError(
            "yt-dlp n'est pas installe.\n"
            "Installez-le avec: pip install yt-dlp"
        )

    options = {
        "quiet":         True,
        "no_warnings":   True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        infos = ydl.extract_info(url, download=False)

    if not infos:
        raise ValueError(f"Impossible de recuperer les infos: {url}")

    # playlist ou video unique ?
    if infos.get("_type") == "playlist":
        videos = infos.get("entries", [])
        return {
            "type":    "playlist",
            "title":   infos.get("title", "Playlist"),
            "channel": infos.get("uploader", ""),
            "count":   len(videos),
        }

    # video unique
    duree = infos.get("duration", 0) or 0
    heures   = int(duree // 3600)
    minutes  = int((duree % 3600) // 60)
    secondes = int(duree % 60)

    if heures > 0:
        duree_str = f"{heures}h {minutes}m {secondes}s"
    else:
        duree_str = f"{minutes}m {secondes}s"

    # langues de sous-titres disponibles
    sous_titres = list(infos.get("subtitles", {}).keys())
    sous_titres_auto = list(infos.get("automatic_captions", {}).keys())
    toutes_langues = list(set(sous_titres + sous_titres_auto))

    return {
        "type":             "video",
        "title":            infos.get("title", ""),
        "channel":          infos.get("uploader", ""),
        "duration":         duree,
        "duration_str":     duree_str,
        "subtitles_langs":  toutes_langues,
        "has_manual_subs":  bool(sous_titres),
        "has_auto_subs":    bool(sous_titres_auto),
    }


def download_video(url, dossier_sortie, qualite="720p", progress_cb=None):
    """
    Telecharge une video YouTube en MP4.
    Retourne le chemin du fichier telecharge.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("Installez yt-dlp avec: pip install yt-dlp")

    # correspondance qualite -> format yt-dlp
    formats = {
        "best":       "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "1080p":      "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "720p":       "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "480p":       "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        "audio_only": "bestaudio[ext=m4a]/bestaudio",
    }
    format_choisi = formats.get(qualite, formats["720p"])

    chemin_telecharge = [None]

    def hook_progression(d):
        if not progress_cb:
            return
        if d.get("status") == "downloading":
            total   = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            actuel  = d.get("downloaded_bytes", 0)
            vitesse = d.get("_speed_str", "").strip()
            eta     = d.get("_eta_str", "").strip()
            if total > 0:
                pct = int(actuel * 100 / total)
                progress_cb(pct, f"Telechargement {pct}% - {vitesse} - ETA {eta}")
        elif d.get("status") == "finished":
            chemin_telecharge[0] = d.get("filename")
            if progress_cb:
                progress_cb(100, "Telechargement termine !")

    options = {
        "format":              format_choisi,
        "outtmpl":             os.path.join(dossier_sortie, "%(title)s.%(ext)s"),
        "progress_hooks":      [hook_progression],
        "quiet":               True,
        "no_warnings":         True,
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        infos = ydl.extract_info(url, download=True)

        # retrouver le chemin du fichier telecharge
        if not chemin_telecharge[0]:
            chemin_telecharge[0] = ydl.prepare_filename(infos)

    chemin = chemin_telecharge[0]
    if not chemin or not os.path.exists(chemin):
        # chercher dans le dossier de sortie
        for fichier in os.listdir(dossier_sortie):
            if fichier.endswith((".mp4", ".mkv", ".webm")):
                return os.path.join(dossier_sortie, fichier)
        raise FileNotFoundError("Fichier telecharge introuvable")

    return chemin


def download_subtitles_only(url, dossier_sortie, langue="fr"):
    """
    Telecharge uniquement les sous-titres d'une video YouTube.
    Ne telecharge pas la video.
    Retourne le chemin du fichier .srt ou None.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("Installez yt-dlp avec: pip install yt-dlp")

    options = {
        "writesubtitles":    True,
        "writeautomaticsub": True,
        "subtitleslangs":    [langue],
        "subtitlesformat":   "srt",
        "skip_download":     True,
        "outtmpl":           os.path.join(dossier_sortie, "%(title)s.%(ext)s"),
        "quiet":             True,
        "no_warnings":       True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        infos = ydl.extract_info(url, download=True)

    if not infos:
        return None

    # chercher le fichier SRT dans le dossier de sortie
    for fichier in os.listdir(dossier_sortie):
        if fichier.endswith(".srt"):
            return os.path.join(dossier_sortie, fichier)

    return None
