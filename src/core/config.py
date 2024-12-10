import json
import os
import logging

CONFIG_FILE = "config.json"

def load_config():
    """Charger la configuration depuis le fichier"""
    default_config = {
        "m3u_url": "",
        "bandwidth_limit": 0,
        "dark_mode": False,
        "download_dir": "downloads",
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
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info("Configuration saved successfully.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde de la configuration: {e}") 