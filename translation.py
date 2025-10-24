"""
translation.py - Module de compatibilite et redirection vers le moteur de traduction contextuelle.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Expose les fonctions de traduction de context_translation_ia pour maintenir la retrocompatibilite.
"""

from context_translation_ia import translate_segments_batch, detect_domain, get_glossary, protect_terms, restore_terms

__all__ = ["translate_segments_batch", "detect_domain", "get_glossary", "protect_terms", "restore_terms"]
