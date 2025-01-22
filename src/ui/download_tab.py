from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QListWidget, QPushButton,
    QMessageBox
)
from PyQt5.QtCore import Qt

class DownloadTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """Initialiser l'interface de l'onglet de téléchargement"""
        layout = QVBoxLayout()
        
        # Zone de recherche
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Rechercher...")
        search_layout.addWidget(self.search_box)
        
        # Filtres et tri
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Tous")
        self.filter_combo.setMinimumWidth(200)  # Définir une largeur minimale
        self.filter_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  # Ajuster à la taille du contenu
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Nom (A-Z)", "Nom (Z-A)"])
        search_layout.addWidget(self.filter_combo)
        search_layout.addWidget(self.sort_combo)
        layout.addLayout(search_layout)
        
        # Liste des VODs
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Informations sur le fichier
        self.file_info_label = QLabel()
        layout.addWidget(self.file_info_label)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Télécharger")
        button_layout.addWidget(self.download_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connexions
        self.search_box.textChanged.connect(self.search_vods)
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        self.sort_combo.currentTextChanged.connect(self.apply_sort)
        self.download_button.clicked.connect(self.download_selected_vod)
        self.list_widget.currentItemChanged.connect(self.update_file_info)

    def search_vods(self):
        """Rechercher dans les VODs"""
        if not self.parent.entries:
            QMessageBox.warning(
                self, "Erreur", "Aucune donnée chargée. Veuillez charger ou actualiser le contenu M3U."
            )
            return

        search_query = self.search_box.text().lower()
        selected_category = self.filter_combo.currentText()
        
        self.list_widget.clear()
        filtered = []

        for name, url in self.parent.entries:
            info = self.parent.vod_info[name]
            
            # Vérifier la catégorie
            if selected_category != "Tous" and info['group_title'] != selected_category:
                continue
                
            # Vérifier le terme de recherche
            if search_query and search_query not in name.lower():
                continue
                
            filtered.append(name)

        # Appliquer le tri
        sort_method = self.sort_combo.currentText()
        if sort_method == "Nom (A-Z)":
            filtered.sort()
        elif sort_method == "Nom (Z-A)":
            filtered.sort(reverse=True)

        self.list_widget.addItems(filtered)

    def apply_filter(self, filter_text):
        """Appliquer le filtre de catégorie"""
        self.search_vods()

    def apply_sort(self, sort_method):
        """Appliquer le tri"""
        items = []
        for i in range(self.list_widget.count()):
            items.append(self.list_widget.item(i).text())
        
        if sort_method == "Nom (A-Z)":
            items.sort()
        elif sort_method == "Nom (Z-A)":
            items.sort(reverse=True)
        
        self.list_widget.clear()
        self.list_widget.addItems(items)

    def update_filter_categories(self):
        """Mettre à jour la liste des catégories dans le filtre"""
        categories = set()
        for info in self.parent.vod_info.values():
            if info['group_title']:
                categories.add(info['group_title'])
        
        self.filter_combo.clear()
        self.filter_combo.addItem("Tous")
        self.filter_combo.addItems(sorted(categories))

    def update_file_info(self, current, previous):
        """Mettre à jour les informations du fichier sélectionné"""
        if current:
            name = current.text()
            info = self.parent.vod_info.get(name, {})
            
            details = []
            if info.get('group_title'):
                details.append(f"Catégorie: {info['group_title']}")
            if info.get('xui_id'):
                details.append(f"ID: {info['xui_id']}")
            
            self.file_info_label.setText("\n".join(details))

    def download_selected_vod(self):
        """Télécharger le VOD sélectionné"""
        selected_item = self.list_widget.currentItem()
        if selected_item:
            name = selected_item.text()
            url = next((url for name_, url in self.parent.entries if name == name_), None)
            if url:
                bandwidth_limit = self.parent.config.get("bandwidth_limit", 0)
                self.parent.download_manager.add_to_queue(name, url, bandwidth_limit)
                QMessageBox.information(
                    self,
                    "Ajouté à la file d'attente",
                    f"{name} a été ajouté à la file d'attente de téléchargement."
                ) 