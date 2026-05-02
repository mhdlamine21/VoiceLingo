"""
build.py - Script de packaging de VoiceLingo en binaire executable autonome (PyInstaller).
Auteur: Mouhamadou Lamine Niang (2026) - mouhamedlniang@gmail.com
Description: Genere un package autonome Windows (.exe) ou Linux/macOS sans necessiter
             l'installation prealable de Python par l'utilisateur final.

Usage :
    python build.py               # Build standard (dossier dist/VoiceLingo)
    python build.py --onefile     # Binaire .exe unique
    python build.py --check       # Verification prealable des prerequis
"""

import sys
import subprocess
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).parent

# Codes couleur ANSI pour sortie console
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def log_ok(msg):
    print(f"{GREEN}  [OK]  {msg}{RESET}")


def log_warn(msg):
    print(f"{YELLOW}  [WARN]  {msg}{RESET}")


def log_err(msg):
    print(f"{RED}  [ERR]  {msg}{RESET}")


def log_info(msg):
    print(f"        {msg}")


# Verifications des prerequis

def check_dependencies() -> bool:
    """Verifie que les outils et bibliotheques requis sont operationnels."""
    print(f"\n{BOLD}Verification des dependances et de l'environnement{RESET}\n")
    ok = True

    # Version de Python
    if sys.version_info >= (3, 10):
        log_ok(f"Python {sys.version.split()[0]}")
    else:
        log_err(f"Python 3.10+ requis (version actuelle : {sys.version.split()[0]})")
        ok = False

    # Verifier PyInstaller
    try:
        import PyInstaller
        log_ok(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        log_err("PyInstaller n'est pas installe (pip install pyinstaller)")
        ok = False

    # Detection FFmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
        if r.returncode == 0:
            log_ok("FFmpeg present dans le PATH")
        else:
            log_warn("FFmpeg absent ou non repondant")
    except Exception:
        log_warn("FFmpeg non detecte - necessaire pour l'execution de l'application")

    # Module graphique tkinter
    try:
        import tkinter  # noqa: F401
        log_ok("tkinter operationnel")
    except ImportError:
        log_err("tkinter manquant dans l'environnement Python")
        ok = False

    # Fichiers sources vitaux
    essential = [
        "main.py", "ui.py", "processor.py", "config.json",
        "speech_to_text.py", "context_translation_ia.py",
        "srt_generator.py", "video_handler.py"
    ]
    for f in essential:
        path = ROOT / f
        if path.exists():
            log_ok(f"Fichier source : {f}")
        else:
            log_err(f"Fichier source manquant : {f}")
            ok = False

    # Ressources graphiques
    logo = ROOT / "assets" / "icons" / "logo.svg"
    if logo.exists():
        log_ok("Logo vectoriel : assets/icons/logo.svg")
    else:
        log_warn("assets/icons/logo.svg manquant - un rendu de secours sera utilise")

    print()
    return ok


# Generation du fichier de specifications PyInstaller

def generate_spec(onefile: bool = False) -> str:
    """Genere dynamiquement le fichier voicelingo.spec."""
    datas = [
        ("config.json", "."),
        ("assets/", "assets"),
        ("speaker_wavs/.gitkeep", "speaker_wavs"),
    ]

    hidden_imports = [
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "pathlib",
        "threading",
        "subprocess",
        "json",
        "shutil",
        "tempfile",
        "re",
        "math",
        "cairosvg",
    ]

    excludes = [
        "matplotlib",
        "numpy.testing",
        "scipy",
        "IPython",
        "notebook",
        "pytest",
    ]

    datas_str = "\n    ".join(f"('{s}', '{d}')," for s, d in datas)
    hidden_str = "\n    ".join(f"'{h}'," for h in hidden_imports)
    excl_str = "\n    ".join(f"'{e}'," for e in excludes)

    icon_path = ROOT / "assets" / "icons" / "logo.ico"
    icon_line = f"icon=r'{icon_path}'," if icon_path.exists() else "# icon='logo.ico',"

    spec = f"""# -*- mode: python ; coding: utf-8 -*-
# VoiceLingo - Fichier spec PyInstaller
# Produit automatiquement par build.py

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[r'{ROOT}'],
    binaries=[],
    datas=[
    {datas_str}
    ],
    hiddenimports=[
    {hidden_str}
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
    {excl_str}
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
"""

    if onefile:
        spec += f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VoiceLingo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    {icon_line}
)
"""
    else:
        spec += f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoiceLingo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    {icon_line}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceLingo',
)
"""
    return spec


# Execution du build

def build(onefile: bool = False) -> None:
    """Compile l'application VoiceLingo."""
    print(f"\n{BOLD}Compilation VoiceLingo{RESET}")
    print(
        f"  Mode   : {'--onefile (Fichier unique)' if onefile else '--onedir (Repertoire complet dist/VoiceLingo/)'}")
    print(f"  Racine : {ROOT}\n")

    spec_content = generate_spec(onefile)
    spec_path = ROOT / "voicelingo.spec"
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    log_ok("voicelingo.spec genere")

    for d in ["build", "dist"]:
        if (ROOT / d).exists():
            shutil.rmtree(ROOT / d)
            log_info(f"Dossier {d}/ nettoye")

    print(f"\n{BOLD}Lancement de PyInstaller...{RESET}")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--log-level", "WARN",
        str(spec_path),
    ]

    result = subprocess.run(cmd, cwd=str(ROOT))

    if result.returncode == 0:
        dist = ROOT / "dist"
        if onefile:
            exe = dist / "VoiceLingo.exe"
            if not exe.exists():
                exe = dist / "VoiceLingo"
            size = exe.stat().st_size / (1024 * 1024) if exe.exists() else 0
            print(f"\n{GREEN}{BOLD}Build execute avec succes !{RESET}")
            log_ok(f"Fichier binaire : {exe}")
            log_info(f"Taille : {size:.1f} Mo")
        else:
            folder = dist / "VoiceLingo"
            exe = folder / "VoiceLingo.exe"
            if not exe.exists():
                exe = folder / "VoiceLingo"
            print(f"\n{GREEN}{BOLD}Build execute avec succes !{RESET}")
            log_ok(f"Dossier distribuable : {folder}")
            log_ok(f"Executable : {exe}")
        print()
    else:
        print(f"\n{RED}{BOLD}La compilation a echoue.{RESET}")
        log_info("Veuillez examiner les journaux d'erreurs ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script de packaging VoiceLingo en application autonome",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--onefile", action="store_true", help="Generer un seul fichier .exe autonome")
    parser.add_argument("--check", action="store_true", help="Verifier les prerequis et dependances")
    args = parser.parse_args()

    if args.check:
        ok = check_dependencies()
        sys.exit(0 if ok else 1)

    ok = check_dependencies()
    if not ok:
        print(f"\n{RED}Veuillez resoudre les avertissements avant de relancer le build.{RESET}")
        sys.exit(1)

    build(onefile=args.onefile)
