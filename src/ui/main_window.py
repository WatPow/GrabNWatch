import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QMessageBox,
    QProgressDialog, QApplication, QMenuBar,
    QMenu, QAction, QTextBrowser, QDialog,
    QVBoxLayout, QDialogButtonBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import markdown2
import sys

logger = logging.getLogger(__name__)

from src.core.config import load_config, save_config
from src.core.download import DownloadManager
from src.core.m3u import M3UParser
from src.core.updater import Updater

from src.ui.download_tab import DownloadTab
from src.ui.queue_tab import QueueTab
from src.ui.stats_tab import StatsTab
from src.ui.config_tab import ConfigTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GrabNWatch")
        
        # Définir l'icône de la fenêtre
        try:
            # Essayer d'abord le chemin relatif normal
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
            if not os.path.exists(icon_path):
                # Si on est dans un environnement PyInstaller
                if hasattr(sys, '_MEIPASS'):
                    icon_path = os.path.join(sys._MEIPASS, 'src', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône: {e}")
        
        # Charger la configuration
        self.config = load_config()
        self.dark_mode = self.config.get("dark_mode", False)
        self.m3u_url = self.config.get("m3u_url", "")
        
        # Initialiser les attributs
        self.progress_dialog = None
        self._update_error_shown = False
        self._update_available_shown = False
        self.loader_thread = None
        self.entries = []
        self.vod_info = {}
        
        # Initialiser les composants
        self.download_manager = DownloadManager(self.config)
        self.m3u_parser = M3UParser()
        
        # Créer la barre de menu
        self.create_menu()
        
        # Initialiser l'interface principale
        self.init_ui()
        
        # Initialiser le gestionnaire de mises à jour
        self.init_updater()
        
        # Appliquer le thème
        self.apply_theme()

        # Charger le contenu M3U et afficher le message de démarrage
        self.try_load_m3u_content()
        self.show_startup_message()

    def create_menu(self):
        """Crée la barre de menu de l'application"""
        self.menubar = self.menuBar()
        
        # Menu Aide
        help_menu = self.menubar.addMenu("Aide")
        
        # Actions du menu Aide
        check_updates_action = QAction("Vérifier les mises à jour", self)
        check_updates_action.triggered.connect(self.check_updates_manually)
        help_menu.addAction(check_updates_action)
        
        update_history_action = QAction("Historique des mises à jour", self)
        update_history_action.triggered.connect(self.show_update_history)
        help_menu.addAction(update_history_action)
        
        help_menu.addSeparator()
        
        auto_check_action = QAction("Vérification automatique", self)
        auto_check_action.setCheckable(True)
        auto_check_action.setChecked(self.config.get("auto_check_updates", True))
        auto_check_action.triggered.connect(self.toggle_auto_check)
        help_menu.addAction(auto_check_action)

    def init_updater(self):
        """Initialise le gestionnaire de mises à jour"""
        self.updater = Updater()
        self.updater.update_available.connect(self.on_update_available)
        self.updater.update_progress.connect(self.on_update_progress)
        self.updater.update_error.connect(self.on_update_error)
        self.updater.update_success.connect(self.on_update_success)
        self.updater.update_history_loaded.connect(self.on_update_history_loaded)
        
        # Créer la boîte de dialogue de progression
        self.progress_dialog = None
        
        # Vérifier les mises à jour au démarrage si activé
        if self.config.get("auto_check_updates", True):
            self.updater.check_for_updates()

    def init_ui(self):
        """Initialise l'interface utilisateur principale"""
        # Créer les onglets
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Créer les différents onglets
        self.download_tab = DownloadTab(self)
        self.config_tab = ConfigTab(self)
        self.queue_tab = QueueTab(self)
        self.stats_tab = StatsTab(self)
        
        # Ajouter les onglets
        self.tabs.addTab(self.download_tab, "Téléchargement")
        self.tabs.addTab(self.queue_tab, "File d'attente")
        self.tabs.addTab(self.config_tab, "Configuration")
        self.tabs.addTab(self.stats_tab, "Statistiques")
        
        # Définir une taille par défaut
        self.setGeometry(100, 100, 800, 600)

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
        """Gestionnaire d'événement de fermeture de la fenêtre"""
        try:
            # Arrêter le thread de chargement s'il existe
            if self.loader_thread is not None:
                self.loader_thread.quit()
                self.loader_thread.wait()

            # Arrêter le thread de vérification des mises à jour s'il existe
            if hasattr(self, 'updater') and self.updater._checker_thread:
                self.updater._checker_thread.stop()
                self.updater._checker_thread.wait()

            # Arrêter les téléchargements en cours
            if hasattr(self, 'download_manager'):
                if self.download_manager.current_download:
                    self.download_manager.current_download.stop()
                    self.download_manager.current_download.wait()

            # Sauvegarder la configuration
            save_config(self.config)
            
            # Accepter l'événement de fermeture
            event.accept()
            
        except Exception as e:
            # Logger l'erreur mais permettre la fermeture quand même
            logging.error(f"Erreur lors de la fermeture: {str(e)}")
            event.accept()  # Accepter la fermeture même en cas d'erreur

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

    def on_update_available(self, version):
        """Appelé quand une mise à jour est disponible"""
        self._update_available_shown = True
        reply = QMessageBox.question(
            self,
            "Mise à jour disponible",
            f"Une nouvelle version ({version}) est disponible. Voulez-vous la télécharger et l'installer ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.start_update_download()

    def on_update_progress(self, progress):
        """Met à jour la progression du téléchargement"""
        if self.progress_dialog:
            self.progress_dialog.setValue(progress)

    def on_update_error(self, error):
        """Appelé en cas d'erreur pendant la mise à jour"""
        self._update_error_shown = True
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog = None
        QMessageBox.warning(self, "Erreur de mise à jour", error)

    def on_update_success(self):
        """Appelé quand la mise à jour est terminée avec succès"""
        if self.progress_dialog:
            self.progress_dialog.close()
        QMessageBox.information(
            self,
            "Mise à jour terminée",
            "La mise à jour a été installée avec succès. L'application va redémarrer."
        )

    def check_updates_manually(self):
        """Vérification manuelle des mises à jour"""
        # Réinitialiser les flags d'état
        self._update_error_shown = False
        self._update_available_shown = False
        
        # Créer une boîte de dialogue de progression avec bouton Annuler
        self.progress_dialog = QProgressDialog(
            "Recherche de mises à jour en cours...",
            "Annuler",
            0, 0,  # Min et Max à 0 pour une barre indéterminée
            self
        )
        self.progress_dialog.setWindowTitle("Vérification des mises à jour")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(500)  # Délai minimum avant affichage
        self.progress_dialog.canceled.connect(self.cancel_update_check)
        
        # Connecter les signaux de l'updater
        self.updater.check_finished.connect(self.on_check_finished)
        
        # Démarrer la vérification
        self.updater.check_for_updates()
        
        # Afficher la boîte de dialogue
        self.progress_dialog.exec_()

    def cancel_update_check(self):
        """Annule la vérification des mises à jour"""
        if hasattr(self, 'updater') and self.updater._checker_thread:
            self.updater._checker_thread.stop()
            self.updater._checker_thread.wait()
        self.cleanup_update_check()

    def on_check_finished(self):
        """Appelé quand la vérification est terminée"""
        # Nettoyer les connexions et la boîte de dialogue
        self.cleanup_update_check()
        
        # Si aucune mise à jour n'a été trouvée et aucune erreur n'a été affichée
        if not self._update_error_shown and not self._update_available_shown:
            QMessageBox.information(
                self,
                "Mise à jour",
                "Vous utilisez déjà la dernière version du programme."
            )

    def cleanup_update_check(self):
        """Nettoie les ressources de la vérification des mises à jour"""
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        try:
            # Déconnecter les signaux s'ils sont connectés
            self.updater.check_finished.disconnect(self.on_check_finished)
        except:
            pass  # Ignorer si le signal n'était pas connecté

    def toggle_auto_check(self, checked):
        """Active/désactive la vérification automatique des mises à jour"""
        self.config["auto_check_updates"] = checked
        save_config(self.config)

    def show_update_history(self):
        """Affiche l'historique des mises à jour"""
        self.updater.load_update_history()

    def on_update_history_loaded(self, history):
        """Affiche l'historique des mises à jour dans une boîte de dialogue scrollable"""
        if not history:
            QMessageBox.information(
                self,
                "Historique des mises à jour",
                "Aucun historique de mise à jour disponible."
            )
            return

        # Créer une boîte de dialogue personnalisée
        dialog = QDialog(self)
        dialog.setWindowTitle("Historique des mises à jour")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        # Créer la disposition
        layout = QVBoxLayout()
        
        # Créer un widget de texte riche avec ascenseur
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # Préparer le contenu en HTML
        history_text = "# Historique des mises à jour\n\n"
        for version, changes in history:
            history_text += f"## Version {version}\n"
            for change in changes:
                history_text += f"- {change}\n"
            history_text += "\n"
        
        # Convertir le markdown en HTML
        html_content = markdown2.markdown(history_text)
        text_browser.setHtml(html_content)
        
        # Ajouter le widget de texte à la disposition
        layout.addWidget(text_browser)
        
        # Ajouter un bouton Fermer
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.close)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def start_update_download(self):
        """Démarre le téléchargement de la mise à jour"""
        self.progress_dialog = QProgressDialog(
            "Téléchargement de la mise à jour...",
            "Annuler",
            0, 100,
            self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.canceled.connect(self.cancel_update_download)
        self.progress_dialog.show()
        
        # Lancer le téléchargement
        self.updater.download_and_install_update()

    def cancel_update_download(self):
        """Annule le téléchargement de la mise à jour"""
        # TODO: Implémenter l'annulation du téléchargement
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            delattr(self, 'progress_dialog')