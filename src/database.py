from option_parser import Options
from pathlib import Path
from tinydb import TinyDB, Query
import hashlib
import logging
import os

log = logging.getLogger(__name__)


class Database(object):
    def __init__(self, options: Options):
        self._db = self.load_database(options.input_dir)

    @staticmethod
    def load_database(database_path):
        # Use MD5 of source_path to establish database name
        db_name = hashlib.md5(str(database_path).encode('utf-8')).hexdigest() + '.json'
        db_dir_env = os.environ.get('AUDIOSYNC_DATABASE_DIR')
        if db_dir_env:
            db_dir = Path(db_dir_env)
        else:
            db_dir = Path(Path(__file__).parent.parent, 'db')

        if not db_dir.exists():
            log.info(f"Directory '{db_dir}' does't exist. Creating directory")
            db_dir.mkdir(parents=True)
        else:
            log.debug(f"Directory '{db_dir}' already exist. Skipping directory creation.")

        db_full_path = Path(db_dir, db_name)
        return TinyDB(db_full_path)

    ''' Take key/value pair and store/update value in database '''
    def update(self, path, hash, mtime, size):
        file = Query()
        data = {'path': str(path), 'hash': hash, 'mtime': mtime, 'size': size}

        if self._db.count(file.path == str(path)) >= 1:
            self._db.update(data, file.path == str(path))
        else:
            self._db.insert(data)

    ''' Lookup key in database, return value '''
    def get_property(self, path, prop):
        file_property = ''
        file = Query()
        if self._db.count(file.path == str(path)) >= 1:
            file_property = self._db.search(file.path == str(path))[0][prop]
        return file_property
