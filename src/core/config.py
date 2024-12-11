import json
import os
import logging
import platform
from pathlib import Path

def get_config_dir():
    """Retourne le répertoire de configuration selon le système d'exploitation"""
    if platform.system() == "Windows":
        config_dir = os.path.join(os.getenv('APPDATA'), 'GrabNWatch')
    else:
        config_dir = os.path.join(str(Path.home()), '.config', 'grabnwatch')
    
    # Créer le répertoire s'il n'existe pas
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_default_downloads_dir():
    """Retourne le dossier de téléchargements par défaut du système"""
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        return os.path.join(str(Path.home()), "Downloads")

CONFIG_FILE = os.path.join(get_config_dir(), "config.json")

def validate_download_dir(download_dir):
    """Valide et prépare le dossier de téléchargement
    
    Returns:
        tuple: (bool, str) - (est_valide, message_erreur)
    """
    try:
        # Convertir en chemin absolu si nécessaire
        download_dir = os.path.abspath(os.path.expanduser(download_dir))
        
        # Vérifier si le dossier existe, sinon le créer
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # Vérifier les permissions d'écriture
        test_file = os.path.join(download_dir, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True, download_dir
        except (IOError, PermissionError):
            return False, f"Pas de permission d'écriture dans le dossier: {download_dir}"
            
    except Exception as e:
        return False, f"Erreur lors de la validation du dossier: {str(e)}"

def load_config():
    """Charger la configuration depuis le fichier"""
    default_config = {
        "m3u_url": "",
        "bandwidth_limit": 0,
        "dark_mode": False,
        "download_dir": get_default_downloads_dir(),
        "auto_check_updates": True,
        "stats": {
            "total_downloads": 0,
            "total_size": 0,
            "average_speed": 0,
            "download_times": []
        }
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # S'assurer que toutes les clés par défaut existent
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                # Valider le dossier de téléchargement
                is_valid, result = validate_download_dir(config["download_dir"])
                if not is_valid:
                    logging.warning(f"Dossier de téléchargement invalide: {result}")
                    logging.info("Utilisation du dossier par défaut")
                    config["download_dir"] = default_config["download_dir"]
                else:
                    config["download_dir"] = result
                
                return config
        except json.JSONDecodeError:
            logging.error("Erreur lors de la lecture du fichier de configuration")
            return default_config.copy()
        except Exception as e:
            logging.error(f"Erreur inattendue lors du chargement de la configuration: {e}")
            return default_config.copy()
    return default_config.copy()

def save_config(config):
    """Sauvegarder la configuration dans le fichier"""
    try:
        # Valider le dossier de téléchargement avant la sauvegarde
        is_valid, result = validate_download_dir(config["download_dir"])
        if not is_valid:
            raise ValueError(f"Dossier de téléchargement invalide: {result}")
        
        config["download_dir"] = result  # Utiliser le chemin absolu validé
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info("Configuration sauvegardée avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
        raise 