# VoiceLingo - Guide de packaging en application standalone

Ce guide explique comment transformer VoiceLingo en une application
téléchargeable et exécutable sans installer Python - comme un `.jar` Java
ou un installateur Windows classique.

---

## Option 1 - PyInstaller (recommandée pour ton portfolio)

**Ce que ça produit :** Un dossier `dist/VoiceLingo/` ou un seul `.exe`
que tu distribues via GitHub Releases.

### Étape 1 - Installer PyInstaller

```bash
pip install pyinstaller
```

### Étape 2 - Lancer le build

```bash
# Mode dossier (recommandé - plus rapide à démarrer)
python build.py

# Mode fichier unique (plus portable mais plus lent à démarrer)
python build.py --onefile

# Vérifier les dépendances avant de builder
python build.py --check
```

### Étape 3 - Tester le résultat

```
dist/
└── VoiceLingo/
    ├── VoiceLingo.exe        ← double-cliquer pour lancer
    ├── _internal/            ← librairies Python bundlées
    └── assets/               ← logo, ressources
```

> **Important :** Distribue le dossier `VoiceLingo/` entier (en .zip),
> pas seulement le .exe.

---

## Option 2 - Inno Setup (installateur Windows professionnel)

Produit un vrai installateur `.exe` avec progression d'installation,
raccourcis bureau et menu démarrer - comme un vrai logiciel Windows.

### Étape 1 - Prérequis

1. Builder d'abord avec PyInstaller (option 1 ci-dessus)
2. Télécharger **Inno Setup** : https://jrsoftware.org/isdl.php

### Étape 2 - Fichier .iss (script Inno Setup)

Crée un fichier `installer.iss` :

```ini
[Setup]
AppName=VoiceLingo
AppVersion=1.0.0
AppPublisher=Ton Nom
AppPublisherURL=https://github.com/TON_USERNAME/voicelingo
DefaultDirName={autopf}\VoiceLingo
DefaultGroupName=VoiceLingo
OutputDir=installer_output
OutputBaseFilename=VoiceLingo_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le bureau"; GroupDescription: "Icônes additionnelles :"

[Files]
; Inclure tout le dossier dist/VoiceLingo/
Source: "dist\VoiceLingo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VoiceLingo"; Filename: "{app}\VoiceLingo.exe"
Name: "{autodesktop}\VoiceLingo"; Filename: "{app}\VoiceLingo.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VoiceLingo.exe"; Description: "Lancer VoiceLingo"; Flags: nowait postinstall skipifsilent
```

### Étape 3 - Compiler l'installateur

Ouvrir `installer.iss` dans Inno Setup et cliquer **Build → Compile**.
Résultat : `installer_output/VoiceLingo_Setup_v1.0.0.exe`

---

## Option 3 - Nuitka (alternative à PyInstaller)

Nuitka compile Python en C puis en binaire natif - résultat plus rapide
et plus difficile à décompiler.

```bash
pip install nuitka

# Build Windows one-file
python -m nuitka \
  --onefile \
  --windows-disable-console \
  --include-data-dir=assets=assets \
  --include-data-files=config.json=config.json \
  --output-filename=VoiceLingo.exe \
  main.py
```

> Plus lent à compiler mais produit un exécutable plus performant.

---

## Ce que les modèles IA impliquent pour la distribution

Les modèles IA ne peuvent PAS être inclus dans l'exécutable (7+ Go).

| Modèle | Taille | Téléchargé par | Au 1er lancement |
|--------|--------|----------------|-----------------|
| Whisper large-v3 | ~3 Go | faster-whisper | Automatique |
| NLLB-200-600M | ~2.4 Go | transformers | Automatique |
| XTTS-v2 | ~1.9 Go | Coqui TTS | Automatique (mode doublage) |

**Solution recommandée :** Documenter clairement dans le README que le
1er lancement télécharge ~7 Go de modèles. L'utilisateur a besoin d'une
connexion internet uniquement pour ce téléchargement initial.

Pour les utilisateurs sans connexion, inclure les instructions pour
copier les modèles depuis `~/.cache/huggingface/`.

---

## Résumé : quelle option choisir ?

| Situation | Option recommandée |
|-----------|-------------------|
| Portfolio GitHub rapide | PyInstaller `--onefile` |
| Distribution professionnelle Windows | Inno Setup (après PyInstaller) |
| Performance maximale | Nuitka |
| Démo technique pour recruteur | Lien GitHub + instructions pip |

---

## Commandes build complètes

```bash
# 1. Vérifier les dépendances
python build.py --check

# 2. Builder le dossier distributable
python build.py

# 3. Compresser pour GitHub Releases
# Windows PowerShell :
Compress-Archive -Path "dist\VoiceLingo" -DestinationPath "VoiceLingo_v1.0.0_Windows.zip"

# Linux/macOS :
zip -r VoiceLingo_v1.0.0_Linux.zip dist/VoiceLingo/

# 4. Ajouter à la release GitHub
# → GitHub > Releases > New release > Upload files
```
