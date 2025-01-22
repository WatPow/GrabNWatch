from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QGroupBox,
    QMessageBox
)
from PyQt5.QtCore import Qt
import time

class QueueTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        # Désactiver les boutons par défaut
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

    def init_ui(self):
        """Initialiser l'interface de l'onglet de la file d'attente"""
        layout = QVBoxLayout()
        
        # Liste des téléchargements actifs
        active_group = QGroupBox("Téléchargement en cours")
        self.active_list = QListWidget()
        active_layout = QVBoxLayout()
        active_layout.addWidget(self.active_list)
        active_group.setLayout(active_layout)
        
        # Liste de la file d'attente
        queue_group = QGroupBox("File d'attente")
        self.queue_list = QListWidget()
        queue_layout = QVBoxLayout()
        queue_layout.addWidget(self.queue_list)
        queue_group.setLayout(queue_layout)
        
        # Historique des téléchargements
        history_group = QGroupBox("Historique")
        self.history_list = QListWidget()
        history_layout = QVBoxLayout()
        history_layout.addWidget(self.history_list)
        history_group.setLayout(history_layout)
        
        # Boutons de contrôle
        control_layout = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Reprendre")
        self.cancel_button = QPushButton("Annuler")
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.resume_button)
        control_layout.addWidget(self.cancel_button)
        
        # Ajout des widgets au layout principal
        layout.addWidget(active_group)
        layout.addWidget(queue_group)
        layout.addWidget(history_group)
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
        
        # Connexion des boutons
        self.cancel_button.clicked.connect(self.cancel_selected_download)
        self.pause_button.clicked.connect(self.pause_selected_download)
        self.resume_button.clicked.connect(self.resume_selected_download)
        
        # Ajouter la connexion pour la sélection d'item
        self.active_list.itemSelectionChanged.connect(self.update_buttons_state)
        
        # Connexion des signaux du gestionnaire de téléchargements
        self.parent.download_manager.download_progress.connect(self.update_download_progress)
        self.parent.download_manager.download_finished.connect(self.on_download_finished)
        self.parent.download_manager.download_error.connect(self.on_download_error)
        self.parent.download_manager.queue_updated.connect(self.update_queue_display)
        self.parent.download_manager.download_finished.connect(
            lambda: self.parent.stats_tab.update_stats_display()
        )

    def update_buttons_state(self):
        """Mettre à jour l'état des boutons en fonction de la sélection et de l'état du téléchargement"""
        selected_item = self.active_list.currentItem()
        if selected_item:
            self.cancel_button.setEnabled(True)
            full_text = selected_item.text()
            is_paused = "En pause" in full_text
            self.pause_button.setEnabled(not is_paused)
            self.resume_button.setEnabled(is_paused)
        else:
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

    def format_size(self, size_in_bytes):
        """Formater la taille en format lisible"""
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} To"

    def update_download_progress(self, name, progress, speed):
        """Mettre à jour la progression du téléchargement"""
        items = self.active_list.findItems(f"{name}", Qt.MatchStartsWith)
        if items and self.parent.download_manager.current_download:
            # Formater la vitesse avec 2 décimales
            speed_text = f"{speed:.2f} Ko/s"
            # Formater la taille totale
            total_size = self.format_size(self.parent.download_manager.current_download.total_size)
            # Garder le même format que précédemment pour la compatibilité
            status = "En pause" if hasattr(self.parent.download_manager.current_download, 'paused') and self.parent.download_manager.current_download.paused else f"{progress}% - {speed_text} - {total_size}"
            items[0].setText(f"{name} - {status}")

    def update_queue_display(self):
        """Mettre à jour l'affichage de la file d'attente"""
        # Mise à jour du téléchargement actif
        self.active_list.clear()
        if self.parent.download_manager.current_download:
            name = self.parent.download_manager.current_download.name
            total_size = self.format_size(self.parent.download_manager.current_download.total_size)
            status = f"En pause - {total_size}" if hasattr(self.parent.download_manager.current_download, 'paused') and self.parent.download_manager.current_download.paused else f"En cours - {total_size}"
            self.active_list.addItem(f"{name} - {status}")
        
        # Mise à jour de la file d'attente
        self.queue_list.clear()
        for name, _, _ in self.parent.download_manager.download_queue:
            self.queue_list.addItem(f"{name} - En attente")
        
        # Mise à jour de l'historique
        self.history_list.clear()
        for name, status, timestamp in sorted(
            self.parent.download_manager.download_history,
            key=lambda x: x[2],
            reverse=True
        ):
            # Si le statut contient déjà la taille (pour les téléchargements terminés), on le garde tel quel
            if " - " in status and any(unit in status for unit in ['o', 'Ko', 'Mo', 'Go', 'To']):
                display_status = status
            else:
                display_status = status
            self.history_list.addItem(
                f"{name} - {display_status} - {time.strftime('%H:%M:%S', time.localtime(timestamp))}"
            )
        
        # Mettre à jour l'état des boutons
        self.update_buttons_state()

    def on_download_finished(self, name):
        """Gérer la fin d'un téléchargement"""
        # Pas de boîte de dialogue, juste mettre à jour l'interface
        self.update_queue_display()

    def on_download_error(self, name, error):
        """Gérer une erreur de téléchargement"""
        # Pour les erreurs, on garde la boîte de dialogue car c'est important
        QMessageBox.warning(
            self,
            "Erreur de téléchargement",
            f"Erreur lors du téléchargement de {name}: {error}"
        )
        self.update_queue_display()

    def cancel_selected_download(self):
        """Annuler le téléchargement sélectionné"""
        selected_item = self.active_list.currentItem()
        if selected_item:
            # Récupérer juste le nom (première partie avant le premier " - ")
            full_text = selected_item.text()
            name = full_text.split(" - ")[0]
            self.parent.download_manager.cancel_download(name)

    def pause_selected_download(self):
        """Mettre en pause le téléchargement sélectionné"""
        selected_item = self.active_list.currentItem()
        if selected_item:
            # Récupérer juste le nom (première partie avant le premier " - ")
            full_text = selected_item.text()
            name = full_text.split(" - ")[0]
            self.parent.download_manager.pause_download(name)

    def resume_selected_download(self):
        """Reprendre le téléchargement sélectionné"""
        selected_item = self.active_list.currentItem()
        if selected_item:
            # Récupérer juste le nom (première partie avant le premier " - ")
            full_text = selected_item.text()
            name = full_text.split(" - ")[0]
            self.parent.download_manager.resume_download(name) 