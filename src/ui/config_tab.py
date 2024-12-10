from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QCheckBox, QGroupBox, QMessageBox
)
from src.core.config import save_config

class ConfigTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """Initialiser l'interface de l'onglet de configuration"""
        layout = QVBoxLayout()
        
        # Configuration M3U
        m3u_group = QGroupBox("Configuration M3U")
        m3u_layout = QHBoxLayout()
        self.m3u_label = QLabel("M3U URL:")
        self.m3u_box = QLineEdit(self.parent.m3u_url)
        self.m3u_button = QPushButton("Sauvegarder URL")
        m3u_layout.addWidget(self.m3u_label)
        m3u_layout.addWidget(self.m3u_box)
        m3u_layout.addWidget(self.m3u_button)
        m3u_group.setLayout(m3u_layout)
        
        # Configuration des téléchargements
        download_group = QGroupBox("Configuration des téléchargements")
        download_layout = QGridLayout()
        
        self.bandwidth_label = QLabel("Limite de bande passante (KB/s):")
        self.bandwidth_spin = QSpinBox()
        self.bandwidth_spin.setRange(0, 100000)
        self.bandwidth_spin.setValue(self.parent.config.get("bandwidth_limit", 0))
        self.bandwidth_spin.setSpecialValueText("Illimité")
        
        download_layout.addWidget(self.bandwidth_label, 0, 0)
        download_layout.addWidget(self.bandwidth_spin, 0, 1)
        
        download_group.setLayout(download_layout)
        
        # Configuration du thème
        theme_group = QGroupBox("Apparence")
        theme_layout = QVBoxLayout()
        self.theme_check = QCheckBox("Mode sombre")
        self.theme_check.setChecked(self.parent.dark_mode)
        theme_layout.addWidget(self.theme_check)
        theme_group.setLayout(theme_layout)
        
        # Ajout des groupes au layout principal
        layout.addWidget(m3u_group)
        layout.addWidget(download_group)
        layout.addWidget(theme_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connexions
        self.m3u_button.clicked.connect(self.save_m3u_url)
        self.bandwidth_spin.valueChanged.connect(self.save_config)
        self.theme_check.stateChanged.connect(self.toggle_theme)

    def save_m3u_url(self):
        """Sauvegarder l'URL M3U"""
        self.parent.m3u_url = self.m3u_box.text()
        self.parent.config["m3u_url"] = self.parent.m3u_url
        self.save_config()
        QMessageBox.information(self, "URL Sauvegardée", "L'URL M3U a été mise à jour.")
        self.parent.try_load_m3u_content()

    def save_config(self):
        """Sauvegarder la configuration"""
        self.parent.config["bandwidth_limit"] = self.bandwidth_spin.value()
        self.parent.config["dark_mode"] = self.parent.dark_mode
        save_config(self.parent.config)

    def toggle_theme(self, state):
        """Changer le thème de l'application"""
        self.parent.dark_mode = bool(state)
        self.parent.config["dark_mode"] = self.parent.dark_mode
        self.save_config()
        self.parent.apply_theme()