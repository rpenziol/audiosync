from pathlib import Path
import converter
import database
import logging
import os
import shutil

log = logging.getLogger(__name__)


class Scanner(object):
    def __init__(self, source_dir, dest_dir, options):
        self._converter = converter.Converter(database.Database(source_dir), options)
        self._options = options
        self.tree_scanner(source_dir, dest_dir)

    ''' Recursively scans input directory structure and compares to the destination folder tree.
    Creates missing directories in destination folder, calls dir_scanner to queue conversions, then processes queue '''
    def tree_scanner(self, source_dir: Path, dest_dir: Path):

        def _remove_orphans(source_dir: Path, dest_dir: Path):
            for path in dest_dir.rglob('*'):
                rel_path = path.relative_to(dest_dir)
                source_path = Path(source_dir, rel_path)

                if path.is_dir() and not source_path.exists():
                    log.debug(f'"{path}" is an orphaned directory. Removing.')
                    shutil.rmtree(path)

                if path.is_file():
                    source_file_found = False
                    source_file_dir = source_path.parent
                    dest_filename_without_extension = rel_path.stem

                    for source_file in source_file_dir.glob(f'{dest_filename_without_extension}*'):
                        source_file_extension = source_file.suffix.lstrip('.').lower()

                        if source_file_extension in self._options['extensions_to_convert']:
                            log.debug(f'Source file found "{source_file}".')
                            source_file_found = True
                            break

                    if not source_file_found:
                        log.debug(f'"{path}" is an orphaned file. Removing.')
                        path.unlink()

        def _sync_to_dest(source_dir: Path, dest_dir: Path):
            for path in source_dir.rglob('*'):
                rel_path = path.relative_to(source_dir)
                output_path = Path(dest_dir, rel_path)

                if path.is_dir() and not output_path.exists():
                    log.info('Directory "{0}" does not exist. Creating directory'.format(output_path))
                    output_path.mkdir(parents=True)
                elif path.is_dir():
                    log.debug('Directory "{0}" already exist. Skipping directory creation.'.format(output_path))
                else:
                    self.queue_file(source_dir, dest_dir, path)

        _remove_orphans(source_dir, dest_dir)
        _sync_to_dest(source_dir, dest_dir)
        # Make the magic happen
        self._converter.process_queue()


    ''' Add file to process queue if it meets conversion criteria '''
    def queue_file(self, source_dir, dest_dir, source_file):

        file_extension = source_file.suffix.lstrip('.').lower()
        if file_extension in self._options['extensions_to_ignore'] or file_extension not in self._options['extensions_to_convert']:
            return
        
        rel_dir = source_file.relative_to(source_dir).parent
        filename_without_extension = source_file.stem
        destination_file = Path(dest_dir, rel_dir, f"{filename_without_extension}.{self._options['format']}")
        self._converter.queue_job(source_file, destination_file)

    ''' Wrapper function to call converter's process queue function'''
    def process_queue(self):
        self._converter.process_queue()
