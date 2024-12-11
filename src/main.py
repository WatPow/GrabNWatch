import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Ajouter le chemin du script au PYTHONPATH
if getattr(sys, 'frozen', False):
    # Si on est dans l'exécutable
    application_path = sys._MEIPASS
else:
    # Si on est en développement
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(application_path))

from src.ui.main_window import MainWindow

def setup_logging():
    """Configuration du système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Point d'entrée principal de l'application"""
    setup_logging()
    
    app = QApplication(sys.argv)
    
    # Définir l'icône au niveau de l'application
    try:
        if getattr(sys, 'frozen', False):
            # Si on est dans l'exécutable
            icon_path = os.path.join(sys._MEIPASS, 'src', 'assets', 'icon.ico')
        else:
            # Si on est en développement
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        logging.warning(f"Impossible de charger l'icône globale: {e}")
    
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 