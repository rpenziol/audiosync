from pathlib import Path
import converter
import database
import logging
import option_parser
import scanner
import shutil
import sys
import time

logging.basicConfig(
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d_%H:%M:%S',
    level=logging.INFO
)
log = logging.getLogger(__name__)


def main():
    log.info('WELCOME TO AUDIOSYNC')
    options = option_parser.options()
    output_dir = options.output_dir

    if '--purge' in sys.argv:
        log.info(f'Purging all files in directory: "{output_dir}"')

        # Delete all folder contents without deleting output_dir folder
        for path in Path(output_dir).iterdir():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)

    db = database.Database(options)
    scan = scanner.Scanner(options)
    convert = converter.Converter(db, options)
    scan.remove_orphans()
    iterator = scan.sync_to_dest()
    convert.process_queue(iterator)
    log.info('DONE SYNCING DIRECTORIES. EXITING.')


if __name__ == '__main__':
    while True:
        main()
        time.sleep(600)
