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
    input_dir = option_parser.input_dir()
    output_dir = option_parser.output_dir()

    if '--purge' in sys.argv:
        log.info('Purging all files in directory: "{0}".'.format(output_dir))

        # Delete all folder contents without deleting output_dir folder
        for item in Path(output_dir).iterdir():
            full_path = Path(output_dir, item)
            if full_path.is_file():
                full_path.unlink()
            else:
                shutil.rmtree(full_path)

    scanner.Scanner(input_dir, output_dir, options)
    log.info('DONE SYNCING DIRECTORIES. EXITING.')


if __name__ == '__main__':
    main()
