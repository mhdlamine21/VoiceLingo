"""
context_translation_ia.py - Traduction neuronale contextuelle NLLB avec preservation des termes techniques.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Traduit les segments de sous-titres en detectant le domaine (informatique, sciences...)
             et en protegeant les mots-cles techniques pour eviter les contresens.
"""

import re


# correspondance codes ISO -> codes FLORES-200 requis par NLLB
CODES_NLLB = {
    "fr": "fra_Latn",
    "en": "eng_Latn",
    "es": "spa_Latn",
    "de": "deu_Latn",
    "it": "ita_Latn",
    "pt": "por_Latn",
    "ja": "jpn_Jpan",
    "zh": "zho_Hans",
    "ar": "arb_Arab",
}

# mots-cles pour detecter le domaine du contenu
MOTS_CLES_DOMAINE = {
    "informatique": [
        "function", "class", "variable", "loop", "array", "object",
        "python", "javascript", "algorithm", "database", "api",
        "docker", "git", "neural", "gradient", "tensor", "model",
    ],
    "mathematiques": [
        "theorem", "proof", "matrix", "integral", "derivative",
        "probability", "vector", "eigenvalue", "calculus",
    ],
    "physique": [
        "electron", "quantum", "energy", "wave", "particle",
        "thermodynamics", "relativity", "momentum",
    ],
    "medecine": [
        "patient", "diagnosis", "treatment", "symptom", "clinical",
        "surgery", "therapy", "disease", "medical",
    ],
    "biologie": [
        "cell", "protein", "gene", "dna", "rna", "evolution",
        "organism", "species", "chromosome",
    ],
}

# termes a ne PAS traduire par domaine
TERMES_A_GARDER = {
    "informatique": {
        "Python", "JavaScript", "TypeScript", "Java", "C++", "Rust",
        "function", "class", "return", "async", "await", "callback",
        "API", "REST", "JSON", "HTML", "CSS", "SQL", "Docker",
        "Git", "GitHub", "npm", "pip", "import", "export",
        "True", "False", "None", "null", "undefined",
        "gradient", "tensor", "model", "dataset", "epoch",
        "neural", "network", "layer", "batch", "loss",
    },
    "mathematiques": {
        "matrix", "vector", "tensor", "sigma", "lambda", "theta",
        "pi", "alpha", "beta", "delta", "epsilon",
    },
    "physique": {
        "Newton", "Einstein", "Maxwell", "Planck", "quark", "boson",
        "photon", "lepton", "electron", "proton",
    },
    "general": set(),
}

# on charge le modele une seule fois
_pipeline_traduction = None


def _charger_pipeline(modele_nllb):
    """Charge le pipeline de traduction NLLB."""
    global _pipeline_traduction
    if _pipeline_traduction is None:
        from transformers import pipeline
        print(f"Chargement du modele NLLB: {modele_nllb}")
        _pipeline_traduction = pipeline("translation", model=modele_nllb)
        print("Modele NLLB charge !")
    return _pipeline_traduction


def detect_domain(texte):
    """
    Detecte le domaine du contenu en comptant les mots-cles.
    Analyse les 3000 premiers caracteres seulement.
    """
    texte_a_analyser = texte[:3000].lower()
    scores = {}

    for domaine, mots_cles in MOTS_CLES_DOMAINE.items():
        score = sum(1 for mot in mots_cles if mot in texte_a_analyser)
        scores[domaine] = score

    # retourner le domaine avec le plus de mots-cles
    meilleur_domaine = max(scores, key=scores.get)

    if scores[meilleur_domaine] == 0:
        return "general"

    return meilleur_domaine


def _proteger_termes(texte, termes_a_garder):
    """
    Remplace les termes techniques par des tokens avant la traduction.
    Exemple: "use a function" -> "use a __TK0__"
    On les trie du plus long au plus court pour eviter les sous-chaines.
    """
    termes_tries = sorted(termes_a_garder, key=len, reverse=True)
    correspondances = {}
    compteur = 0

    for terme in termes_tries:
        # chercher le terme avec des frontieres de mots
        pattern = r"(?<!\w)" + re.escape(terme) + r"(?!\w)"
        if re.search(pattern, texte, re.IGNORECASE):
            token = f"__TK{compteur}__"
            correspondances[token] = terme
            texte = re.sub(pattern, token, texte, flags=re.IGNORECASE)
            compteur += 1

    return texte, correspondances


