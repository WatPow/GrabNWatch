from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QLabel, QGroupBox
)

class StatsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """Initialiser l'interface de l'onglet des statistiques"""
        layout = QVBoxLayout()
        
        # Statistiques globales
        stats_group = QGroupBox("Statistiques globales")
        stats_layout = QGridLayout()
        
        self.total_downloads_label = QLabel("Téléchargements totaux: 0")
        self.total_size_label = QLabel("Taille totale: 0 MB")
        self.average_speed_label = QLabel("Vitesse moyenne: 0 MB/s")
        
        stats_layout.addWidget(self.total_downloads_label, 0, 0)
        stats_layout.addWidget(self.total_size_label, 1, 0)
        stats_layout.addWidget(self.average_speed_label, 2, 0)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        self.setLayout(layout)

    def update_stats_display(self):
        """Mettre à jour l'affichage des statistiques"""
        stats = self.parent.download_manager.stats
        self.total_downloads_label.setText(f"Téléchargements totaux: {stats['total_downloads']}")
        self.total_size_label.setText(f"Taille totale: {stats['total_size'] / (1024*1024):.2f} MB")
        self.average_speed_label.setText(f"Vitesse moyenne: {stats['average_speed'] / (1024*1024):.2f} MB/s") 