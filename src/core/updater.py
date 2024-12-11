import os
import json
import requests
import sys
import platform
import tempfile
import zipfile
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from packaging import version

class UpdateCheckerThread(QThread):
    """Thread pour vérifier les mises à jour en arrière-plan"""
    finished = pyqtSignal(bool, str, str)  # (has_update, version, error_message)
    
    def __init__(self, current_version, api_url):
        super().__init__()
        self.current_version = current_version
        self.api_url = api_url
        self._stop = False

    def run(self):
        try:
            response = requests.get(
                f"{self.api_url}/latest",
                timeout=5,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            response.raise_for_status()
            release_info = response.json()
            
            latest_version = release_info["tag_name"].lstrip('v')
            if version.parse(latest_version) > version.parse(self.current_version):
                # Trouver l'URL de téléchargement pour Windows
                update_url = None
                for asset in release_info["assets"]:
                    if asset["name"].endswith(".zip"):
                        update_url = asset["browser_download_url"]
                        break
                
                if update_url:
                    self.finished.emit(True, latest_version, update_url)
                    return
                
            self.finished.emit(False, "", "")
            
        except requests.exceptions.Timeout:
            self.finished.emit(False, "", "Le serveur ne répond pas. Veuillez réessayer plus tard.")
        except requests.exceptions.ConnectionError:
            self.finished.emit(False, "", "Impossible de se connecter au serveur. Vérifiez votre connexion internet.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.finished.emit(False, "", "Aucune version publiée n'a été trouvée.")
            else:
                self.finished.emit(False, "", f"Erreur HTTP {e.response.status_code} lors de la vérification des mises à jour.")
        except Exception as e:
            self.finished.emit(False, "", f"Erreur lors de la vérification des mises à jour: {str(e)}")

    def stop(self):
        self._stop = True

class Updater(QObject):
    update_available = pyqtSignal(str)  # Signal émis quand une mise à jour est disponible
    update_progress = pyqtSignal(int)   # Signal pour la progression du téléchargement
    update_error = pyqtSignal(str)      # Signal en cas d'erreur
    update_success = pyqtSignal()       # Signal quand la mise à jour est terminée
    update_history_loaded = pyqtSignal(list)  # Signal émis avec l'historique des mises à jour
    check_finished = pyqtSignal()       # Signal émis quand la vérification est terminée

    def __init__(self):
        super().__init__()
        self.current_version = "1.0.0"  # Version actuelle du programme
        self.github_api_url = "https://api.github.com/repos/WatPow/GrabNWatch/releases"
        self.update_url = None
        self.new_version = None
        self._cached_history = None
        self._checker_thread = None

    def check_for_updates(self):
        """Vérifie si une mise à jour est disponible"""
        # Si un thread est déjà en cours, l'arrêter
        if self._checker_thread and self._checker_thread.isRunning():
            self._checker_thread.stop()
            self._checker_thread.wait()

        # Créer et démarrer un nouveau thread
        self._checker_thread = UpdateCheckerThread(self.current_version, self.github_api_url)
        self._checker_thread.finished.connect(self._on_check_finished)
        self._checker_thread.start()
        return True  # Indique que la vérification a commencé

    def _on_check_finished(self, has_update, version, message):
        """Appelé quand la vérification est terminée"""
        if has_update:
            self.new_version = version
            self.update_url = message
            self.update_available.emit(version)
        elif message:  # message contient l'erreur s'il y en a une
            self.update_error.emit(message)
        
        self.check_finished.emit()

    def load_update_history(self):
        """Charge l'historique des mises à jour depuis GitHub"""
        if self._cached_history is not None:
            self.update_history_loaded.emit(self._cached_history)
            return

        try:
            response = requests.get(self.github_api_url)
            response.raise_for_status()
            releases = response.json()
            
            history = []
            for release in releases:
                version = release["tag_name"].lstrip('v')
                # Convertir le corps de la release en liste de changements
                changes = [
                    line.lstrip("- ") 
                    for line in release["body"].split("\n") 
                    if line.strip() and not line.startswith("#")
                ]
                history.append((version, changes))
            
            self._cached_history = history
            self.update_history_loaded.emit(history)
            
        except Exception as e:
            self.update_error.emit(f"Erreur lors du chargement de l'historique: {str(e)}")
            self.update_history_loaded.emit([])

    def download_and_install_update(self):
        """Télécharge et installe la mise à jour"""
        if not self.update_url:
            self.update_error.emit("Aucune mise à jour disponible")
            return

        try:
            # Créer un dossier temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                # Télécharger le fichier
                response = requests.get(self.update_url, stream=True)
                response.raise_for_status()
                
                # Obtenir la taille totale
                total_size = int(response.headers.get('content-length', 0))
                
                # Préparer le fichier zip temporaire
                zip_path = os.path.join(temp_dir, "update.zip")
                downloaded_size = 0
                
                # Télécharger le fichier
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size:
                                progress = int(downloaded_size * 100 / total_size)
                                self.update_progress.emit(progress)

                # Extraire dans un sous-dossier temporaire
                extract_path = os.path.join(temp_dir, "extracted")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # Obtenir le chemin de l'exécutable actuel
                if getattr(sys, 'frozen', False):
                    current_dir = os.path.dirname(sys.executable)
                else:
                    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

                # Copier les nouveaux fichiers
                self._copy_tree(extract_path, current_dir)
                
                self.update_success.emit()
                
                # Redémarrer l'application si on est en mode frozen
                if getattr(sys, 'frozen', False):
                    os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            self.update_error.emit(f"Erreur lors de la mise à jour: {str(e)}")

    def _copy_tree(self, src, dst):
        """Copie récursivement les fichiers d'un dossier à l'autre"""
        import shutil
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
            else:
                os.makedirs(d, exist_ok=True)
                self._copy_tree(s, d) 