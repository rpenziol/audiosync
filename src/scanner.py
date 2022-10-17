from option_parser import Options
from pathlib import Path
import logging
import shutil

log = logging.getLogger(__name__)


class Scanner(object):
    def __init__(self, options: Options):
        self._options = options

    ''' Recursively scans input directory structure and compares to the destination folder tree.
    Creates missing directories in destination folder, calls dir_scanner to queue conversions, then processes queue '''
    def remove_orphans(self, source_dir: Path = None, dest_dir: Path = None):
        if not source_dir:
            source_dir = self._options.input_dir
        if not dest_dir:
            dest_dir = self._options.output_dir

        def _is_orphaned_dir(path: Path):
            common_path = path.relative_to(dest_dir)
            source_path = Path(source_dir, common_path)
            return path.is_dir() and not source_path.exists()

        def _is_orphaned_file(path: Path):
            if path.is_dir() and path.exists():
                return False

            common_path = path.relative_to(dest_dir)
            source_path = Path(source_dir, common_path)

            source_file_dir = source_path.parent
            dest_filename_without_extension = common_path.stem

            for source_file in source_file_dir.glob(f'{dest_filename_without_extension}*'):
                source_file_extension = source_file.suffix.lstrip('.').lower()

                if source_file_extension in self._options.convert_extensions and \
                   path.suffix.lower().lstrip('.') == self._options.extension:
                    log.debug(f'Source file found "{source_file}".')
                    return False
            return True

        for path in dest_dir.rglob('*'):
            if _is_orphaned_dir(path):
                log.info(f'"{path}" is an orphaned directory. Removing.')
                shutil.rmtree(path)

            elif _is_orphaned_file(path):
                log.info(f'"{path}" is an orphaned file. Removing.')
                path.unlink()

    def sync_to_dest(self, source_dir: Path = None, dest_dir: Path = None):
        if not source_dir:
            source_dir = self._options.input_dir
        if not dest_dir:
            dest_dir = self._options.output_dir

        def _queue_file(source_dir: Path, dest_dir: Path, source_file: Path):
            file_extension = source_file.suffix.lstrip('.').lower()
            if file_extension in self._options.ignore_extensions or \
               file_extension not in self._options.convert_extensions:
                return False

            common_path = source_file.relative_to(source_dir).parent
            filename_without_extension = source_file.stem
            destination_filename = f"{filename_without_extension}.{self._options.extension}"
            destination_file_path = Path(dest_dir, common_path, destination_filename)
            file_to_process = {
                'input_file': source_file,
                'output_file': destination_file_path,
                'ffmpeg_path': self._options.ffmpeg_path,
                'custom_command': self._options.custom_command
            }
            return file_to_process

        for path in source_dir.rglob('*'):
            common_path = path.relative_to(source_dir)
            output_path = Path(dest_dir, common_path)

            if path.is_dir() and not output_path.exists():
                log.info(f'Directory "{output_path}" does not exist. Creating directory')
                output_path.mkdir(parents=True)
            elif path.is_dir():
                log.debug(f'Directory "{output_path}" already exist. Skipping directory creation.')
            else:
                file_to_process = _queue_file(source_dir, dest_dir, path)
                if file_to_process:
                    yield file_to_process
