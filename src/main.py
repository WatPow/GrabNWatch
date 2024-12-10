import sys
import os
import logging
from PyQt5.QtWidgets import QApplication

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
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 