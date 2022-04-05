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
    def tree_scanner(self, source_dir, dest_dir):
        for root, dirs, _ in os.walk(source_dir, topdown=True):
            for directory in dirs:
                rel_root = root.replace(str(source_dir), '').lstrip('/')
                rel_path = Path(rel_root, directory)
                input_path = Path(source_dir, rel_path)
                output_path = Path(dest_dir, rel_path)

                if not output_path.exists():
                    log.info('Directory "{0}" does not exist. Creating directory'.format(output_path))
                    output_path.mkdir(parents=True)
                else:
                    log.debug('Directory "{0}" already exist. Skipping directory creation.'.format(output_path))

                self.dir_scanner(input_path, output_path)
        # Make the magic happen
        self._converter.process_queue()

    ''' Compares files between input and output paths.
    Depending on file type, copy or convert file from input_path to output_path '''
    def dir_scanner(self, input_path, output_path):
            # Remove orphaned files and folder trees from output_path
            self.remove_orphan_dirs(input_path, output_path)
            self.remove_orphan_files(input_path, output_path)

            for item in input_path.iterdir():
                self.queue_file(input_path, output_path, item)

    ''' Remove folder trees from output_path if folder isn't in input_path'''
    @staticmethod
    def remove_orphan_dirs(input_path, output_path):
        for item in output_path.iterdir():
            if Path(output_path, item).is_dir() and not Path(input_path, item).exists():
                log.debug('"{0}" is an orphaned directory. Removing from "{1}".'.format(item, output_path))
                shutil.rmtree(Path(output_path, item))

    ''' Remove files from output_path if file isn't in input_path'''
    @staticmethod
    def remove_orphan_files(input_path, output_path):
        input_files = []

        # Collect list of file names from input_path
        for item in input_path.iterdir():
            if Path(input_path, item).is_file():
                base_name = Path(item).stem
                input_files.append(base_name)

        # Remove orphaned files from output_path
        for item in output_path.iterdir():
            if Path(output_path, item).is_file():
                base_name = Path(item).stem
                if base_name not in input_files:
                    log.debug('"{0}" is an orphaned file. Removing from "{1}".'.format(item, output_path))
                    Path(output_path, item).unlink()

    ''' Add file to process queue if it meets conversion criteria '''
    def queue_file(self, input_path, output_path, item):
        if not Path(input_path, item).is_file():
            log.debug('"{0}" is a directory. Skipping conversion.'.format(item))
            return

        # Create full file path for input and output
        base_filename = Path(item).stem
        input_extension = Path(item).suffix
        input_file = Path(input_path, item)
        output_file = Path(output_path, item)

        # Skip ignored extensions completely
        if len(self._options['extensions_to_ignore']) > 0 and \
                (input_extension.lstrip('.').lower() in self._options['extensions_to_ignore']):
            return

        # Adjust output file extension if it is going to be converted
        if input_extension.lstrip('.').lower() in self._options['extensions_to_convert']:
            output_filename = base_filename + '.' + self._options['extension']
            output_file = Path(output_path, output_filename)

        self._converter.queue_job(input_file, output_file)

    ''' Wrapper function to call converter's process queue function'''
    def process_queue(self):
        self._converter.process_queue()
