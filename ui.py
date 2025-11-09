"""
ui.py - Interface graphique utilisateur moderne et responsive pour VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Interface ergonomique Tkinter a 3 panneaux avec gestion de theme sombre/clair,
             guide d'utilisation exhaustif integre, support vectoriel pour le logo,
             importation de fichiers locaux et telechargement YouTube via yt-dlp.
"""

import os
import re
import sys
import webbrowser
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Dict, Any

from config_manager import load_config, save_config
from processor import ProcessingPipeline
from youtube_handler import is_youtube_url, get_video_info_youtube, download_video


# Palettes de couleurs modernes et contraste soigneusement calibre

THEMES = {
    "light": {
        "bg_app": "#f8fafc",
        "bg_header": "#1e3a8a",
        "bg_header_btn": "#2563eb",
        "bg_header_btn_hover": "#1d4ed8",
        "bg_panel": "#ffffff",
        "bg_card": "#ffffff",
        "bg_card_selected": "#eff6ff",
        "bg_card_hover": "#f1f5f9",
        "bg_badge": "#dbeafe",
        "fg_badge": "#1d4ed8",
        "fg_header_title": "#ffffff",
        "fg_header_sub": "#bfdbfe",
        "fg_title": "#0f172a",
        "fg_text": "#334155",
        "fg_subtext": "#64748b",
        "border": "#e2e8f0",
        "border_selected": "#2563eb",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "success": "#16a34a",
        "success_bg": "#f0fdf4",
        "warning": "#d97706",
        "warning_bg": "#fffbeb",
        "danger": "#dc2626",
        "progress_bg": "#e2e8f0",
        "progress_fill": "#2563eb",
        "input_bg": "#ffffff",
        "input_fg": "#0f172a",
    },
    "dark": {
        "bg_app": "#0b0f19",
        "bg_header": "#0f172a",
        "bg_header_btn": "#1e293b",
        "bg_header_btn_hover": "#334155",
        "bg_panel": "#111827",
        "bg_card": "#1e293b",
        "bg_card_selected": "#1e3a8a",
        "bg_card_hover": "#334155",
        "bg_badge": "#1e3a8a",
        "fg_badge": "#93c5fd",
        "fg_header_title": "#ffffff",
        "fg_header_sub": "#94a3b8",
        "fg_title": "#ffffff",
        "fg_text": "#f1f5f9",
        "fg_subtext": "#94a3b8",
        "border": "#334155",
        "border_selected": "#60a5fa",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "success": "#22c55e",
        "success_bg": "#064e3b",
        "warning": "#f59e0b",
        "warning_bg": "#451a03",
        "danger": "#ef4444",
        "progress_bg": "#334155",
        "progress_fill": "#3b82f6",
        "input_bg": "#1e293b",
        "input_fg": "#ffffff",
    }
}


LANGUES_SOURCE = [
    ("Auto-detecter", "auto"),
    ("Anglais", "en"),
    ("Francais", "fr"),
    ("Espagnol", "es"),
    ("Allemand", "de"),
    ("Italien", "it"),
    ("Portugais", "pt"),
    ("Arabe", "ar"),
    ("Chinois", "zh"),
    ("Japonais", "ja"),
]

LANGUES_CIBLE = [
    ("Francais", "fr"),
    ("Anglais", "en"),
    ("Espagnol", "es"),
    ("Allemand", "de"),
    ("Italien", "it"),
    ("Portugais", "pt"),
    ("Arabe", "ar"),
]

CODES_LANGUES = {lbl: code for lbl, code in LANGUES_SOURCE + LANGUES_CIBLE}

ETAPES_PIPELINE = [
    ("Analyse video",         0,  5),
    ("Extraction audio",      5, 20),
    ("Transcription Whisper", 20, 40),
    ("Traduction NLLB",       40, 62),
    ("Generation SRT",        62, 78),
    ("Finalisation",          78, 100),
]


