import os
import time
import requests
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QWaitCondition, QMutex, QMutexLocker
from src.core.config import save_config, get_default_downloads_dir

class DownloadThread(QThread):
    progress = pyqtSignal(str, int, float)  # name, progress, speed in KB/s
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, name, url, bandwidth_limit=None, config=None):
        super().__init__()
        self.name = name
        self.url = url
        self.bandwidth_limit = bandwidth_limit
        self.config = config or {}
        self.stop_flag = False
        self.paused = False
        self.pause_condition = QWaitCondition()
        self.pause_mutex = QMutex()
        
        # Attributs pour les statistiques
        self.total_size = 0
        self.downloaded_size = 0
        self.start_time = 0
        self.download_time = 0
        self.current_speed = 0
        self.speeds = []  # Liste des vitesses pour calculer la moyenne
        self.bytes_since_last_update = 0
        self.last_update_time = time.time()

    def run(self):
        try:
            self.start_time = time.time()
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            # Obtenir la taille totale du fichier
            self.total_size = int(response.headers.get('content-length', 0))
            if self.total_size == 0:
                raise Exception("Impossible de déterminer la taille du fichier")
            
            # Utiliser le dossier configuré ou le dossier par défaut du système
            download_dir = self.config.get("download_dir", get_default_downloads_dir())
            os.makedirs(download_dir, exist_ok=True)
            filename = os.path.join(download_dir, f"{self.name}.mp4")
            
            # Ouvrir le fichier en mode binaire avec buffer optimisé
            with open(filename, 'wb', buffering=1024*1024) as f:  # Buffer de 1MB
                self.downloaded_size = 0
                chunk_size = 1024*1024  # 1MB par chunk pour de meilleures performances
                self.last_update_time = time.time()
                self.bytes_since_last_update = 0
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # Vérifier si l'arrêt a été demandé
                    if self.stop_flag:
                        return
                    
                    # Gérer la pause
                    with QMutexLocker(self.pause_mutex):
                        while self.paused and not self.stop_flag:
                            self.pause_condition.wait(self.pause_mutex)
                    
                    if chunk:
                        f.write(chunk)
                        self.downloaded_size += len(chunk)
                        self.bytes_since_last_update += len(chunk)
                        
                        # Calculer la vitesse toutes les 0.5 secondes
                        current_time = time.time()
                        if current_time - self.last_update_time >= 0.5:
                            elapsed = current_time - self.last_update_time
                            speed = self.bytes_since_last_update / elapsed  # Octets par seconde
                            self.speeds.append(speed)
                            # Garder seulement les 3 dernières mesures pour une moyenne plus réactive
                            if len(self.speeds) > 3:
                                self.speeds.pop(0)
                            self.current_speed = sum(self.speeds) / len(self.speeds)
                            self.last_update_time = current_time
                            self.bytes_since_last_update = 0
                        
                        # Limiter la bande passante si nécessaire
                        if self.bandwidth_limit:
                            time.sleep(len(chunk) / (self.bandwidth_limit * 1024))
                        
                        # Émettre la progression avec la vitesse (convertie en KB/s)
                        progress = int(self.downloaded_size * 100 / self.total_size)
                        self.progress.emit(self.name, progress, self.current_speed / 1024)
            
            self.download_time = time.time() - self.start_time
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.stop_flag = True
        self.resume()  # Pour sortir de la pause si nécessaire

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        with QMutexLocker(self.pause_mutex):
            self.pause_condition.wakeAll()


