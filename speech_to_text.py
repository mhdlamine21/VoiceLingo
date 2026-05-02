"""
speech_to_text.py - Transcription audio automatique avec Whisper.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Convertit le signal audio en texte enrichi avec horodatage mot a mot
             via faster-whisper et decoupage intelligent en tranches.
"""

import os
import tempfile

from video_handler import get_audio_duration, extract_audio_chunk


# duree d'une tranche en secondes (1 heure)
# on decoupe les videos longues pour ne pas saturer la RAM
DUREE_TRANCHE = 3600

# chevauchement entre les tranches en secondes
# pour ne pas perdre les mots qui sont a la jonction
CHEVAUCHEMENT = 30

# on charge le modele une seule fois pour eviter de le recharger
# a chaque traitement (ca prendrait trop longtemps)
_cache_modele = {}


def _charger_modele(taille_modele, device, compute_type):
    """
    Charge le modele Whisper et le garde en memoire.
    Si le modele est deja charge, on le reutilise.
    """
    cle = (taille_modele, device, compute_type)

    if cle not in _cache_modele:
        from faster_whisper import WhisperModel
        print(f"Chargement du modele Whisper {taille_modele} sur {device}...")
        _cache_modele[cle] = WhisperModel(
            taille_modele,
            device=device,
            compute_type=compute_type
        )
        print("Modele charge !")

    return _cache_modele[cle]


def _est_hallucination(texte):
    """
    Detecte les hallucinations de Whisper.
    Whisper genere parfois des phrases parasites repetitives.
    """
    if not texte or not texte.strip():
        return True

    texte_lower = texte.lower().strip()

    # phrases parasites connues de Whisper
    phrases_parasites = [
        "merci d'avoir regarde",
        "thanks for watching",
        "merci d'avoir suivi",
        "sous-titres realises par",
        "sous-titres par",
        "abonnez-vous",
        "subscribe",
        "like and subscribe",
    ]

    for phrase in phrases_parasites:
        if phrase in texte_lower:
            return True

    # detecter les repetitions (whisper boucle parfois)
    mots = texte_lower.split()
    if len(mots) >= 4:
        # si les 4 premiers mots se repetent
        moitie = len(mots) // 2
        if mots[:moitie] == mots[moitie:moitie * 2]:
            return True

    return False


def _transcrire_tranche(modele, chemin_audio, langue_src, config):
    """
    Transcrit un fichier audio et retourne les mots avec leurs timestamps.
    """
    # parametres de qualite maximale
    options = {
        "beam_size": 5,
        "best_of": 5,
        "vad_filter": True,        # filtre les silences avec Silero VAD
        "word_timestamps": True,     # timestamps par mot (pas par segment)
        "condition_on_previous_text": True,
    }

    # si la langue n'est pas auto, on la precise
    if langue_src and langue_src != "auto":
        options["language"] = langue_src

    segments, infos = modele.transcribe(chemin_audio, **options)

    # extraire tous les mots avec leurs timestamps
    tous_les_mots = []
    langue_detectee = infos.language if hasattr(infos, "language") else "en"

    for segment in segments:
        # ignorer les hallucinations
        if _est_hallucination(segment.text):
            continue

        # extraire les mots du segment
        if hasattr(segment, "words") and segment.words:
            for mot in segment.words:
                tous_les_mots.append({
                    "word": mot.word,
                    "start": mot.start,
                    "end": mot.end,
                })

    return tous_les_mots, langue_detectee


def transcribe(chemin_audio, langue_src="auto", config=None, progress_cb=None):
    """
    Transcrit un fichier audio complet.
    Decoupe en tranches de 1h pour les videos longues.

    Retourne : (texte_complet, langue_detectee, liste_des_mots)
    """
    if config is None:
        config = {}

    # charger le modele
    taille = config.get("whisper_model_size", "base")
    device = config.get("whisper_device", "cpu")
    compute = config.get("whisper_compute_type", "int8")

    modele = _charger_modele(taille, device, compute)

    # calculer la duree totale
    duree_totale = get_audio_duration(chemin_audio)
    print(f"Duree de l'audio: {duree_totale:.1f} secondes")

    # si l'audio est court, on le transcrit en une seule fois
    if duree_totale <= DUREE_TRANCHE:
        if progress_cb:
            progress_cb(25, "Transcription Whisper en cours...")

        mots, langue = _transcrire_tranche(modele, chemin_audio, langue_src, config)

        if progress_cb:
            progress_cb(40, "Transcription terminee")

        texte_complet = " ".join(m["word"] for m in mots)
        return texte_complet, langue, mots

    # pour les videos longues : decouper en tranches
    nombre_tranches = int(duree_totale / DUREE_TRANCHE) + 1
    print(f"Video longue: {nombre_tranches} tranches de 1h")

    tous_les_mots = []
    langue_detectee = "en"

    for numero_tranche in range(nombre_tranches):
        # calcul du debut et de la fin de la tranche
        debut = numero_tranche * DUREE_TRANCHE
        if debut > 0:
            debut = max(0, debut - CHEVAUCHEMENT)

        fin = min(duree_totale, (numero_tranche + 1) * DUREE_TRANCHE)
        duree_tranche = fin - debut

        if duree_tranche <= 0:
            break

        # mettre a jour la progression
        if progress_cb:
            pct = 20 + int((numero_tranche / nombre_tranches) * 20)
            msg = (
                f"Transcription Whisper - "
                f"tranche {numero_tranche + 1}/{nombre_tranches} - "
                f"{int(debut // 3600)}h {int((debut % 3600) // 60)}m "
                f"→ {int(fin // 3600)}h {int((fin % 3600) // 60)}m"
            )
            progress_cb(pct, msg)

        # extraire la tranche audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            chemin_tranche = f.name

        try:
            extract_audio_chunk(chemin_audio, chemin_tranche, debut, duree_tranche)
            mots_tranche, langue = _transcrire_tranche(
                modele, chemin_tranche, langue_src, config
            )

            # ajuster les timestamps avec le decalage
            for mot in mots_tranche:
                mot["start"] += debut
                mot["end"] += debut

            tous_les_mots.extend(mots_tranche)
            langue_detectee = langue

        finally:
            # supprimer le fichier temporaire
            if os.path.exists(chemin_tranche):
                os.remove(chemin_tranche)

    # trier les mots par ordre chronologique
    tous_les_mots.sort(key=lambda m: m["start"])

    texte_complet = " ".join(m["word"] for m in tous_les_mots)
    return texte_complet, langue_detectee, tous_les_mots