class VoiceLingoApp:
    """
    Application graphique principale pour VoiceLingo.
    Propose un agencement moderne en 3 panneaux :
    - Panneau gauche : Configuration des langues et modes de sortie
    - Panneau central : Zone d'import dynamique (fichier local ou YouTube) et execution
    - Panneau droit : Synthese en temps reel, domaine detecte et apercu des fichiers
    """

    def __init__(self, fenetre: tk.Tk):
        self.fenetre = fenetre
        self.fenetre.title("VoiceLingo - Transcription et Traduction Video")
        self.fenetre.geometry("1120x720")
        self.fenetre.minsize(1020, 640)

        self._configurer_icone_fenetre()

        # Chargement de la configuration
        self.config = load_config()

        # Variables d'etat
        self.is_dark_mode = False
        self.theme = THEMES["light"]
        self.chemin_video: Optional[str] = None
        self.pipeline: Optional[ProcessingPipeline] = None
        self.is_processing = False
        self.active_tab = "local"  # "local" ou "youtube"

        # Variables de selection
        self.langue_source_var = tk.StringVar(value="Auto-detecter")
        self.langue_cible_var = tk.StringVar(value="Francais")
        self.mode_sortie_var = tk.StringVar(value="srt")
        self.incruster_var = tk.BooleanVar(value=False)
        self.youtube_url_var = tk.StringVar(value="")

        # References dynamiques de widgets
        self.label_etape = None
        self.label_pourcent = None
        self.barre_progress = None
        self.label_tranche = None
        self.bouton_demarrer = None
        self.bouton_annuler = None
        self.frame_progress = None
        self.widgets_etapes = {}
        self.label_domaine = None
        self._cartes_radio = {}

        # Style ttk et theme
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._appliquer_style_ttk()

        # Construction de l'interface
        self._construire_interface()

    def _configurer_icone_fenetre(self):
        """Assigne l'icone a la fenetre principale si disponible."""
        ico_path = os.path.join(os.path.dirname(__file__), "assets", "icons", "logo.ico")
        if os.path.exists(ico_path):
            try:
                self.fenetre.iconbitmap(ico_path)
            except Exception:
                pass

    def _appliquer_style_ttk(self):
        """Configure les styles des composants ttk pour un affichage fidele au theme."""
        t = self.theme

        # Style Combobox
        self.style.configure(
            "TCombobox",
            fieldbackground=t["input_bg"],
            background=t["bg_card"],
            foreground=t["input_fg"],
            arrowcolor=t["accent"],
            darkcolor=t["border"],
            lightcolor=t["border"],
            bordercolor=t["border"],
            padding=4
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["input_bg"])],
            foreground=[("readonly", t["input_fg"])],
            selectbackground=[("readonly", t["accent"])],
            selectforeground=[("readonly", "#ffffff")]
        )

        # Style Entry
        self.style.configure(
            "TEntry",
            fieldbackground=t["input_bg"],
            foreground=t["input_fg"],
            insertcolor=t["fg_title"],
            bordercolor=t["border"],
            lightcolor=t["border"],
            darkcolor=t["border"],
            padding=4
        )

        # Style Scrollbar
        self.style.configure(
            "Vertical.TScrollbar",
            background=t["bg_card"],
            troughcolor=t["bg_app"],
            bordercolor=t["border"],
            arrowcolor=t["fg_subtext"]
        )

        # Assurer que les popups de combobox heritent des bonnes couleurs
        self.fenetre.option_add("*TCombobox*Listbox.background", t["input_bg"])
        self.fenetre.option_add("*TCombobox*Listbox.foreground", t["input_fg"])
        self.fenetre.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.fenetre.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def _construire_interface(self):
        """Assemble l'ensemble de la disposition de la fenetre."""
        self.fenetre.configure(bg=self.theme["bg_app"])

        # En-tete
        self._construire_entete()

        # Corps principal en 3 colonnes
        self.corps = tk.Frame(self.fenetre, bg=self.theme["bg_app"])
        self.corps.pack(fill="both", expand=True)

        self.corps.grid_columnconfigure(0, weight=0, minsize=280)
        self.corps.grid_columnconfigure(1, weight=1)
        self.corps.grid_columnconfigure(2, weight=0, minsize=270)
        self.corps.grid_rowconfigure(0, weight=1)

        self._construire_panneau_gauche(self.corps)
        self._construire_panneau_centre(self.corps)
        self._construire_panneau_droit(self.corps)

    def _dessiner_logo_vectoriel(self, parent, size=36) -> tk.Canvas:
        """Dessine le logo vectoriel sur un Canvas Tkinter sans dependances externes."""
        c = tk.Canvas(parent, width=size, height=size, bg=parent.cget("bg"), highlightthickness=0)

        # Fond bouton bleu moderne
        c.create_rectangle(1, 1, size - 1, size - 1, fill="#2563eb", outline="#60a5fa", width=1)

        # Microphone central
        cx = size / 2.0
        cy = size / 2.0 - 2

        # Capsule micro
        cw = size * 0.22
        ch = size * 0.38
        c.create_rectangle(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2, fill="#ffffff", outline="")

        # Arc de capture
        arc_r = size * 0.24
        c.create_arc(cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r, start=0, extent=-180, style="arc", outline="#ffffff", width=2)

        # Pied et socle
        c.create_line(cx, cy + arc_r, cx, cy + arc_r + 4, fill="#ffffff", width=2)
        c.create_line(cx - 5, cy + arc_r + 4, cx + 5, cy + arc_r + 4, fill="#ffffff", width=2)

        return c

    def _construire_entete(self):
        """Barre superieure avec branding et actions globales."""
        self.entete = tk.Frame(self.fenetre, bg=self.theme["bg_header"], height=62)
        self.entete.pack(fill="x")
        self.entete.pack_propagate(False)
        self._remplir_entete()

    def _remplir_entete(self):
        """Remplit l'en-tete avec des composants homogenes au theme actif."""
        for w in self.entete.winfo_children():
            w.destroy()

        self.entete.configure(bg=self.theme["bg_header"])

        # Bloc gauche : Logo vectoriel et titres
        bloc_logo = tk.Frame(self.entete, bg=self.theme["bg_header"])
        bloc_logo.pack(side="left", padx=16, pady=8)

        logo_canvas = self._dessiner_logo_vectoriel(bloc_logo, size=38)
        logo_canvas.pack(side="left", padx=(0, 10))

        titres_frame = tk.Frame(bloc_logo, bg=self.theme["bg_header"])
        titres_frame.pack(side="left")

        self.label_app_nom = tk.Label(
            titres_frame,
            text="VoiceLingo",
            font=("Segoe UI", 15, "bold"),
            fg=self.theme["fg_header_title"],
            bg=self.theme["bg_header"]
        )
        self.label_app_nom.pack(anchor="w")

        self.label_app_desc = tk.Label(
            titres_frame,
            text="Transcription & Traduction Video 100% Locale",
            font=("Segoe UI", 8),
            fg=self.theme["fg_header_sub"],
            bg=self.theme["bg_header"]
        )
        self.label_app_desc.pack(anchor="w")

        # Bloc droit : Boutons (Guide, Parametres, A propos, Theme)
        bloc_actions = tk.Frame(self.entete, bg=self.theme["bg_header"])
        bloc_actions.pack(side="right", padx=16, pady=12)

        self.btn_theme = tk.Button(
            bloc_actions,
            text="Mode Clair" if self.is_dark_mode else "Mode Sombre",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg=self.theme["bg_header_btn"],
            activebackground=self.theme["bg_header_btn_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._changer_theme
        )
        self.btn_theme.pack(side="right", padx=(6, 0))

        self.btn_guide = tk.Button(
            bloc_actions,
            text="Guide d'utilisation",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#2563eb",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._ouvrir_guide_utilisation
        )
        self.btn_guide.pack(side="right", padx=(6, 0))

        self.btn_params = tk.Button(
            bloc_actions,
            text="Parametres IA",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg=self.theme["bg_header_btn"],
            activebackground=self.theme["bg_header_btn_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._ouvrir_parametres
        )
        self.btn_params.pack(side="right", padx=(6, 0))

        self.btn_about = tk.Button(
            bloc_actions,
            text="A propos",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg=self.theme["bg_header_btn"],
            activebackground=self.theme["bg_header_btn_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._ouvrir_a_propos
        )
        self.btn_about.pack(side="right", padx=(0, 0))

    def _construire_panneau_gauche(self, parent):
        """Panneau lateral gauche pour les reglages et formats de sortie."""
        self.panneau_gauche = tk.Frame(
            parent,
            bg=self.theme["bg_panel"],
            highlightbackground=self.theme["border"],
            highlightthickness=1,
            width=280
        )
        self.panneau_gauche.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.panneau_gauche.grid_propagate(False)

        contenu = tk.Frame(self.panneau_gauche, bg=self.theme["bg_panel"])
        contenu.pack(fill="both", expand=True, padx=14, pady=12)

        # Section Langues
        self._titre_section(contenu, "Langues")

        tk.Label(
            contenu,
            text="Langue audio d'origine",
            font=("Segoe UI", 8),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_panel"]
        ).pack(anchor="w", pady=(2, 2))

        labels_src = [lbl for lbl, _ in LANGUES_SOURCE]
        self.liste_src = ttk.Combobox(
            contenu,
            textvariable=self.langue_source_var,
            values=labels_src,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.liste_src.pack(fill="x", pady=(0, 8))

        tk.Label(
            contenu,
            text="Langue de traduction cible",
            font=("Segoe UI", 8),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_panel"]
        ).pack(anchor="w", pady=(2, 2))

        labels_cible = [lbl for lbl, _ in LANGUES_CIBLE]
        self.liste_cible = ttk.Combobox(
            contenu,
            textvariable=self.langue_cible_var,
            values=labels_cible,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.liste_cible.pack(fill="x", pady=(0, 12))
        self.liste_cible.bind("<<ComboboxSelected>>", self._on_langue_cible_change)

        tk.Frame(contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=6)

        # Section Mode de sortie
        self._titre_section(contenu, "Format de sortie")

        self.frame_card_srt = self._creer_carte_radio(
            contenu, "srt", "Sous-titres SRT", "Fichier .srt traduit conforme"
        )
        self.frame_card_dub = self._creer_carte_radio(
            contenu, "dub", "Doublage Vocal", "Video MP4 avec voix synthetisee"
        )

        tk.Frame(contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=8)

        # Section Options de rendu
        self._titre_section(contenu, "Options de rendu")

        self.chk_incrust = tk.Checkbutton(
            contenu,
            text="Incruster sous-titres (Hardsub)",
            variable=self.incruster_var,
            font=("Segoe UI", 9),
            bg=self.theme["bg_panel"],
            fg=self.theme["fg_text"],
            activebackground=self.theme["bg_panel"],
            activeforeground=self.theme["fg_text"],
            selectcolor=self.theme["bg_card"],
            cursor="hand2"
        )
        self.chk_incrust.pack(anchor="w", pady=(2, 8))

        tk.Frame(contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=6)

        # Section Moteur IA actif
        self._titre_section(contenu, "Moteur d'inference actif")

        modele_w = self.config.get("whisper_model_size", "base")
        device_w = self.config.get("whisper_device", "cpu").upper()

        cadre_info_modele = tk.Frame(contenu, bg=self.theme["bg_badge"], padx=10, pady=8)
        cadre_info_modele.pack(fill="x", pady=(4, 4))

        tk.Label(
            cadre_info_modele,
            text=f"Whisper {modele_w} ({device_w})",
            font=("Segoe UI", 9, "bold"),
            fg=self.theme["fg_badge"],
            bg=self.theme["bg_badge"]
        ).pack(anchor="w")

        tk.Label(
            cadre_info_modele,
            text="NLLB-600M - XTTS-v2 / local",
            font=("Segoe UI", 8),
            fg=self.theme["fg_badge"],
            bg=self.theme["bg_badge"]
        ).pack(anchor="w", pady=(2, 0))

    def _titre_section(self, parent, texte):
        """En-tete de section avec contraste optimise."""
        tk.Label(
            parent,
            text=texte.upper(),
            font=("Segoe UI", 8, "bold"),
            fg=self.theme["fg_subtext"],
            bg=parent.cget("bg")
        ).pack(anchor="w", pady=(6, 2))

    def _creer_carte_radio(self, parent, valeur, titre, description):
        """Genere une carte interactive de selection de mode."""
        is_selected = (valeur == self.mode_sortie_var.get())
        fond = self.theme["bg_card_selected"] if is_selected else self.theme["bg_card"]
        bord = self.theme["border_selected"] if is_selected else self.theme["border"]

        cadre = tk.Frame(
            parent,
            bg=fond,
            highlightbackground=bord,
            highlightthickness=1,
            cursor="hand2"
        )
        cadre.pack(fill="x", pady=4)

        ligne = tk.Frame(cadre, bg=fond)
        ligne.pack(fill="x", padx=10, pady=8)

        point = tk.Label(
            ligne,
            text="●" if is_selected else "○",
            font=("Segoe UI", 11),
            fg=self.theme["accent"] if is_selected else self.theme["fg_subtext"],
            bg=fond
        )
        point.pack(side="left", padx=(0, 8))

        textes = tk.Frame(ligne, bg=fond)
        textes.pack(side="left", fill="x", expand=True)

        lbl_titre = tk.Label(
            textes,
            text=titre,
            font=("Segoe UI", 10, "bold"),
            fg=self.theme["fg_title"],
            bg=fond
        )
        lbl_titre.pack(anchor="w")

        lbl_desc = tk.Label(
            textes,
            text=description,
            font=("Segoe UI", 8),
            fg=self.theme["fg_subtext"],
            bg=fond
        )
        lbl_desc.pack(anchor="w")

        def select_fn(v=valeur):
            self.mode_sortie_var.set(v)
            self._rafraichir_cartes_radio()
            self._rafraichir_panneau_droit()

        for w in [cadre, ligne, point, textes, lbl_titre, lbl_desc]:
            w.bind("<Button-1>", lambda e, s=select_fn: s())

        self._cartes_radio[valeur] = {
            "cadre": cadre,
            "ligne": ligne,
            "point": point,
            "textes": textes,
            "titre": lbl_titre,
            "desc": lbl_desc
        }
        return cadre

    def _rafraichir_cartes_radio(self):
        """Met a jour l'aspect des cartes de selection de mode."""
        actuel = self.mode_sortie_var.get()
        for val, items in self._cartes_radio.items():
            sel = (val == actuel)
            fond = self.theme["bg_card_selected"] if sel else self.theme["bg_card"]
            bord = self.theme["border_selected"] if sel else self.theme["border"]

            items["cadre"].configure(bg=fond, highlightbackground=bord)
            items["ligne"].configure(bg=fond)
            items["textes"].configure(bg=fond)
            items["titre"].configure(bg=fond, fg=self.theme["fg_title"])
            items["desc"].configure(bg=fond, fg=self.theme["fg_subtext"])
            items["point"].configure(
                text="●" if sel else "○",
                fg=self.theme["accent"] if sel else self.theme["fg_subtext"],
                bg=fond
            )

    def _construire_panneau_centre(self, parent):
        """Panneau central avec onglets de selection Fichier Local / YouTube."""
        self.frame_centre = tk.Frame(parent, bg=self.theme["bg_app"])
        self.frame_centre.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)

        # Onglets
        self.tabs_frame = tk.Frame(self.frame_centre, bg=self.theme["bg_app"])
        self.tabs_frame.pack(fill="x", pady=(0, 8))

        self.btn_tab_local = tk.Button(
            self.tabs_frame,
            text="Fichier Video Local",
            font=("Segoe UI", 10, "bold" if self.active_tab == "local" else "normal"),
            fg="#ffffff" if self.active_tab == "local" else self.theme["fg_text"],
            bg=self.theme["accent"] if self.active_tab == "local" else self.theme["bg_panel"],
            activebackground=self.theme["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self._changer_onglet("local")
        )
        self.btn_tab_local.pack(side="left", padx=(0, 6))

        self.btn_tab_yt = tk.Button(
            self.tabs_frame,
            text="Lien YouTube / URL",
            font=("Segoe UI", 10, "bold" if self.active_tab == "youtube" else "normal"),
            fg="#ffffff" if self.active_tab == "youtube" else self.theme["fg_text"],
            bg=self.theme["accent"] if self.active_tab == "youtube" else self.theme["bg_panel"],
            activebackground=self.theme["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self._changer_onglet("youtube")
        )
        self.btn_tab_yt.pack(side="left")

        # Vue centrale
        self.zone_vue = tk.Frame(self.frame_centre, bg=self.theme["bg_app"])
        self.zone_vue.pack(fill="both", expand=True)

        self._afficher_vue_courante()

    def _changer_onglet(self, mode):
        """Bascule entre local et YouTube."""
        if self.is_processing:
            return
        self.active_tab = mode
        self.btn_tab_local.configure(
            font=("Segoe UI", 10, "bold" if self.active_tab == "local" else "normal"),
            fg="#ffffff" if self.active_tab == "local" else self.theme["fg_text"],
            bg=self.theme["accent"] if self.active_tab == "local" else self.theme["bg_panel"]
        )
        self.btn_tab_yt.configure(
            font=("Segoe UI", 10, "bold" if self.active_tab == "youtube" else "normal"),
            fg="#ffffff" if self.active_tab == "youtube" else self.theme["fg_text"],
            bg=self.theme["accent"] if self.active_tab == "youtube" else self.theme["bg_panel"]
        )
        self._afficher_vue_courante()

    def _afficher_vue_courante(self):
        """Affiche la vue correspondant au fichier charge ou au selecteur."""
        for w in self.zone_vue.winfo_children():
            w.destroy()

        if self.chemin_video:
            from video_handler import get_video_info
            try:
                infos = get_video_info(self.chemin_video)
                self._afficher_carte_traitement(infos)
                return
            except Exception:
                self.chemin_video = None

        if self.active_tab == "local":
            self._afficher_zone_import_local()
        else:
            self._afficher_zone_import_youtube()

    def _afficher_zone_import_local(self):
        """Zone ergonomique de glisser-deposer ou clic pour fichier local."""
        carte = tk.Frame(
            self.zone_vue,
            bg=self.theme["bg_card"],
            highlightbackground=self.theme["border"],
            highlightthickness=2,
            cursor="hand2"
        )
        carte.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        contenu = tk.Frame(carte, bg=self.theme["bg_card"])
        contenu.place(relx=0.5, rely=0.5, anchor="center")

        c_ico = tk.Canvas(contenu, width=64, height=64, bg=self.theme["bg_badge"], highlightthickness=0)
        c_ico.pack(pady=(0, 14))
        c_ico.create_text(32, 32, text="⬆", font=("Segoe UI", 28, "bold"), fill=self.theme["accent"])

        tk.Label(
            contenu,
            text="Importer une video a traiter",
            font=("Segoe UI", 15, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_card"]
        ).pack()

        tk.Label(
            contenu,
            text="Cliquez ici pour selectionner votre enregistrement ou cours",
            font=("Segoe UI", 10),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"]
        ).pack(pady=(4, 6))

        tk.Label(
            contenu,
            text="Formats pris en charge : MP4 - MKV - AVI - MOV - WEBM",
            font=("Segoe UI", 8),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"]
        ).pack(pady=(0, 18))

        btn = tk.Button(
            contenu,
            text="Parcourir mes fichiers",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"],
            activebackground=self.theme["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=18,
            pady=9,
            cursor="hand2",
            command=self._choisir_fichier
        )
        btn.pack()

        def on_enter(e):
            carte.configure(highlightbackground=self.theme["accent"])

        def on_leave(e):
            carte.configure(highlightbackground=self.theme["border"])

        carte.bind("<Enter>", on_enter)
        carte.bind("<Leave>", on_leave)
        carte.bind("<Button-1>", lambda e: self._choisir_fichier())
        contenu.bind("<Button-1>", lambda e: self._choisir_fichier())

    def _afficher_zone_import_youtube(self):
        """Zone de saisie d'URL YouTube avec telechargement direct."""
        carte = tk.Frame(
            self.zone_vue,
            bg=self.theme["bg_card"],
            highlightbackground=self.theme["border"],
            highlightthickness=1
        )
        carte.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        contenu = tk.Frame(carte, bg=self.theme["bg_card"])
        contenu.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86)

        tk.Label(
            contenu,
            text="Telecharger une video depuis YouTube",
            font=("Segoe UI", 14, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_card"]
        ).pack(pady=(0, 6))

        tk.Label(
            contenu,
            text="Collez le lien complet de la video ou du tutoriel",
            font=("Segoe UI", 9),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"]
        ).pack(pady=(0, 16))

        self.entry_yt = ttk.Entry(contenu, textvariable=self.youtube_url_var, font=("Segoe UI", 10))
        self.entry_yt.pack(fill="x", ipady=4, pady=(0, 14))

        self.btn_yt_dl = tk.Button(
            contenu,
            text="Recuperer et Charger la Video",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"],
            activebackground=self.theme["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=9,
            cursor="hand2",
            command=self._telecharger_youtube
        )
        self.btn_yt_dl.pack()

        self.lbl_yt_status = tk.Label(
            contenu,
            text="",
            font=("Segoe UI", 9, "italic"),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"]
        )
        self.lbl_yt_status.pack(pady=(12, 0))

    def _telecharger_youtube(self):
        """Telecharge la video YouTube saisie via yt-dlp dans un thread daemon."""
        url = self.youtube_url_var.get().strip()
        if not url:
            messagebox.showwarning("URL requise", "Veuillez coller une URL YouTube valide.", parent=self.fenetre)
            return

        if not is_youtube_url(url):
            messagebox.showerror("URL invalide", "Le format de l'URL n'est pas reconnu comme un lien YouTube.", parent=self.fenetre)
            return

        self.btn_yt_dl.configure(state="disabled", text="Analyse et telechargement en cours...")
        self.lbl_yt_status.configure(text="Recuperation des metadonnees...")

        def run_dl():
            try:
                infos = get_video_info_youtube(url)
                titre = infos.get("title", "video_youtube")
                dossier_telechargement = self.config.get("output_dir") or os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(dossier_telechargement, exist_ok=True)

                self.fenetre.after(0, lambda: self.lbl_yt_status.configure(text=f"Telechargement de : {titre[:45]}..."))

                chemin_telecharge = download_video(
                    url,
                    dossier_sortie=dossier_telechargement,
                    qualite="720p",
                    progress_cb=lambda p, m: self.fenetre.after(0, lambda: self.lbl_yt_status.configure(text=f"{m} ({p}%)"))
                )

                def on_done():
                    self.btn_yt_dl.configure(state="normal", text="Recuperer et Charger la Video")
                    self.lbl_yt_status.configure(text="")
                    self.chemin_video = chemin_telecharge
                    self._afficher_vue_courante()

                self.fenetre.after(0, on_done)

            except Exception as e:
                def on_err():
                    self.btn_yt_dl.configure(state="normal", text="Recuperer et Charger la Video")
                    self.lbl_yt_status.configure(text=f"Erreur : {e}")
                    messagebox.showerror("Erreur YouTube", f"Impossible de telecharger la video :\n{e}", parent=self.fenetre)

                self.fenetre.after(0, on_err)

        threading.Thread(target=run_dl, daemon=True).start()

    def _afficher_carte_traitement(self, infos):
        """Affiche la carte d'etat de la video chargee et la progression."""
        wrap = tk.Frame(
            self.zone_vue,
            bg=self.theme["bg_card"],
            highlightbackground=self.theme["border"],
            highlightthickness=1
        )
        wrap.pack(fill="both", expand=True, padx=4, pady=4)

        ligne_fichier = tk.Frame(wrap, bg=self.theme["bg_card"])
        ligne_fichier.pack(fill="x", padx=16, pady=14)

        ico_lbl = tk.Label(
            ligne_fichier,
            text="▶",
            font=("Segoe UI", 16, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg_badge"],
            width=3,
            height=2
        )
        ico_lbl.pack(side="left", padx=(0, 12))

        infos_f = tk.Frame(ligne_fichier, bg=self.theme["bg_card"])
        infos_f.pack(side="left", fill="x", expand=True)

        nom = infos.get("name", "Video")
        if len(nom) > 40:
            nom = nom[:37] + "..."

        tk.Label(
            infos_f,
            text=nom,
            font=("Segoe UI", 12, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_card"]
        ).pack(anchor="w")

        tk.Label(
            infos_f,
            text=f"{infos.get('format', 'Video')} - {infos.get('size_mb', 0)} Mo - Duree : {infos.get('duration_str', 'N/A')}",
            font=("Segoe UI", 9),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"]
        ).pack(anchor="w", pady=(2, 0))

        tk.Button(
            ligne_fichier,
            text="✕ Retirer",
            font=("Segoe UI", 9),
            fg=self.theme["danger"],
            bg=self.theme["bg_card"],
            relief="flat",
            padx=8,
            cursor="hand2",
            command=self._supprimer_fichier
        ).pack(side="right")

        tk.Frame(wrap, bg=self.theme["border"], height=1).pack(fill="x")

        self.frame_progress = tk.Frame(wrap, bg=self.theme["bg_card"])
        self.frame_progress.pack(fill="x", padx=16, pady=(12, 6))

        entete_p = tk.Frame(self.frame_progress, bg=self.theme["bg_card"])
        entete_p.pack(fill="x")

        self.label_etape = tk.Label(
            entete_p,
            text="Pret a demarrer",
            font=("Segoe UI", 10, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_card"]
        )
        self.label_etape.pack(side="left")

        self.label_pourcent = tk.Label(
            entete_p,
            text="0%",
            font=("Segoe UI", 10, "bold"),
            fg=self.theme["accent"],
            bg=self.theme["bg_card"]
        )
        self.label_pourcent.pack(side="right")

        self.barre_progress = tk.Canvas(
            self.frame_progress,
            height=10,
            bg=self.theme["progress_bg"],
            highlightthickness=0
        )
        self.barre_progress.pack(fill="x", pady=(6, 4))

        self.label_tranche = tk.Label(
            self.frame_progress,
            text="",
            font=("Segoe UI", 8, "italic"),
            fg=self.theme["warning"],
            bg=self.theme["bg_card"]
        )
        self.label_tranche.pack(anchor="w")

        frame_etapes = tk.Frame(self.frame_progress, bg=self.theme["bg_card"])
        frame_etapes.pack(fill="x", pady=(8, 12))

        self.widgets_etapes = {}
        for nom_e, deb, fin in ETAPES_PIPELINE:
            l = tk.Frame(frame_etapes, bg=self.theme["bg_card"])
            l.pack(fill="x", pady=2)

            pt = tk.Label(
                l,
                text="○",
                font=("Segoe UI", 10),
                fg=self.theme["fg_subtext"],
                bg=self.theme["bg_card"],
                width=2
            )
            pt.pack(side="left")

            lb = tk.Label(
                l,
                text=nom_e,
                font=("Segoe UI", 9),
                fg=self.theme["fg_subtext"],
                bg=self.theme["bg_card"]
            )
            lb.pack(side="left", padx=(4, 0))

            self.widgets_etapes[nom_e] = {"ligne": l, "point": pt, "label": lb}

        tk.Frame(wrap, bg=self.theme["border"], height=1).pack(fill="x")

        zone_btn = tk.Frame(wrap, bg=self.theme["bg_card"])
        zone_btn.pack(fill="x", padx=16, pady=14)

        self.bouton_demarrer = tk.Button(
            zone_btn,
            text="Lancer la Transcription et Traduction",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"],
            activebackground=self.theme["accent_hover"],
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=10,
            cursor="hand2",
            command=self._demarrer_traitement
        )
        self.bouton_demarrer.pack(fill="x")

        self.bouton_annuler = tk.Button(
            zone_btn,
            text="Interrompre le Traitement",
            font=("Segoe UI", 9),
            fg=self.theme["danger"],
            bg=self.theme["bg_card"],
            activebackground=self.theme["bg_card_hover"],
            activeforeground=self.theme["danger"],
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._annuler_traitement
        )

    def _construire_panneau_droit(self, parent):
        """Panneau droit d'analyse, domaine et synthese."""
        self.panneau_droit = tk.Frame(
            parent,
            bg=self.theme["bg_panel"],
            highlightbackground=self.theme["border"],
            highlightthickness=1,
            width=270
        )
        self.panneau_droit.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        self.panneau_droit.grid_propagate(False)

        self.frame_droit_contenu = tk.Frame(self.panneau_droit, bg=self.theme["bg_panel"])
        self.frame_droit_contenu.pack(fill="both", expand=True, padx=14, pady=12)

        self._rafraichir_panneau_droit()

    def _rafraichir_panneau_droit(self):
        """Actualise les informations contextuelles du panneau droit."""
        for w in self.frame_droit_contenu.winfo_children():
            w.destroy()

        mode = self.mode_sortie_var.get()
        code_cible = CODES_LANGUES.get(self.langue_cible_var.get(), "fr")

        # Fichier de sortie
        self._titre_section(self.frame_droit_contenu, "Apercu Fichier Produit")

        self._afficher_carte_sortie_info(
            actif=(mode == "srt"),
            badge="SRT",
            nom=f"video_{code_cible}.srt",
            description="Sous-titres SubRip UTF-8 BOM"
        )
        self._afficher_carte_sortie_info(
            actif=(mode == "dub"),
            badge="MP4",
            nom=f"video_{code_cible}_double.mp4",
            description="Flux video H.264 + Voix IA"
        )

        tk.Frame(self.frame_droit_contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=8)

        # Specifications
        self._titre_section(self.frame_droit_contenu, "Parametres Techniques")
        self._ligne_cle_valeur("Langue finale", code_cible.upper())
        self._ligne_cle_valeur("Max par ligne", "42 car (Netflix)")
        self._ligne_cle_valeur("Encodage", "UTF-8 avec BOM")

        tk.Frame(self.frame_droit_contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=8)

        # Domaine
        self._titre_section(self.frame_droit_contenu, "Domaine Contextuel")

        self.label_domaine = tk.Label(
            self.frame_droit_contenu,
            text="En attente d'analyse...",
            font=("Segoe UI", 9, "italic"),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_card"],
            padx=8,
            pady=6,
            wraplength=220,
            justify="left"
        )
        self.label_domaine.pack(fill="x", pady=(2, 6))

        tk.Frame(self.frame_droit_contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=8)

        # Auteur
        self._titre_section(self.frame_droit_contenu, "Concepteur & Annee")
        self._ligne_cle_valeur("Auteur", "M. Lamine Niang")
        self._ligne_cle_valeur("Annee", "2026")
        self._ligne_cle_valeur("Licence", "Libre et Offline")

    def _afficher_carte_sortie_info(self, actif, badge, nom, description):
        """Affiche une vignette du format de fichier produit."""
        fond = self.theme["bg_card_selected"] if actif else self.theme["bg_card"]
        bord = self.theme["border_selected"] if actif else self.theme["border"]

        f = tk.Frame(
            self.frame_droit_contenu,
            bg=fond,
            highlightbackground=bord,
            highlightthickness=1
        )
        f.pack(fill="x", pady=3)

        ligne = tk.Frame(f, bg=fond)
        ligne.pack(fill="x", padx=8, pady=6)

        b_lbl = tk.Label(
            ligne,
            text=badge,
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"] if actif else self.theme["fg_subtext"],
            padx=6,
            pady=2
        )
        b_lbl.pack(side="left", padx=(0, 8))

        infos = tk.Frame(ligne, bg=fond)
        infos.pack(side="left", fill="x", expand=True)

        tk.Label(
            infos,
            text=nom,
            font=("Segoe UI", 9, "bold"),
            fg=self.theme["fg_title"] if actif else self.theme["fg_subtext"],
            bg=fond
        ).pack(anchor="w")

        tk.Label(
            infos,
            text=description,
            font=("Segoe UI", 7),
            fg=self.theme["fg_subtext"],
            bg=fond
        ).pack(anchor="w")

    def _ligne_cle_valeur(self, cle, valeur):
        """Ligne d'information cle-valeur compacte."""
        f = tk.Frame(self.frame_droit_contenu, bg=self.theme["bg_panel"])
        f.pack(fill="x", pady=2)
        tk.Label(f, text=cle, font=("Segoe UI", 8), fg=self.theme["fg_subtext"], bg=self.theme["bg_panel"]).pack(side="left")
        tk.Label(f, text=valeur, font=("Segoe UI", 8, "bold"), fg=self.theme["fg_title"], bg=self.theme["bg_panel"]).pack(side="right")

    def _choisir_fichier(self):
        """Ouvre le dialogue de selection de fichier video."""
        chemin = filedialog.askopenfilename(
            parent=self.fenetre,
            title="Selectionner un fichier video a traduire",
            filetypes=[
                ("Fichiers video", "*.mp4 *.avi *.mov *.mkv *.webm *.MP4 *.MKV"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if chemin:
            self._charger_fichier_video(chemin)

    def _charger_fichier_video(self, chemin):
        """Verifie et charge la video."""
        try:
            taille = os.path.getsize(chemin)
        except OSError as e:
            messagebox.showerror("Erreur fichier", f"Impossible d'acceder au fichier :\n{e}", parent=self.fenetre)
            return

        if taille > 4 * 1024 * 1024 * 1024:
            messagebox.showwarning("Fichier volumineux", "Le fichier depasse 4 Go. Le traitement pourrait prendre du temps.", parent=self.fenetre)

        self.chemin_video = chemin
        self._afficher_vue_courante()

    def _supprimer_fichier(self):
        """Retire le fichier charge."""
        if self.is_processing:
            return
        self.chemin_video = None
        self._afficher_vue_courante()

    def _demarrer_traitement(self):
        """Demarre le pipeline de transcription et traduction."""
        if not self.chemin_video:
            messagebox.showwarning("Selection requise", "Veuillez selectionner une video.", parent=self.fenetre)
            return

        dossier_sortie = self.config.get("output_dir")
        if not dossier_sortie or not os.path.exists(dossier_sortie):
            dossier_sortie = filedialog.askdirectory(
                parent=self.fenetre,
                title="Choisir le dossier d'enregistrement des fichiers traduits"
            )
            if not dossier_sortie:
                return

        code_src = CODES_LANGUES.get(self.langue_source_var.get(), "auto")
        code_cible = CODES_LANGUES.get(self.langue_cible_var.get(), "fr")
        mode = self.mode_sortie_var.get()
        burn_subs = self.incruster_var.get()

        self.is_processing = True
        if self.bouton_demarrer:
            self.bouton_demarrer.configure(state="disabled", text="Traitement en cours...")
        if self.bouton_annuler:
            self.bouton_annuler.pack(fill="x", pady=(6, 0))

        self.pipeline = ProcessingPipeline(self.config)
        self.pipeline.run(
            video_path=self.chemin_video,
            src_lang=code_src,
            tgt_lang=code_cible,
            output_mode=mode,
            output_dir=dossier_sortie,
            burn_subs=burn_subs,
            progress_cb=self._on_progression,
            done_cb=self._on_termine
        )

    def _annuler_traitement(self):
        """Interrompt le traitement en cours."""
        if self.pipeline:
            self.pipeline.cancel()
        self.is_processing = False
        if self.bouton_demarrer:
            self.bouton_demarrer.configure(state="normal", text="Lancer la Transcription et Traduction")
        if self.bouton_annuler:
            self.bouton_annuler.pack_forget()

    def _on_progression(self, pourcent: int, message: str):
        """Notification de progression recue depuis le thread d'arriere-plan."""
        self.fenetre.after(0, lambda: self._mettre_a_jour_progress_ui(pourcent, message))

    def _mettre_a_jour_progress_ui(self, pourcent: int, message: str):
        """Met a jour les indicateurs visuels d'avancement."""
        if not self.is_processing:
            return

        msg_principal = message
        detail_tranche = ""
        if " - " in message and "tranche" in message.lower():
            pts = message.split(" - ", 1)
            msg_principal = pts[0]
            detail_tranche = pts[1]

        if self.label_etape:
            self.label_etape.configure(text=msg_principal)
        if self.label_pourcent:
            self.label_pourcent.configure(text=f"{pourcent}%")
        if self.label_tranche:
            self.label_tranche.configure(text=detail_tranche)

        if self.barre_progress:
            self.barre_progress.update_idletasks()
            w = self.barre_progress.winfo_width()
            if w > 1:
                self.barre_progress.delete("all")
                self.barre_progress.create_rectangle(0, 0, w, 10, fill=self.theme["progress_bg"], outline="")
                filled_w = int(w * (pourcent / 100.0))
                if filled_w > 0:
                    self.barre_progress.create_rectangle(0, 0, filled_w, 10, fill=self.theme["progress_fill"], outline="")

        for nom_e, deb, fin in ETAPES_PIPELINE:
            w_dict = self.widgets_etapes.get(nom_e)
            if not w_dict:
                continue
            if pourcent >= fin:
                w_dict["point"].configure(text="✓", fg=self.theme["success"])
                w_dict["label"].configure(fg=self.theme["success"], font=("Segoe UI", 9, "bold"))
            elif pourcent >= deb:
                w_dict["point"].configure(text="◉", fg=self.theme["accent"])
                w_dict["label"].configure(fg=self.theme["accent"], font=("Segoe UI", 9, "bold"))
            else:
                w_dict["point"].configure(text="○", fg=self.theme["fg_subtext"])
                w_dict["label"].configure(fg=self.theme["fg_subtext"], font=("Segoe UI", 9, "normal"))

        if "domaine" in message.lower() and self.label_domaine:
            domaines = ["informatique", "mathematiques", "physique", "medecine", "biologie", "economie"]
            for d in domaines:
                if d in message.lower():
                    noms = {
                        "informatique": "Informatique & Programmation",
                        "mathematiques": "Mathematiques & Calcul",
                        "physique": "Sciences Physiques",
                        "medecine": "Sciences Medicales",
                        "biologie": "Sciences Biologiques",
                        "economie": "Economie & Finance",
                    }
                    self.label_domaine.configure(
                        text=noms.get(d, d.capitalize()),
                        font=("Segoe UI", 9, "bold"),
                        fg=self.theme["accent"]
                    )
                    break

    def _on_termine(self, succes: bool, resultat: str):
        """Callback de cloture de traitement."""
        self.fenetre.after(0, lambda: self._afficher_resultat(succes, resultat))

    def _afficher_resultat(self, succes: bool, resultat: str):
        """Affiche le resultat de l'operation."""
        self.is_processing = False
        if self.bouton_annuler:
            self.bouton_annuler.pack_forget()

        if self.bouton_demarrer:
            self.bouton_demarrer.configure(
                state="normal",
                text="Traitement Termine - Relancer ?",
                bg=self.theme["success"] if succes else self.theme["accent"]
            )

        if succes:
            messagebox.showinfo(
                "Traduction Reussie !",
                f"Le traitement s'est acheve avec succes !\n\nFichier genere :\n{resultat}",
                parent=self.fenetre
            )
        else:
            messagebox.showerror(
                "Erreur de Traitement",
                f"Une anomalie s'est produite durant le traitement :\n\n{resultat}",
                parent=self.fenetre
            )

    def _on_langue_cible_change(self, event=None):
        """Actualise les apercus lors du changement de langue cible."""
        self._rafraichir_panneau_droit()

    def _changer_theme(self):
        """Bascule entre mode sombre et clair et reconstruit l'arborescence visuelle."""
        self.is_dark_mode = not self.is_dark_mode
        self.theme = THEMES["dark"] if self.is_dark_mode else THEMES["light"]

        # Mise a jour des styles ttk
        self._appliquer_style_ttk()

        # Fenetre et conteneur racine
        self.fenetre.configure(bg=self.theme["bg_app"])

        # En-tete integralement reconstruit avec le nouveau theme
        self._remplir_entete()

        # Reconstruire les 3 panneaux de maniere propre et complete
        for w in self.corps.winfo_children():
            w.destroy()

        self.corps.configure(bg=self.theme["bg_app"])
        self._construire_panneau_gauche(self.corps)
        self._construire_panneau_centre(self.corps)
        self._construire_panneau_droit(self.corps)

    def _ouvrir_guide_utilisation(self):
        """Affiche la fenetre modale complete du Guide d'Utilisation avec explication de chaque option."""
        g = tk.Toplevel(self.fenetre)
        g.title("Guide d'Utilisation Complet - VoiceLingo")
        g.geometry("900x700")
        g.minsize(820, 580)
        g.configure(bg=self.theme["bg_app"])
        g.transient(self.fenetre)
        g.grab_set()

        # En-tete du guide
        hdr = tk.Frame(g, bg=self.theme["bg_header"], height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        logo_c = self._dessiner_logo_vectoriel(hdr, size=40)
        logo_c.pack(side="left", padx=(16, 10), pady=14)

        t_frame = tk.Frame(hdr, bg=self.theme["bg_header"])
        t_frame.pack(side="left", pady=12)

        tk.Label(
            t_frame,
            text="Guide d'Utilisation & Documentation des Options",
            font=("Segoe UI", 13, "bold"),
            fg="#ffffff",
            bg=self.theme["bg_header"]
        ).pack(anchor="w")

        tk.Label(
            t_frame,
            text="Explication pas a pas, comparatif des modeles, avantages et inconvenients",
            font=("Segoe UI", 8),
            fg="#bfdbfe",
            bg=self.theme["bg_header"]
        ).pack(anchor="w")

        tk.Button(
            hdr,
            text="Fermer le guide",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#2563eb",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=g.destroy
        ).pack(side="right", padx=16, pady=16)

        # Zone scrollable pour le guide
        canvas = tk.Canvas(g, bg=self.theme["bg_app"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(g, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=self.theme["bg_app"])

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_content, anchor="nw")

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Support molette
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        g.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), g.destroy()))

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Contenu detaille du guide organise en cartes
        def creer_carte_guide(titre, badge=""):
            c = tk.Frame(
                scroll_content,
                bg=self.theme["bg_card"],
                highlightbackground=self.theme["border"],
                highlightthickness=1,
                padx=16,
                pady=14
            )
            c.pack(fill="x", pady=8, padx=6)

            h = tk.Frame(c, bg=self.theme["bg_card"])
            h.pack(fill="x", pady=(0, 6))

            if badge:
                tk.Label(
                    h,
                    text=badge,
                    font=("Segoe UI", 8, "bold"),
                    fg="#ffffff",
                    bg=self.theme["accent"],
                    padx=6,
                    pady=2
                ).pack(side="left", padx=(0, 8))

            tk.Label(
                h,
                text=titre,
                font=("Segoe UI", 11, "bold"),
                fg=self.theme["fg_title"],
                bg=self.theme["bg_card"]
            ).pack(side="left", anchor="w")

            tk.Frame(c, bg=self.theme["border"], height=1).pack(fill="x", pady=6)
            return c

        def ajouter_bloc_option(parent, nom_option, description, avantages, inconvenients, reco=""):
            cadre = tk.Frame(
                parent,
                bg=self.theme["bg_card"],
                highlightbackground=self.theme["border"],
                highlightthickness=1,
                padx=12,
                pady=10
            )
            cadre.pack(fill="x", pady=6)

            tk.Label(
                cadre,
                text=nom_option,
                font=("Segoe UI", 10, "bold"),
                fg=self.theme["fg_title"],
                bg=self.theme["bg_card"]
            ).pack(anchor="w")

            tk.Label(
                cadre,
                text=description,
                font=("Segoe UI", 9),
                fg=self.theme["fg_text"],
                bg=self.theme["bg_card"],
                wraplength=780,
                justify="left"
            ).pack(anchor="w", pady=(2, 6))

            # Ligne avantages et inconvenients
            grid_f = tk.Frame(cadre, bg=self.theme["bg_card"])
            grid_f.pack(fill="x", pady=(2, 4))

            # Avantages (vert)
            av_f = tk.Frame(grid_f, bg=self.theme["success_bg"], padx=8, pady=6)
            av_f.pack(fill="x", pady=2)
            tk.Label(
                av_f,
                text=f"+ Avantages : {avantages}",
                font=("Segoe UI", 8),
                fg=self.theme["success"],
                bg=self.theme["success_bg"],
                wraplength=760,
                justify="left"
            ).pack(anchor="w")

            # Inconvenients (orange/rouge)
            if inconvenients:
                inc_f = tk.Frame(grid_f, bg=self.theme["warning_bg"], padx=8, pady=6)
                inc_f.pack(fill="x", pady=2)
                tk.Label(
                    inc_f,
                    text=f"- Inconvenients : {inconvenients}",
                    font=("Segoe UI", 8),
                    fg=self.theme["warning"],
                    bg=self.theme["warning_bg"],
                    wraplength=760,
                    justify="left"
                ).pack(anchor="w")

            if reco:
                tk.Label(
                    cadre,
                    text=f"* Conseil d'utilisation : {reco}",
                    font=("Segoe UI", 8, "italic"),
                    fg=self.theme["accent"],
                    bg=self.theme["bg_card"],
                    wraplength=780,
                    justify="left"
                ).pack(anchor="w", pady=(4, 0))

        # 1. Prise en main rapide
        c1 = creer_carte_guide("1. Flux de Travail Rapide (4 Etapes)", "GUIDE")
        tk.Label(
            c1,
            text=(
                "VoiceLingo a ete concu pour rendre la transcription et la traduction de tutoriels video "
                "aussi simple que possible. Voici le deroulement recommande :\n\n"
                "1. Choisissez votre source : Onglet 'Fichier Video Local' pour vos fichiers sur disque, "
                "ou onglet 'Lien YouTube' pour coller l'URL d'un cours en ligne.\n"
                "2. Reglez les langues : Laissez 'Auto-detecter' si la langue de la video est incertaine, "
                "et choisissez 'Francais' comme langue cible.\n"
                "3. Choisissez votre type de sortie : 'Sous-titres SRT' (recommande pour les cours de code) "
                "ou 'Doublage Vocal' pour generer une voix synthetisee.\n"
                "4. Cliquez sur 'Lancer la Transcription et Traduction' : le traitement tourne 100% en local "
                "et le fichier resultat est automatiquement sauvegarde."
            ),
            font=("Segoe UI", 9),
            fg=self.theme["fg_text"],
            bg=self.theme["bg_card"],
            wraplength=800,
            justify="left"
        ).pack(anchor="w")

        # 2. Options de Format de Sortie
        c2 = creer_carte_guide("2. Formats de Sortie : Sous-titres SRT vs Doublage Vocal", "SORTIE")
        ajouter_bloc_option(
            c2,
            nom_option="Sous-titres SRT (.srt horodate conforme)",
            description="Genere un fichier standard de sous-titres avec decoupage optimal de 42 caracteres par ligne et encodage UTF-8 BOM lisible par VLC, MPV et YouTube.",
            avantages="Traitement tres rapide, fichier leger (< 100 Ko), precision textuelle maximale, preserve la voix du formateur original.",
            inconvenients="Nécessite de lire a l'ecran pendant le visionnage.",
            reco="Recommande pour tous les cours d'informatique, tutoriels de programmation et sciences."
        )
        ajouter_bloc_option(
            c2,
            nom_option="Doublage Vocal (Video MP4 avec voix IA synthetisee)",
            description="Remplace la piste audio originale par une piste traduite synthetisee avec XTTS-v2 / pyttsx3 / edge-tts, puis assemble la nouvelle video en MP4.",
            avantages="Confort d'ecoute total sans avoir a lire les sous-titres, ideal pour suivre un long tutoriel tout en codant sur un autre ecran.",
            inconvenients="Temps de calcul plus important pour la synthese vocale, debit audio variable selon la longueur des phrases.",
            reco="Recommande pour les presentations conceptuelles, conferences ou cours magistraux."
        )

        # 3. Incrustation Hardsub
        c3 = creer_carte_guide("3. Option d'Incrustation Hardsub (Dans la video)", "VIDEO")
        ajouter_bloc_option(
            c3,
            nom_option="Incruster les sous-titres dans la video (Hardsub)",
            description="Grave definitivement les sous-titres traduits directement dans le flux d'images de la video MP4 via le filtre video FFmpeg.",
            avantages="Permet de lire la video avec ses sous-titres sur n'importe quel televiseur, tablette, smartphone ou lecteur sans fichier .srt additionnel.",
            inconvenients="Les sous-titres ne peuvent plus etre desactives, et l'encodage complet de la video necessite quelques minutes supplementaires.",
            reco="A cocher si vous exportez la video pour la visionner sur un appareil ne supportant pas les fichiers .srt externes."
        )

        # 4. Modeles Whisper
        c4 = creer_carte_guide("4. Modeles de Transcription Whisper (faster-whisper)", "IA SPEECH")
        ajouter_bloc_option(
            c4,
            nom_option="Whisper Base (Taille : ~140 Mo - Defaut)",
            description="Modele de transcription compact et ultra rapide. Fonctionne sur n'importe quel ordinateur portable standard.",
            avantages="Tres faible consommation de RAM (~500 Mo), execution instantanee meme sur processeur CPU ancien.",
            inconvenients="Peut faire de legeres approximations sur des mots en anglais prononces avec un accent tres fort.",
            reco="Choix ideal par defaut pour un traitement rapide sans surcharger la machine."
        )
        ajouter_bloc_option(
            c4,
            nom_option="Whisper Small / Medium (Taille : ~460 Mo a 1.5 Go)",
            description="Compromis equilibre offrant une reconnaissance plus fine des accents et du vocabulaire technique.",
            avantages="Precision accrue sur les acronymes informatiques et les bruits de fond legers.",
            inconvenients="Demande entre 1.5 Go et 3 Go de RAM.",
            reco="A selectionner si vous disposez d'un processeur multi-coeurs recent ou de 8 Go+ de RAM."
        )
        ajouter_bloc_option(
            c4,
            nom_option="Whisper Large-v3 (Taille : ~3 Go - Qualite Maximale)",
            description="Le modele le plus puissant de Whisper. Qualite de transcription identique a celle de YouTube professionnel.",
            avantages="Precision quasi parfaite, horodatage au mot pres (VAD) et excellente tenue sur le jargon avance.",
            inconvenients="Plus lourd a charger et temps de transcription plus long sur processeur CPU seul.",
            reco="Hautement recommande si vous disposez d'une carte graphique NVIDIA avec support CUDA."
        )

        # 5. Acceleration Materielle
        c5 = creer_carte_guide("5. Processeur CPU vs Carte Graphique GPU CUDA", "HARDWARE")
        ajouter_bloc_option(
            c5,
            nom_option="Mode CPU (Processeur classique)",
            description="Execute l'ensemble des reseaux de neurones directement sur les coeurs du processeur central.",
            avantages="Universel : fonctionne sur 100% des machines Windows, Linux et macOS sans aucun pilote additionnel.",
            inconvenients="Vitesse de transcription moderee par rapport a une carte graphique dediee.",
            reco="Active par defaut pour garantir une compatibilite universelle."
        )
        ajouter_bloc_option(
            c5,
            nom_option="Mode CUDA (Acceleration Carte Graphique NVIDIA)",
            description="Exploite la puissance de calcul massif des puces graphiques NVIDIA Tensor Cores.",
            avantages="Vitesse de traitement multipliee par 5 a 10 fois. Un cours de 1 heure est transcrit en 2 a 3 minutes.",
            inconvenients="Necessite une carte graphique NVIDIA et l'installation des pilotes CUDA.",
            reco="A activer dans 'Parametres IA' si votre ordinateur est equipe d'une carte NVIDIA GTX/RTX."
        )

        # 6. Modeles NLLB et Protection du Contexte
        c6 = creer_carte_guide("6. Traduction Contextuelle NLLB & Glossaire Technique", "TRADUCTION")
        ajouter_bloc_option(
            c6,
            nom_option="Protection intelligente des termes de programmation",
            description="VoiceLingo analyse le domaine de la video et applique un mecanisme de protection par jetons specifiques. Les termes comme 'function', 'class', 'API', 'Docker', 'gradient', 'loop' ne sont jamais traduits de facon absurde.",
            avantages="Garantit que le code explique dans le tutoriel reste fidele a ce que vous devez taper dans votre editeur.",
            inconvenients="Aucun, le glossaire s'adapte automatiquement selon la thematique detectee.",
            reco="Laissez la detection de domaine active pour beneficier de ce traitement intelligent."
        )
        ajouter_bloc_option(
            c6,
            nom_option="NLLB-200-600M (Hugging Face - 200 Langues)",
            description="Modele de traduction neuronale multilingue optimise pour l'execution locale.",
            avantages="Tres rapide, comprehension grammaticale avancee, ne requiert aucune connexion internet apres le premier chargement.",
            inconvenients="Poids initial du modele (~2.4 Go) telecharge une seule fois dans le cache local.",
            reco="Le modele 600M offre le meilleur ratio vitesse / fidelite linguistique."
        )

        # 7. Astuces tutoriels
        c7 = creer_carte_guide("7. Astuces & Recommandations pour les Tutoriels de Code", "ASTUCES")
        tk.Label(
            c7,
            text=(
                "- Pour un tutoriel YouTube : Copiez directement le lien de la video (ou d'un Short) "
                "dans l'onglet YouTube. VoiceLingo telecharge la video au format optimal et l'ouvre automatiquement.\n\n"
                "- Si la voix du formateur est etouffee : Activez le format 'Sous-titres SRT' et Whisper 'base' ou 'medium'. "
                "L'algorithme de detection de voix (VAD) supprimera automatiquement les blancs et les silences.\n\n"
                "- Visionnage dans VLC : Une fois le fichier .srt produit a cote de votre video, ouvrez la video "
                "dans VLC Media Player. Le sous-titre est detecte et affiche immediatement sans aucune configuration."
            ),
            font=("Segoe UI", 9),
            fg=self.theme["fg_text"],
            bg=self.theme["bg_card"],
            wraplength=800,
            justify="left"
        ).pack(anchor="w")

    def _ouvrir_a_propos(self):
        """Ouvre le dialogue A propos avec auteur, contexte et contact."""
        w = tk.Toplevel(self.fenetre)
        w.title("A propos de VoiceLingo")
        w.geometry("540x480")
        w.resizable(False, False)
        w.configure(bg=self.theme["bg_panel"])
        w.transient(self.fenetre)
        w.grab_set()

        hdr = tk.Frame(w, bg=self.theme["bg_header"], height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="VoiceLingo - Transcription & Traduction Locale",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg=self.theme["bg_header"]
        ).pack(side="left", padx=16, pady=14)

        contenu = tk.Frame(w, bg=self.theme["bg_panel"])
        contenu.pack(fill="both", expand=True, padx=22, pady=16)

        tk.Label(
            contenu,
            text="Contexte et Origine du Projet",
            font=("Segoe UI", 11, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_panel"]
        ).pack(anchor="w", pady=(0, 4))

        resume_contexte = (
            "Ce projet est ne d'un besoin personnel : j'avais regulierement besoin "
            "de suivre des tutoriels video techniques en ligne, mais ne maitrisant pas "
            "l'anglais a 100% et certaines videos n'ayant pas de sous-titres, "
            "j'ai imagine et concu VoiceLingo en 2026 pour transcrire automatiquement "
            "l'audio, traduire les propos sans deformer les concepts et termes de code "
            "(function, class, API, Docker...), et generer des sous-titres SRT conformes "
            "ou des doublages de maniere 100% locale, autonome et gratuite."
        )

        tk.Label(
            contenu,
            text=resume_contexte,
            font=("Segoe UI", 9),
            fg=self.theme["fg_text"],
            bg=self.theme["bg_panel"],
            wraplength=490,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        tk.Frame(contenu, bg=self.theme["border"], height=1).pack(fill="x", pady=6)

        tk.Label(
            contenu,
            text="Concepteur : Mouhamadou Lamine Niang",
            font=("Segoe UI", 10, "bold"),
            fg=self.theme["fg_title"],
            bg=self.theme["bg_panel"]
        ).pack(anchor="w")

        tk.Label(
            contenu,
            text="Annee de creation : 2026",
            font=("Segoe UI", 9),
            fg=self.theme["fg_subtext"],
            bg=self.theme["bg_panel"]
        ).pack(anchor="w", pady=(2, 4))

        lbl_mail = tk.Label(
            contenu,
            text="Contact : mouhamedlniang@gmail.com",
            font=("Segoe UI", 9, "underline"),
            fg=self.theme["accent"],
            bg=self.theme["bg_panel"],
            cursor="hand2"
        )
        lbl_mail.pack(anchor="w", pady=(0, 12))
        lbl_mail.bind("<Button-1>", lambda e: webbrowser.open("mailto:mouhamedlniang@gmail.com"))

        tk.Button(
            contenu,
            text="Fermer",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"],
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=w.destroy
        ).pack(side="bottom", anchor="e")

    def _ouvrir_parametres(self):
        """Ouvre le dialogue de configuration des modeles IA."""
        w = tk.Toplevel(self.fenetre)
        w.title("Parametres des Modeles IA")
        w.geometry("520x560")
        w.resizable(False, True)
        w.configure(bg=self.theme["bg_panel"])
        w.transient(self.fenetre)
        w.grab_set()

        hdr = tk.Frame(w, bg=self.theme["bg_header"], height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr,
            text="Configuration des Modeles IA",
            font=("Segoe UI", 11, "bold"),
            fg="#ffffff",
            bg=self.theme["bg_header"]
        ).pack(side="left", padx=16, pady=12)

        contenu = tk.Frame(w, bg=self.theme["bg_panel"])
        contenu.pack(fill="both", expand=True, padx=20, pady=16)

        def champ_combo(label, options, actuel, aide):
            tk.Label(contenu, text=label, font=("Segoe UI", 9, "bold"), fg=self.theme["fg_title"], bg=self.theme["bg_panel"]).pack(anchor="w", pady=(8, 2))
            var = tk.StringVar(value=actuel)
            cb = ttk.Combobox(contenu, textvariable=var, values=options, state="readonly", font=("Segoe UI", 9))
            cb.pack(fill="x")
            if aide:
                tk.Label(contenu, text=aide, font=("Segoe UI", 7), fg=self.theme["fg_subtext"], bg=self.theme["bg_panel"]).pack(anchor="w", pady=(1, 4))
            return var

        var_whisper = champ_combo(
            "whisper_model_size",
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            self.config.get("whisper_model_size", "base"),
            "base = tres rapide et leger | large-v3 = qualite maximale"
        )

        var_device = champ_combo(
            "whisper_device",
            ["cpu", "cuda"],
            self.config.get("whisper_device", "cpu"),
            "cpu = universel | cuda = acceleration NVIDIA GPU"
        )

        var_nllb = champ_combo(
            "nllb_model",
            [
                "facebook/nllb-200-distilled-600M",
                "facebook/nllb-200-1.3B",
                "facebook/nllb-200-3.3B"
            ],
            self.config.get("nllb_model", "facebook/nllb-200-distilled-600M"),
            "600M = rapide et peu gourmand en RAM"
        )

        tk.Label(contenu, text="Dossier de sortie par defaut", font=("Segoe UI", 9, "bold"), fg=self.theme["fg_title"], bg=self.theme["bg_panel"]).pack(anchor="w", pady=(10, 2))
        f_dir = tk.Frame(contenu, bg=self.theme["bg_panel"])
        f_dir.pack(fill="x", pady=(0, 16))

        entree_dir = ttk.Entry(f_dir, font=("Segoe UI", 9))
        entree_dir.insert(0, self.config.get("output_dir", ""))
        entree_dir.pack(side="left", fill="x", expand=True)

        def choisir_dir():
            d = filedialog.askdirectory(parent=w)
            if d:
                entree_dir.delete(0, "end")
                entree_dir.insert(0, d)

        tk.Button(f_dir, text="...", font=("Segoe UI", 8), bg=self.theme["bg_card"], fg=self.theme["fg_title"], padx=8, cursor="hand2", command=choisir_dir).pack(side="left", padx=(4, 0))

        def enregistrer():
            self.config["whisper_model_size"] = var_whisper.get()
            self.config["whisper_device"] = var_device.get()
            self.config["nllb_model"] = var_nllb.get()
            self.config["output_dir"] = entree_dir.get().strip()
            save_config(self.config)
            self._rafraichir_panneau_droit()
            w.destroy()
            messagebox.showinfo("Configuration sauvegardee", "Les parametres ont ete enregistres dans config.json.", parent=self.fenetre)

        tk.Button(
            contenu,
            text="Sauvegarder les Parametres",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=self.theme["accent"],
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=enregistrer
        ).pack(fill="x", pady=(10, 0))
