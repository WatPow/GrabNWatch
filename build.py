import PyInstaller.__main__
import os
import shutil

def build():
    # Nettoyer les dossiers de build précédents
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # Configuration PyInstaller
    PyInstaller.__main__.run([
        'src/main.py',                    # Script principal
        '--name=GrabNWatch',              # Nom de l'exécutable
        '--onefile',                      # Un seul fichier exécutable
        '--windowed',                     # Mode fenêtré (pas de console)
        '--icon=src/assets/icon.ico',     # Icône de l'application
        '--add-data=src;src',             # Inclure tout le package src
        '--clean',                        # Nettoyer avant la construction
        '--noconfirm',                    # Ne pas demander de confirmation
        '--paths=.',                      # Ajouter le répertoire courant au PYTHONPATH
        '--uac-admin',                    # Demander les droits admin explicitement
        '--disable-windowed-traceback',   # Désactiver le traceback en mode fenêtré
        '--version-file=version.txt',     # Ajouter des informations de version
    ])

if __name__ == "__main__":
    build() 