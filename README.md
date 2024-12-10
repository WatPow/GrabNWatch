# GrabNWatch

GrabNWatch est une application de bureau permettant de télécharger des contenus VOD à partir d'une liste M3U.

## Fonctionnalités

- Chargement de playlists M3U
- Recherche et filtrage des VODs par catégorie
- Téléchargement avec gestion de la file d'attente
- Contrôle de la bande passante
- Pause/Reprise des téléchargements
- Statistiques de téléchargement
- Mode sombre
- Configuration personnalisable

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/WatPow/GrabNWatch.git
cd GrabNWatch
```

2. Créer un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancer l'application :
```bash
python src/main.py
```

2. Dans l'onglet "Configuration", entrer l'URL de votre playlist M3U et cliquer sur "Sauvegarder URL"

3. Dans l'onglet "Téléchargement" :
   - Rechercher des VODs par nom
   - Filtrer par catégorie
   - Sélectionner un VOD et cliquer sur "Télécharger"

4. Dans l'onglet "File d'attente" :
   - Voir les téléchargements en cours et en attente
   - Mettre en pause/reprendre les téléchargements
   - Annuler les téléchargements
   - Voir l'historique des téléchargements

## Build

Pour créer un exécutable Windows :

Option 1 - Utiliser le script de build (recommandé) :
```bash
python build.py
```

L'exécutable sera créé dans le dossier `dist` sous le nom `GrabNWatch.exe`.

## Structure du projet

```
GrabNWatch/
├── src/
│   ├── assets/         # Ressources (icônes, etc.)
│   ├── core/           # Fonctionnalités principales
│   │   ├── download.py # Gestion des téléchargements
│   │   ├── config.py   # Gestion de la configuration
│   │   └── m3u.py      # Parsing M3U
│   ├── ui/            # Interface utilisateur
│   │   ├── main_window.py
│   │   ├── download_tab.py
│   │   ├── queue_tab.py
│   │   ├── stats_tab.py
│   │   └── config_tab.py
│   └── main.py        # Point d'entrée
├── requirements.txt
└── README.md
```

## Configuration

La configuration est sauvegardée dans `config.json` et comprend :
- URL de la playlist M3U
- Limite de bande passante (KB/s, 0 = illimité)
- Mode sombre
- Dossier de téléchargement
- Statistiques de téléchargement

## Remarques importantes

- Les téléchargements sont limités à un à la fois pour éviter la surcharge
- Les autres téléchargements sont automatiquement mis en file d'attente
- Veuillez vous assurer de ne pas avoir de flux IPTV actifs sur d'autres appareils lors de l'utilisation de GrabNWatch, sauf si vous disposez de plusieurs lignes
