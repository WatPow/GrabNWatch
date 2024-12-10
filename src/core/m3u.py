import re
import requests
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict
from PyQt5.QtCore import QThread, pyqtSignal

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class M3UEntry:
    name: str
    url: str
    xui_id: str = None
    tvg_name: str = None
    tvg_logo: str = None
    group_title: str = None

class M3ULoaderThread(QThread):
    finished = pyqtSignal(tuple)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url, parser):
        super().__init__()
        self.url = url
        self.parser = parser
        self.should_stop = False
        self._is_running = False

    def stop(self):
        logger.debug("Arrêt du chargement demandé")
        self.should_stop = True
        if self._is_running:
            self.wait()

    def run(self):
        try:
            self._is_running = True
            logger.debug(f"Début du chargement M3U depuis {self.url}")
            self.progress.emit("Connexion au serveur...")
            
            if self.should_stop:
                logger.debug("Chargement annulé avant la connexion")
                return
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            try:
                response = session.get(self.url, timeout=30, verify=False)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Erreur lors de la requête HTTP: {str(e)}")
                raise
            
            if self.should_stop:
                logger.debug("Chargement annulé après la connexion")
                return
            
            logger.debug("Connexion établie, début du téléchargement")
            self.progress.emit("Téléchargement du contenu...")
            
            content = response.text
            
            if self.should_stop:
                logger.debug("Chargement annulé après le téléchargement")
                return
            
            if not content.strip():
                raise ValueError("Le contenu M3U est vide")

            if "#EXTINF" not in content:
                raise ValueError("Le fichier ne semble pas être un fichier M3U valide")

            logger.debug("Début de l'analyse du contenu")
            self.progress.emit("Analyse du contenu...")
            
            if self.should_stop:
                logger.debug("Chargement annulé avant l'analyse")
                return
            
            result = self.parser.parse_content(content)
            
            if not result[0]:
                raise ValueError("Aucune entrée VOD n'a été trouvée dans le fichier M3U")

            if self.should_stop:
                logger.debug("Chargement annulé après l'analyse")
                return

            logger.debug(f"Analyse terminée, {len(result[0])} entrées trouvées")
            self.finished.emit(result)

        except requests.ConnectionError as e:
            if not self.should_stop:
                logger.error(f"Erreur de connexion: {str(e)}")
                self.error.emit("Erreur de connexion au serveur. Vérifiez votre connexion internet et l'URL.")
        except requests.Timeout as e:
            if not self.should_stop:
                logger.error(f"Timeout: {str(e)}")
                self.error.emit("Le serveur met trop de temps à répondre. Réessayez plus tard.")
        except requests.HTTPError as e:
            if not self.should_stop:
                logger.error(f"Erreur HTTP {e.response.status_code}: {str(e)}")
                if e.response.status_code == 404:
                    self.error.emit("L'URL du fichier M3U n'est pas valide (404 Not Found)")
                elif e.response.status_code == 403:
                    self.error.emit("Accès refusé au fichier M3U (403 Forbidden)")
                else:
                    self.error.emit(f"Erreur HTTP {e.response.status_code} lors du chargement du M3U")
        except ValueError as e:
            if not self.should_stop:
                logger.error(f"Erreur de validation: {str(e)}")
                self.error.emit(str(e))
        except Exception as e:
            if not self.should_stop:
                logger.error(f"Erreur inattendue: {str(e)}", exc_info=True)
                self.error.emit(f"Erreur inattendue lors du chargement du M3U: {str(e)}")
        finally:
            self._is_running = False

class M3UParser:
    def __init__(self):
        self.pattern = r'#EXTINF:-1\s+(?:.*?xui-id="([^"]*)")?\s*(?:tvg-name="([^"]*)")?\s*(?:tvg-logo="([^"]*)")?\s*(?:group-title="([^"]*)")?,([^\n]*)\n(http[^\n]+)'

    def parse_url(self, url: str) -> M3ULoaderThread:
        return M3ULoaderThread(url, self)

    def parse_content(self, content: str) -> Tuple[List[Tuple[str, str]], Dict[str, Dict]]:
        entries = []
        vod_info = {}
        seen_entries = set()

        try:
            for match in re.finditer(self.pattern, content, re.MULTILINE):
                try:
                    xui_id, tvg_name, tvg_logo, group_title, title, url = match.groups()
                    name = tvg_name or title.strip()
                    
                    entry_key = (name, url)
                    if entry_key in seen_entries:
                        continue
                    seen_entries.add(entry_key)
                    
                    vod_info[name] = {
                        'xui_id': xui_id,
                        'tvg_logo': tvg_logo,
                        'group_title': group_title,
                        'url': url
                    }
                    
                    entries.append((name, url))
                except Exception as e:
                    logger.warning(f"Erreur lors du parsing d'une entrée: {str(e)}")
                    continue

            logger.debug(f"Parsing terminé: {len(entries)} entrées valides trouvées")
            return entries, vod_info
        except Exception as e:
            logger.error(f"Erreur lors du parsing du contenu: {str(e)}", exc_info=True)
            raise ValueError(f"Erreur lors du parsing du contenu M3U: {str(e)}")

    @staticmethod
    def get_categories(vod_info: Dict[str, Dict]) -> List[str]:
        categories = set()
        for info in vod_info.values():
            if info['group_title']:
                categories.add(info['group_title'])
        return sorted(list(categories)) 