def _restaurer_termes(texte, correspondances):
    """Remet les termes techniques a la place des tokens."""
    for token, terme_original in correspondances.items():
        texte = texte.replace(token, terme_original)

    # nettoyer les tokens restants qui n'ont pas ete restaures
    texte = re.sub(r"__TK\d+__", "", texte)
    return texte.strip()


def get_glossary(domaine="informatique", lang="fr"):
    """
    Retourne le glossaire de termes a preserver pour un domaine donne.
    Permet de preserver les mots cles du code, maths ou sciences.
    """
    return set(TERMES_A_GARDER.get(domaine, TERMES_A_GARDER.get("general", set())))


protect_terms = _proteger_termes
restore_terms = _restaurer_termes


def translate_segments_batch(segments, langue_src, langue_cible, config=None, progress_cb=None):
    """
    Traduit une liste de segments.
    On traduit segment par segment (pas en batch) pour eviter le bug du separateur.

    BUG CORRIGE: si on joint les segments avec un separateur et qu'on envoie tout
    a NLLB en une fois, NLLB traduit aussi le separateur et on perd tous les
    segments sauf le premier quand on re-split.
    Solution: traduire chaque segment individuellement.
    """
    if config is None:
        config = {}

    modele_nllb = config.get("nllb_model", "facebook/nllb-200-distilled-600M")

    # verifier que les codes de langue sont supportes
    code_cible = CODES_NLLB.get(langue_cible)
    if not code_cible:
        print(f"Langue '{langue_cible}' non supportee, on garde en anglais")
        return segments

    # charger le modele
    traducteur = _charger_pipeline(modele_nllb)

    # detecter le domaine pour choisir le bon glossaire
    texte_complet = " ".join(s["text"] for s in segments)
    domaine = detect_domain(texte_complet)
    print(f"Domaine detecte: {domaine}")

    termes_a_garder = TERMES_A_GARDER.get(domaine, set())

    # traduire chaque segment un par un
    segments_traduits = []
    contexte_precedent = ""  # garde les 3 derniers segments traduits pour le contexte

    for i, segment in enumerate(segments):
        # mettre a jour la progression
        if progress_cb and i % 5 == 0:
            pct = 40 + int((i / len(segments)) * 20)
            progress_cb(pct, f"Traduction [{domaine}] {i+1}/{len(segments)} → {langue_cible.upper()}")

        texte_original = segment["text"].strip()
        if not texte_original:
            segments_traduits.append({**segment, "translated_text": ""})
            continue

        try:
            # proteger les termes techniques
            texte_protege, correspondances = _proteger_termes(texte_original, termes_a_garder)

            # ajouter le contexte des segments precedents
            texte_avec_contexte = texte_protege
            if contexte_precedent:
                texte_avec_contexte = contexte_precedent + " " + texte_protege

            # traduire avec NLLB
            resultat = traducteur(
                texte_avec_contexte,
                src_lang=CODES_NLLB.get(langue_src, "eng_Latn"),
                tgt_lang=code_cible,
                max_length=512
            )

            texte_traduit = resultat[0]["translation_text"]

            # si on a mis du contexte, enlever la partie contexte de la traduction
            # (approximatif - on garde juste la fin)
            if contexte_precedent and len(texte_traduit) > len(texte_protege) * 2:
                mots_traduits = texte_traduit.split()
                mots_originaux = texte_protege.split()
                ratio = len(mots_traduits) / max(len(mots_originaux), 1)
                nb_mots_a_garder = max(1, int(len(mots_originaux) * ratio))
                texte_traduit = " ".join(mots_traduits[-nb_mots_a_garder:])

            # restaurer les termes techniques
            texte_final = _restaurer_termes(texte_traduit, correspondances)

            # mettre a jour le contexte (garder les 3 derniers)
            contexte_precedent = " ".join(
                (contexte_precedent + " " + texte_traduit).split()[-50:]
            )

        except Exception as e:
            print(f"Erreur traduction segment {i}: {e}")
            texte_final = texte_original  # garder l'original si erreur

        segments_traduits.append({
            **segment,
            "translated_text": texte_final,
            "domain": domaine,
        })

    return segments_traduits
