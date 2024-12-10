import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QMessageBox,
    QProgressDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

from src.core.config import load_config, save_config
from src.core.download import DownloadManager
from src.core.m3u import M3UParser

from src.ui.download_tab import DownloadTab
from src.ui.queue_tab import QueueTab
from src.ui.stats_tab import StatsTab
from src.ui.config_tab import ConfigTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.m3u_url = self.config.get("m3u_url", "")
        self.entries = []
        self.vod_info = {}
        self.download_manager = DownloadManager(self.config)
        self.m3u_parser = M3UParser()
        self.loading_dialog = None
        self.loader_thread = None
        
        # Obtenir le chemin absolu de l'icône
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        
        self.setWindowTitle("GrabNWatch")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setGeometry(100, 100, 1000, 700)
        
        self.dark_mode = self.config.get("dark_mode", False)
        self.init_ui()
        self.try_load_m3u_content()
        self.show_startup_message()

    def init_ui(self):
        """Initialiser l'interface utilisateur"""
        # Configuration des onglets
        self.tabs = QTabWidget(self)
        
        # Créer les onglets
        self.download_tab = DownloadTab(self)
        self.queue_tab = QueueTab(self)
        self.stats_tab = StatsTab(self)
        self.config_tab = ConfigTab(self)
        
        # Ajouter les onglets
        self.tabs.addTab(self.download_tab, "Téléchargement")
        self.tabs.addTab(self.queue_tab, "File d'attente")
        self.tabs.addTab(self.stats_tab, "Statistiques")
        self.tabs.addTab(self.config_tab, "Configuration")
        
        self.setCentralWidget(self.tabs)

    def try_load_m3u_content(self):
        """Tente de charger le contenu M3U si l'URL est valide"""
        if not self.m3u_url:
            return
            
        if not self.m3u_url.startswith("http"):
            QMessageBox.warning(self, "Erreur", "L'URL doit commencer par 'http://' ou 'https://'")
            return

        try:
            logger.debug(f"Début du chargement M3U depuis {self.m3u_url}")
            self.loading_dialog = QProgressDialog("Préparation du chargement...", "Annuler", 0, 0, self)
            self.loading_dialog.setWindowTitle("Chargement M3U")
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.setMinimumDuration(0)
            self.loading_dialog.setAutoClose(False)
            self.loading_dialog.setAutoReset(False)
            self.loading_dialog.setMinimumWidth(300)

            # Arrêter le thread précédent s'il existe
            if self.loader_thread is not None:
                self.loader_thread.stop()
                self.loader_thread.wait()
                self.loader_thread.deleteLater()

            self.loader_thread = self.m3u_parser.parse_url(self.m3u_url)
            self.loader_thread.finished.connect(self.on_m3u_loaded)
            self.loader_thread.error.connect(self.on_m3u_error)
            self.loader_thread.progress.connect(self.loading_dialog.setLabelText)
            
            self.loading_dialog.canceled.connect(self.loader_thread.stop)
            
            self.loading_dialog.show()
            self.loader_thread.start()
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du chargement: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage du chargement: {str(e)}")
            if self.loading_dialog:
                self.loading_dialog.close()

    def on_m3u_loaded(self, result):
        """Appelé lorsque le M3U est chargé avec succès"""
        try:
            if self.loading_dialog and self.loading_dialog.wasCanceled():
                logger.debug("Chargement annulé par l'utilisateur")
                self.loading_dialog.close()
                return
                
            self.entries, self.vod_info = result
            
            if not self.entries:
                logger.warning("Aucune entrée trouvée dans le fichier M3U")
                QMessageBox.warning(self, "Attention", "Aucune entrée n'a été trouvée dans le fichier M3U.")
            else:
                logger.info(f"{len(self.entries)} entrées chargées avec succès")
                self.download_tab.update_filter_categories()
                QMessageBox.information(self, "Succès", f"{len(self.entries)} entrées ont été chargées avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement des données: {str(e)}")
        finally:
            if self.loading_dialog:
                self.loading_dialog.close()
            # Nettoyer le thread
            if self.loader_thread:
                self.loader_thread.deleteLater()
                self.loader_thread = None

    def on_m3u_error(self, error_message):
        """Appelé en cas d'erreur lors du chargement du M3U"""
        try:
            logger.error(f"Erreur de chargement M3U: {error_message}")
            if self.loading_dialog:
                self.loading_dialog.close()
            QMessageBox.critical(self, "Erreur", error_message)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du message d'erreur: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'affichage du message d'erreur: {str(e)}")
        finally:
            # Nettoyer le thread
            if self.loader_thread:
                self.loader_thread.deleteLater()
                self.loader_thread = None

    def show_startup_message(self):
        """Afficher le message de démarrage"""
        QMessageBox.information(
            self,
            "Attention",
            "Veuillez couper les flux IPTV sur les autres appareils que vous utilisez, "
            "sinon le téléchargement ne fonctionnera pas, à moins que vous ne disposiez de plusieurs lignes."
        )

    def closeEvent(self, event):
        """Gérer la fermeture propre de l'application"""
        try:
            # Arrêter le thread de chargement M3U s'il est en cours
            if self.loader_thread is not None:
                logger.debug("Arrêt du thread de chargement M3U")
                self.loader_thread.stop()
                self.loader_thread.wait()
                self.loader_thread.deleteLater()
                self.loader_thread = None

            # Arrêter les téléchargements en cours
            if hasattr(self, 'download_manager'):
                if self.download_manager.current_download:
                    self.download_manager.current_download.stop()
                    self.download_manager.current_download.wait()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {str(e)}", exc_info=True)
        finally:
            event.accept()

    def apply_theme(self):
        """Appliquer le thème (clair ou sombre)"""
        if self.dark_mode:
            self.setStyleSheet("""
                /* Style global */
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }

                /* Onglets */
                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                    background-color: #1e1e1e;
                    top: -1px;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    padding: 8px 20px;
                    border: 1px solid #3d3d3d;
                    border-bottom: none;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    border-top: 2px solid #007acc;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }

                /* Listes */
                QListWidget {
                    background-color: #252526;
                    border: 1px solid #3d3d3d;
                    color: #ffffff;
                    outline: none;
                }
                QListWidget::item {
                    padding: 5px;
                }
                QListWidget::item:selected {
                    background-color: #094771;
                    color: #ffffff;
                }
                QListWidget::item:hover {
                    background-color: #2a2d2e;
                }

                /* Boutons */
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #094771;
                }
                QPushButton:disabled {
                    background-color: #3d3d3d;
                    color: #888888;
                }

                /* Champs de texte et spinbox */
                QLineEdit, QSpinBox {
                    background-color: #3c3c3c;
                    border: 1px solid #3d3d3d;
                    color: white;
                    padding: 5px;
                    selection-background-color: #094771;
                }
                QLineEdit:focus, QSpinBox:focus {
                    border: 1px solid #007acc;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #3c3c3c;
                    border: none;
                }
                QSpinBox::up-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-bottom: 4px solid #ffffff;
                }
                QSpinBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 4px solid #ffffff;
                }

                /* Groupes */
                QGroupBox {
                    border: 1px solid #3d3d3d;
                    margin-top: 12px;
                    padding-top: 5px;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 3px;
                    color: #ffffff;
                }

                /* Labels */
                QLabel {
                    color: #ffffff;
                }

                /* Checkbox */
                QCheckBox {
                    color: #ffffff;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #3d3d3d;
                    background: #3c3c3c;
                }
                QCheckBox::indicator:checked {
                    background: #007acc;
                    border: 1px solid #007acc;
                }
                QCheckBox::indicator:checked:hover {
                    background: #1177bb;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #007acc;
                }

                /* Messages */
                QMessageBox {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMessageBox QLabel {
                    color: #ffffff;
                }
                QMessageBox QPushButton {
                    min-width: 80px;
                }
            """)
        else:
            self.setStyleSheet("")  # Réinitialiser au thème par défaut