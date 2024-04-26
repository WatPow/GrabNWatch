# GrabNWatch

## Description
GrabNWatch est une application conçue pour télécharger des vidéos à la demande (VOD) à partir d'une URL M3U. Elle permet aux utilisateurs de rechercher et de télécharger des VODs spécifiques pour un visionnage hors ligne.

## Installation
Pour installer GrabNWatch, suivez ces étapes :

1. Clonez le dépôt GitHub :
   ```
   git clone https://github.com/WatPow/GrabNWatch.git
   ```
2. Naviguez dans le répertoire du projet :
   ```
   cd GrabNWatch
   ```
3. Installez les dépendances nécessaires :
   ```
   pip install -r requirements.txt
   ```
4. Exécutez l'application :
   ```
   python main.py
   ```
5. Pour construire une version exécutable de l'application, utilisez PyInstaller :
   ```
   pyinstaller --onefile --windowed --add-data "icon.ico;." main.py
   ```

## Exemples d'utilisation
Voici quelques exemples d'utilisation de GrabNWatch :

- Lancer l'application et entrer l'URL M3U dans l'onglet de configuration pour commencer à charger les contenus disponibles.
- Utiliser la barre de recherche pour filtrer et trouver des VODs spécifiques.
- Sélectionner une VOD dans la liste et cliquer sur "Télécharger la VOD sélectionnée" pour commencer le téléchargement.

### Remerciements :
[@N04H2601 pour le GUI](https://github.com/N04H2601)

## Licence
GrabNWatch est distribué sous la licence MIT, ce qui permet une grande flexibilité pour l'utilisation et la distribution du logiciel. Pour plus de détails, consultez le fichier LICENSE inclus dans le dépôt GitHub.
