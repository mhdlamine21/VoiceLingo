"""
text_to_speech.py - Synthese vocale multilingue avec Coqui XTTS-v2 et repli local pyttsx3.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Genere une piste audio doublee a partir du texte des sous-titres traduits.
"""

import os


def synthesize_speech(segments, langue, chemin_sortie, config=None):
    """
    Synthetise la voix pour tous les segments traduits.
    Essaie d'abord XTTS-v2 (meilleure qualite), sinon pyttsx3 (basique).
    """
    if config is None:
        config = {}

    # essayer avec Coqui XTTS-v2
    try:
        _synthese_xtts(segments, langue, chemin_sortie, config)
        return
    except ImportError:
        print("Coqui TTS non installe, utilisation de pyttsx3")
    except Exception as e:
        print(f"Erreur XTTS: {e}, utilisation de pyttsx3")

    # fallback sur pyttsx3 (qualite basique mais toujours present)
    _synthese_pyttsx3(segments, langue, chemin_sortie)


def _synthese_xtts(segments, langue, chemin_sortie, config):
    """Synthese avec Coqui XTTS-v2 (haute qualite, 17 langues)."""
    from TTS.api import TTS

    modele = config.get("tts_model", "tts_models/multilingual/multi-dataset/xtts_v2")
    wav_reference = config.get("tts_speaker_wav", "")

    tts = TTS(modele)

    # construire le texte complet
    texte_complet = " ".join(
        s.get("translated_text", s.get("text", ""))
        for s in segments
        if s.get("translated_text") or s.get("text")
    )

    if not texte_complet.strip():
        raise ValueError("Aucun texte a synthétiser")

    # synthese avec ou sans clonage de voix
    if wav_reference and os.path.exists(wav_reference):
        tts.tts_to_file(
            text=texte_complet,
            speaker_wav=wav_reference,
            language=langue,
            file_path=chemin_sortie
        )
    else:
        # utiliser le premier speaker disponible
        speakers = tts.speakers
        speaker = speakers[0] if speakers else None
        tts.tts_to_file(
            text=texte_complet,
            speaker=speaker,
            language=langue,
            file_path=chemin_sortie
        )


def _synthese_pyttsx3(segments, langue, chemin_sortie):
    """Synthese basique avec pyttsx3 (fallback)."""
    import pyttsx3

    moteur = pyttsx3.init()

    # construire le texte complet
    texte_complet = " ".join(
        s.get("translated_text", s.get("text", ""))
        for s in segments
        if s.get("translated_text") or s.get("text")
    )

    # sauvegarder en fichier audio
    moteur.save_to_file(texte_complet, chemin_sortie)
    moteur.runAndWait()
