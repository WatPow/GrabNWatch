# GrabNWatch 🎥

## 📜 Description
**GrabNWatch** est une outil conçu pour le téléchargement de vidéos à la demande (VOD) via des URL M3U. Elle offre la possibilité de rechercher et de télécharger des VODs spécifiques pour les visionner ensuite hors ligne.

## 🛠 Installation
Suivez ces étapes simples pour installer **GrabNWatch** :

1. **Clonez le dépôt GitHub :**
   ```bash
   git clone https://github.com/WatPow/GrabNWatch.git
   ```
2. **Naviguez dans le répertoire du projet :**
   ```bash
   cd GrabNWatch
   ```
3. **Installez les dépendances nécessaires :**
   ```bash
   pip install -r requirements.txt
   ```
4. **Exécutez l'application :**
   ```bash
   python main.py
   ```
5. **Pour construire une version exécutable de l'application, utilisez PyInstaller :**
   ```bash
   pyinstaller --onefile --windowed --add-data "icon.ico;." --name GrabNWatch main.py
   ```

## 🌟 Exemples d'utilisation
Voici comment utiliser l'application **GrabNWatch** :

- **Démarrage :** Lancez l'application et entrez l'URL M3U dans l'onglet de configuration pour charger les contenus disponibles.
- **Recherche :** Utilisez la barre de recherche pour filtrer et trouver des VODs spécifiques.
- **Téléchargement :** Sélectionnez une VOD dans la liste et cliquez sur "Télécharger la VOD sélectionnée" pour lancer le téléchargement.

## 🤝 Remerciements
[@N04H2601](https://github.com/N04H2601) pour le GUI


## 📄 Licence
**GrabNWatch** est fièrement distribué sous la licence MIT, offrant une grande flexibilité d'utilisation et de distribution. Pour plus de détails, veuillez consulter le fichier LICENSE inclus dans le dépôt GitHub.
