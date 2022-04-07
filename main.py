from pathlib import Path
import logging
import option_parser
import scanner
import shutil
import sys

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    log.info('WELCOME TO AUDIOSYNC')
    options = option_parser.options()
    output_dir = options['output_dir']

    if '--purge' in sys.argv:
        log.info(f'Purging all files in directory: "{output_dir}"')

        # Delete all folder contents without deleting output_dir folder
        for path in Path(output_dir).iterdir():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)

    scan = scanner.Scanner(options)
    scan.remove_orphans()
    scan.sync_to_dest()
    log.info('DONE SYNCING DIRECTORIES. EXITING.')


if __name__ == '__main__':
    main()
