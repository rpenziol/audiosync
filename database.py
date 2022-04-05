from pathlib import Path
from tinydb import TinyDB, Query
import hashlib
import logging

log = logging.getLogger(__name__)


class Database(object):
    def __init__(self, database_path):
        self._db = self.load_database(database_path)

    @staticmethod
    def load_database(database_path):
        # Use MD5 of source_path to establish database name
        db_name = hashlib.md5(str(database_path).encode('utf-8')).hexdigest() + '.json'
        current_path = Path(__file__).parent
        db_dir = Path(current_path, 'db')

        if not db_dir.exists():
            log.info("Directory '{0}' does't exist. Creating directory".format(db_dir))
            db_dir.mkdir(parents=True)
        else:
            log.debug("Directory '{0}' already exist. Skipping directory creation.".format(db_dir))

        db_full_path = Path(db_dir, db_name)
        return TinyDB(db_full_path)

    ''' Take key/value pair and store/update value in database '''
    def update(self, path, hash, mtime, size):
        file = Query()
        if self._db.count(file.path == path) >= 1:
            self._db.update({'path': str(path), 'hash': hash, 'mtime': mtime, 'size': size}, file.path == path)
        else:
            self._db.insert({'path': str(path), 'hash': hash, 'mtime': mtime, 'size': size})

    ''' Lookup key in database, return value '''
    def get_property(self, path, prop):
        file_property = ''
        file = Query()
        if self._db.count(file.path == path) >= 1:
            file_property = self._db.search(file.path == path)[0][prop]
        return file_property
