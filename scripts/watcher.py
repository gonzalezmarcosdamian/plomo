"""Watcher daemon - procesa archivos nuevos en Downloads automáticamente.

Run: python scripts/watcher.py
"""
import time
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from plomo import config


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


class DownloadHandler(FileSystemEventHandler):
    SUPPORTED_EXT = {'.mp3', '.flac', '.wav', '.aiff'}

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in self.SUPPORTED_EXT:
            return
        log.info(f"Detected new audio: {path.name}")
        # Wait for file to fully write
        time.sleep(2)
        self.process(path)

    def process(self, path: Path):
        log.info(f"  TODO: import + cue + move")
        # TODO:
        #  1. Read ID3 (mutagen)
        #  2. shutil.move → MUSIC_NEW_FOLDER
        #  3. RekordboxDB context: db.add_content(...)
        #  4. analyze_track + apply_cues_v8
        #  5. Notification (toast Windows?)


def main():
    if not config.DOWNLOADS_FOLDER.exists():
        log.error(f"Downloads folder no existe: {config.DOWNLOADS_FOLDER}")
        return

    log.info(f"👀 Watching {config.DOWNLOADS_FOLDER}")
    observer = Observer()
    observer.schedule(DownloadHandler(), str(config.DOWNLOADS_FOLDER), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
