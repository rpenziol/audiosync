from multiprocessing import Pool
from option_parser import Options
import hashlib
import logging
import os
import shutil
import subprocess

log = logging.getLogger(__name__)


class Converter(object):
    def __init__(self, db, options: Options):
        self._jobs = []
        self._db = db
        self._options = options
        self._ffmpeg_args = self.ffmpeg_arg_generator()

    def process_queue(self, files):
        for file in files:
            file['ffmpeg_args'] = self._ffmpeg_args
            input_path = file['input_file']
            output_path = file['output_file']
            input_path_md5 = 0
            input_path_mtime = input_path.stat().st_mtime
            input_path_size = input_path.stat().st_size
            match = False
            output_exists = False

            # Process file matches either on date modified & size, or by hash
            if self._options.match_method == 'date_size':
                # Check if input file matches in database
                if self._db.get_property(input_path, 'mtime') == input_path_mtime \
                        and self._db.get_property(input_path, 'size') == input_path_size:
                    match = True
            elif self._options.match_method == 'hash':
                input_path_md5 = hashlib.md5(open(input_path, 'rb').read()).hexdigest()
                if self._db.get_hash(input_path) == input_path_md5:
                    match = True

            if output_path.is_file():
                output_exists = True
                if output_path.stat().st_size == 0:  # Empty dest file exists
                    match = False

            if match and output_exists:
                log.debug(f'Output file "{output_path}" up-to-date. Skipping.')
                continue

            if match and not output_exists:
                log.debug(f'Output file "{output_path}" has been removed. Reprocessing.')

            if not match and output_exists:
                log.debug(f'Output file "{output_path}" has changed. Deleting and reprocessing.')
                output_path.unlink()
                self._db.update(input_path, input_path_md5, input_path_mtime, input_path_size)

            if not match and not output_exists:
                log.debug(f'Input file "{input_path}" is new. Adding to processing list.')
                self._db.update(input_path, input_path_md5, input_path_mtime, input_path_size)

            # Simply copy non-audio files
            input_extension = input_path.suffix
            if input_extension.lstrip('.').lower() not in self._options.convert_extensions:
                log.info(f'Copying "{input_path}" to "{output_path}"')
                shutil.copy2(input_path, output_path)
                continue  # No need to add to convert queue

            self._jobs.append(file)

        pool = Pool(processes=self._options.thread_count)
        pool.map(convert, self._jobs)
        pool.close()
        pool.join()

    '''Using the globaloptions variable, this function will generate and return the proper ffmpeg
    command-line arguments based on the given codec / bitrate configuration'''
    def ffmpeg_arg_generator(self):
        ffmpeg_args = ['-vf', 'scale=-2:500']  # Scale album art to height of 500px
        if self._options.output_sample_rate:
            ffmpeg_args.extend(['-ar', str(self._options.output_sample_rate)])

        bitrate = int(self._options.bitrate)

        if self._options.format == 'mp3':
            if self._options.bitrate_type == 'cbr':
                ffmpeg_args.extend(['-b:a', f'{self._options.bitrate}k'])

            if self._options.bitrate_type == 'vbr':
                if bitrate >= 250:
                    quality = '0'
                elif bitrate in range(210, 250):
                    quality = '1'
                elif bitrate in range(180, 210):
                    quality = '2'
                elif bitrate in range(165, 180):
                    quality = '3'
                elif bitrate in range(145, 165):
                    quality = '4'
                elif bitrate in range(125, 145):
                    quality = '5'
                elif bitrate in range(107, 125):
                    quality = '6'
                elif bitrate in range(93, 107):
                    quality = '7'
                elif bitrate in range(70, 93):
                    quality = '8'
                else:
                    quality = '9'
                ffmpeg_args.extend(['-q:a', quality])

        elif self._options.format == 'aac':
            ffmpeg_args.extend(['-c:a', 'aac'])
            if self._options.bitrate_type == 'cbr':
                ffmpeg_args.extend(['-b:a', f'{self._options.bitrate}k'])

            if self._options.bitrate_type == 'vbr':
                if bitrate >= 250:
                    quality = '2'
                elif bitrate in range(70, 250):
                    # Ffmpeg allows args from 0.1 to 2 for AAC. Assuming this scale is linear, this takes the sensible
                    # bitrates between those values and uses a regression and rounding to get a value between 0.1 and 2
                    quality = round(-0.638889 + 0.0105556 * bitrate, 2)
                else:
                    quality = '0.1'
                ffmpeg_args.extend(['-q:a ', quality])

        return ffmpeg_args


'''Converts files using the command line and ffmpeg. Called in a pool as a multiprocess, meaning multiple copies
of these function may run concurrently. Due to constraints of the multiprocessing pool, this function is only
allowed one input variable.'''


def convert(job):
    input_path = str(job['input_file'])
    output_path = str(job['output_file'])
    ffmpeg_path = job['ffmpeg_path']
    custom_command = job['custom_command']
    ffmpeg_args = job['ffmpeg_args']

    log.info('Converting file "{0}" to "{1}"'.format(input_path, output_path))

    if custom_command:
        command_list = custom_command.split()
        command_list[command_list.index('[INPUT]')] = input_path
        command_list[command_list.index('[OUTPUT]')] = output_path
    else:
        command_list = [ffmpeg_path, '-i', input_path]
        command_list.extend(ffmpeg_args)
        command_list.append(output_path)

    fnull = open(os.devnull, 'w')  # Redirect FFMPEG output to /dev/null
    subprocess.call(command_list, stdout=fnull, stderr=fnull, shell=False)
