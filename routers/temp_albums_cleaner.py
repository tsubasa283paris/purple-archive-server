import os
import multiprocessing
import time

from routers.albums import get_gif_path
from sql_interface import crud
from sql_interface.database import get_db


TEMP_ALBUMS_EXPIRATION_SECS = 60 * 60 # 1 hour
TEMP_ALBUMS_CLEAN_INTERVAL_SECS = 30 * 60 # 30 minutes


class TempAlbumsCleaner:
    proc: multiprocessing.Process

    def __init__(self):
        self.proc = multiprocessing.Process(target=self.run, args=())
        self.proc.start()

    def cleanup_temp_albums(self):
        print("PERIODIC TEMP ALBUM CLEANING START")

        db = next(get_db())
        temp_albums = crud.get_expired_temp_albums(db,
                                                TEMP_ALBUMS_EXPIRATION_SECS)
        
        for temp_album in temp_albums:
            # remove actual file
            try:
                os.remove(get_gif_path(temp_album.uuid))
            except FileNotFoundError:
                print("\tActual file not found:", temp_album.uuid)

            # soft-delete from database
            crud.soft_delete_temp_album(db, temp_album.uuid)
        
        print(f"Removed {len(temp_albums)} temp_albums:",
            ",".join(ta.uuid for ta in temp_albums))
    
    def run(self):
        while True:
            time.sleep(TEMP_ALBUMS_CLEAN_INTERVAL_SECS)
            self.cleanup_temp_albums()
    
    def stop(self):
        self.proc.terminate()
