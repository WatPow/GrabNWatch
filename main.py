import sys
import requests
import re
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QProgressDialog,
    QTabWidget,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from unidecode import unidecode
import json
import logging

# Configure logging to help in debugging by providing timestamps and log levels
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_config(config):
    """
    Save configuration to a JSON file.
    
    Parameters:
        config (dict): Configuration dictionary to be saved.
        
    Raises:
        Exception: If saving the configuration fails.
    """
    try:
        app_name = "GrabNWatch"
        appdata_path = os.getenv("APPDATA")
        if not appdata_path:
            raise EnvironmentError("APPDATA environment variable not found.")
        app_config_path = os.path.join(appdata_path, app_name)
        os.makedirs(app_config_path, exist_ok=True)
        config_file_path = os.path.join(app_config_path, "config.json")
        with open(config_file_path, "w") as f:
            json.dump(config, f)
        logging.info("Configuration saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save configuration: {e}")
        raise

def load_config():
    """
    Load configuration from a JSON file.
    
    Returns:
        dict: The loaded configuration dictionary.
        
    Raises:
        Exception: If loading the configuration fails.
    """
    try:
        app_name = "GrabNWatch"
        appdata_path = os.getenv("APPDATA")
        if not appdata_path:
            raise EnvironmentError("APPDATA environment variable not found.")
        app_config_path = os.path.join(appdata_path, app_name)
        config_file_path = os.path.join(app_config_path, "config.json")
        with open(config_file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        default_config = {"m3u_url": ""}
        save_config(default_config)
        return default_config
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise

class DownloadThread(QThread):
    """
    A thread to handle the download of video on demand (VOD) files.
    
    Attributes:
        progress (pyqtSignal): Signal to update download progress.
        finished (pyqtSignal): Signal to indicate download completion.
        error (pyqtSignal): Signal to indicate an error with the download.
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, name, vod_url):
        """
        Initialize the download thread with the specified VOD name and URL.
        
        Parameters:
            name (str): The name of the VOD.
            vod_url (str): The URL from which to download the VOD.
        """
        super().__init__()
        self.name = name
        self.vod_url = vod_url
        self.is_running = True

    def run(self):
        """
        Run the download process.
        """
        try:
            download_dir = "downloads"
            os.makedirs(download_dir, exist_ok=True)
            safe_name = re.sub(r"[^\w\s-]", "", unidecode(self.name)).replace(" ", "_")
            file_name = os.path.join(download_dir, f"{safe_name}.mp4")
            response = requests.get(self.vod_url, stream=True, timeout=10)
            total_size_in_bytes = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(file_name, "wb") as file:
                for data in response.iter_content(1024):
                    if not self.is_running:
                        break
                    file.write(data)
                    downloaded += len(data)
                    percent_complete = int((downloaded / total_size_in_bytes) * 100)
                    self.progress.emit(percent_complete)
            if self.is_running:
                self.finished.emit()
            else:
                os.remove(file_name)
                self.error.emit("Download canceled.")
        except Exception as e:
            self.error.emit(str(e))
            logging.error(f"Download failed: {e}")

    def stop(self):
        """
        Stop the download process.
        """
        self.is_running = False


class App(QMainWindow):
    """
    Main application window for the GrabNWatch application.
    """
    def __init__(self):
        """
        Initialize the application window and load the configuration.
        """
        super().__init__()
        self.config = load_config()  # Load configuration
        self.m3u_url = self.config.get("m3u_url", "")
        self.entries = []
        self.setWindowTitle("GrabNWatch")
        self.setWindowIcon(QIcon(".\icon.ico"))
        self.setGeometry(100, 100, 800, 600)
        self.tabs = QTabWidget(self)
        self.download_tab = QWidget()
        self.config_tab = QWidget()
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.config_tab, "Configuration")
        self.setCentralWidget(self.tabs)

        self.initUI()
        self.initConfigUI()
        self.load_m3u_url_into_ui()
        self.try_load_m3u_content()
        self.show_startup_message()

    def load_m3u_url_into_ui(self):
        """
        Update the QLineEdit with the loaded M3U URL.
        """
        self.m3u_box.setText(self.config.get("m3u_url", ""))

    def save_m3u_url(self):
        """
        Save the M3U URL from the QLineEdit to the configuration.
        """
        self.m3u_url = self.m3u_box.text()
        self.config["m3u_url"] = self.m3u_url
        save_config(self.config)
        QMessageBox.information(self, "URL Saved", "M3U URL has been updated.")
        self.load_m3u_content()

    def show_startup_message(self):
        """
        Show a startup message about IPTV stream limitations.
        """
        QMessageBox.information(
            self,
            "Attention",
            "Veuillez couper les flux IPTV sur les autres appareils que vous utilisez, sinon le téléchargement ne fonctionnera pas, à moins que vous ne disposiez de plusieurs lignes.",
        )

    def initUI(self):
        """
        Initialize the main UI components for the download tab.
        """
        layout = QVBoxLayout()
        self.search_label = QLabel("Entrez un terme de recherche pour les VODs:")
        self.search_box = QLineEdit()
        self.search_button = QPushButton("Rechercher")
        self.list_widget = QListWidget()
        self.download_button = QPushButton("Télécharger la VOD sélectionnée")
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_box)
        layout.addWidget(self.search_button)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.download_button)
        self.download_tab.setLayout(layout)
        self.search_button.clicked.connect(self.search_vods)
        self.download_button.clicked.connect(self.download_selected_vod)

    def initConfigUI(self):
        """
        Initialize the configuration UI components.
        """
        layout = QVBoxLayout()
        m3u_layout = QHBoxLayout()
        self.m3u_label = QLabel("M3U URL:")
        self.m3u_box = QLineEdit(self.m3u_url)
        self.m3u_button = QPushButton("Sauvegarder URL")
        m3u_layout.addWidget(self.m3u_label)
        m3u_layout.addWidget(self.m3u_box)
        m3u_layout.addWidget(self.m3u_button)
        layout.addLayout(m3u_layout)
        self.config_tab.setLayout(layout)
        self.m3u_button.clicked.connect(self.save_m3u_url)

    def try_load_m3u_content(self):
        """
        Attempt to load M3U content if the URL starts with "http".
        """
        if self.m3u_url.startswith("http"):
            self.load_m3u_content()

    def load_m3u_content(self):
        """
        Load M3U content from the configured URL.
        """
        if not self.m3u_url.startswith("http"):
            QMessageBox.warning(
                self, "Configuration requise", "Veuillez configurer une URL M3U valide."
            )
            return

        try:
            response = requests.get(self.m3u_url, timeout=10)
            response.raise_for_status()
            raw_entries = re.findall(
                r'#EXTINF:-1.*?tvg-name="([^"]+)"(?!.*?tvg-id=").*?\n(http[^\s]+)',
                response.text,
            )
            self.entries = list(dict(raw_entries).items())
        except requests.ConnectionError:
            QMessageBox.critical(
                self,
                "Network Error",
                "Erreur de connexion. Vérifiez votre connexion Internet.",
            )
        except requests.Timeout:
            QMessageBox.critical(
                self,
                "Network Error",
                "La requête a expiré. Vérifiez votre connexion Internet et réessayez.",
            )
        except requests.HTTPError as e:
            QMessageBox.critical(
                self, "Network Error", f"Erreur HTTP : {e.response.status_code}"
            )
        except requests.RequestException as e:
            QMessageBox.critical(self, "Network Error", str(e))

    def search_vods(self):
        """
        Search for VODs matching the entered search terms.
        """
        if not self.entries:
            QMessageBox.warning(
                self, "Error", "No data loaded. Please load or refresh the M3U content."
            )
            return

        search_query = self.search_box.text()
        search_tokens = unidecode(search_query.lower()).split()
        self.list_widget.clear()
        filtered = [
            (name, url)
            for name, url in self.entries
            if all(token in unidecode(name.lower()) for token in search_tokens)
        ]

        if filtered:
            self.list_widget.addItems([name for name, _ in filtered])
        else:
            QMessageBox.information(
                self, "No Matches", "No VODs matched your search criteria."
            )

    def download_selected_vod(self):
        """
        Start the download of the selected VOD.
        """
        selected_item = self.list_widget.currentItem()
        if selected_item:
            name = selected_item.text()
            url = next((url for name_, url in self.entries if name == name_), None)
            if url:
                self.start_download(name, url)

    def start_download(self, name, vod_url):
        """
        Setup and start the download thread.
        """
        self.search_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.m3u_button.setEnabled(False)
        self.download_thread = DownloadThread(name, vod_url)
        self.progress_dialog = QProgressDialog("Downloading...", "Cancel", 0, 100, self)
        self.progress_dialog.setAutoClose(True)
        self.download_thread.progress.connect(self.progress_dialog.setValue)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.progress_dialog.canceled.connect(self.cancel_download)
        self.download_thread.start()

    def cancel_download(self):
        """
        Cancel the ongoing download.
        """
        if self.download_thread.isRunning():
            self.download_thread.stop()
        self.progress_dialog.close()

    def download_finished(self):
        """
        Handle the completion of a download.
        """
        self.reset_buttons()
        QMessageBox.information(
            self, "Download Complete", "The VOD has been downloaded."
        )

    def download_error(self, message):
        """
        Handle errors that occurred during the download.
        """
        self.reset_buttons()
        QMessageBox.critical(self, "Download Error", message)

    def reset_buttons(self):
        """
        Re-enable buttons after a download is completed or canceled.
        """
        self.search_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.m3u_button.setEnabled(True)


def main():
    """
    Main function to start the application.
    """
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

