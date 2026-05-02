"""
main.py - Point d'entree principal de VoiceLingo.
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Initialise l'environnement d'execution, verifie la presence de FFmpeg et demarre l'interface graphique.
"""

# Configuration de l'environnement OpenMP pour eviter les conflits d'allocations de threads sur Windows
from ui import VoiceLingoApp
import subprocess
from tkinter import messagebox
import tkinter as tk
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def verifier_ffmpeg() -> bool:
    """
    Verifie la disponibilite de l'executable FFmpeg dans le PATH systeme.
    Retourne True si FFmpeg repond correctement, False sinon.
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, PermissionError):
        return False


def main():
    """
    Point de depart de l'application de bureau VoiceLingo.
    Controle les pre-requis systeme avant d'instancier l'interface utilisateur.
    """
    if not verifier_ffmpeg():
        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showerror(
            "FFmpeg manquant",
            "FFmpeg n'a pas ete detecte sur votre systeme.\n\n"
            "Veuillez installer FFmpeg et l'ajouter a votre variable d'environnement PATH :\n"
            "https://ffmpeg.org/download.html"
        )
        root_temp.destroy()
        return

    root = tk.Tk()
    VoiceLingoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
