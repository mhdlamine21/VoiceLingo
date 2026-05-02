"""
config_manager.py - Gestion centralisee de la configuration VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Charge, valide et persiste les preferences utilisateurs dans config.json.
"""

import json
import os

# Chemin par defaut du fichier de configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
CHEMIN_CONFIG = CONFIG_PATH

# Valeurs par defaut garantissant un demarrage sans crash
DEFAULTS = {
    "whisper_model_size": "base",
    "whisper_device": "cpu",
    "whisper_compute_type": "int8",
    "nllb_model": "facebook/nllb-200-distilled-600M",
    "tts_model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "tts_speaker_wav": "",
    "output_dir": "",
}
CONFIG_DEFAUT = DEFAULTS

# Ensembles des parametres autorises
VALEURS_VALIDES = {
    "whisper_model_size": ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
    "whisper_device": ["cpu", "cuda"],
    "whisper_compute_type": ["int8", "int8_float16", "float16", "float32"],
}


def load_config():
    """
    Charge la configuration depuis le fichier json configure.
    Si le fichier est absent ou corrompu, applique les valeurs par defaut.
    """
    config = dict(DEFAULTS)
    target_path = str(CONFIG_PATH)

    if not os.path.exists(target_path):
        return config

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(
            f"Avertissement: Erreur de lecture de {target_path} ({e}) - utilisation des valeurs par defaut.")
        return config

    # Validation et assainissement des entrees
    for cle, valeur_defaut in DEFAULTS.items():
        valeur = donnees.get(cle, valeur_defaut)

        if cle in VALEURS_VALIDES:
            if valeur not in VALEURS_VALIDES[cle]:
                valeur = valeur_defaut

        config[cle] = valeur

    return config


def save_config(config):
    """Sauvegarde de facon atomique et securisee la configuration."""
    target_path = str(CONFIG_PATH)
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Erreur de sauvegarde de {target_path}: {e}")