class DownloadManager(QObject):
    download_progress = pyqtSignal(str, int, float)  # name, progress, speed
    download_finished = pyqtSignal(str)
    download_error = pyqtSignal(str, str)
    queue_updated = pyqtSignal()
    download_paused = pyqtSignal(str)
    download_resumed = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.download_queue = []  # [(name, url, bandwidth_limit), ...]
        self.current_download = None  # DownloadThread actif
        self.download_history = []  # [(name, status, timestamp), ...]
        self.stats = self.config.get('stats', {
            'total_downloads': 0,
            'total_size': 0,
            'average_speed': 0,
            'download_times': []
        })

    def add_to_queue(self, name, url, bandwidth_limit=None):
        self.download_queue.append((name, url, bandwidth_limit))
        self.download_history.append((name, "En attente", time.time()))
        self.queue_updated.emit()
        self.process_queue()

    def process_queue(self):
        if not self.current_download and self.download_queue:
            name, url, bandwidth_limit = self.download_queue[0]
            self.start_download(name, url, bandwidth_limit)
            self.download_queue.pop(0)

    def start_download(self, name, url, bandwidth_limit=None):
        self.current_download = DownloadThread(name, url, bandwidth_limit, self.config)
        self.current_download.progress.connect(
            lambda n, p, s: self.download_progress.emit(n, p, s)
        )
        self.current_download.finished.connect(lambda: self.on_download_finished(name))
        self.current_download.error.connect(lambda e: self.on_download_error(name, e))
        self.current_download.start()
        self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
        self.download_history.append((name, "En cours", time.time()))
        self.queue_updated.emit()

    def format_size(self, size_in_bytes):
        """Formater la taille en format lisible"""
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} To"

    def on_download_finished(self, name):
        """Appelé quand un téléchargement est terminé"""
        if self.current_download:
            # Mise à jour des statistiques
            self.stats['total_downloads'] += 1
            self.stats['total_size'] += self.current_download.total_size
            if self.current_download.download_time > 0:
                speed = self.current_download.total_size / self.current_download.download_time
                self.stats['download_times'].append(speed)
                self.stats['average_speed'] = sum(self.stats['download_times']) / len(self.stats['download_times'])
            
            # Formater la taille totale pour l'historique
            total_size = self.format_size(self.current_download.total_size)
            
            # Sauvegarder les statistiques dans la configuration
            self.config['stats'] = self.stats
            save_config(self.config)
            
            # Nettoyer le thread de téléchargement
            self.current_download.deleteLater()
            self.current_download = None
            
            # Mettre à jour l'historique avec la taille
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, f"Terminé - {total_size}", time.time()))
            self.download_finished.emit(name)
            
            # Démarrer automatiquement le prochain téléchargement
            if self.download_queue:
                next_name, next_url, next_bandwidth = self.download_queue.pop(0)
                self.start_download(next_name, next_url, next_bandwidth)

    def on_download_error(self, name, error):
        if self.current_download:
            self.current_download.deleteLater()
            self.current_download = None
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, f"Erreur: {error}", time.time()))
            self.download_error.emit(name, error)
            self.queue_updated.emit()
            
            # Démarrer automatiquement le prochain téléchargement même en cas d'erreur
            if self.download_queue:
                next_name, next_url, next_bandwidth = self.download_queue.pop(0)
                self.start_download(next_name, next_url, next_bandwidth)

    def cancel_download(self, name):
        # Si c'est le téléchargement en cours
        if self.current_download and self.current_download.name == name:
            self.current_download.stop()
            # Attendre que le thread soit terminé
            self.current_download.wait()
            # Maintenant on peut supprimer le thread en toute sécurité
            self.current_download.deleteLater()
            self.current_download = None
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, "Annulé", time.time()))
            self.queue_updated.emit()
            self.process_queue()
        # Si c'est dans la file d'attente
        else:
            self.download_queue = [(n, u, b) for n, u, b in self.download_queue if n != name]
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, "Annulé", time.time()))
            self.queue_updated.emit()

    def pause_download(self, name):
        if self.current_download and self.current_download.name == name:
            self.current_download.pause()
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, "En pause", time.time()))
            self.download_paused.emit(name)
            self.queue_updated.emit()

    def resume_download(self, name):
        if self.current_download and self.current_download.name == name:
            self.current_download.resume()
            self.download_history = [(n, s, t) for n, s, t in self.download_history if n != name]
            self.download_history.append((name, "En cours", time.time()))
            self.download_resumed.emit(name)
            self.queue_updated.emit() 