from collections import namedtuple
from pathlib import Path
import json
import logging
import multiprocessing

log = logging.getLogger(__name__)

Options = namedtuple('Options', [
        'bitrate_type',
        'bitrate',
        'codec',
        'convert_extensions',
        'custom_command',
        'extension',
        'ffmpeg_path',
        'ignore_extensions',
        'input_dir',
        'match_method',
        'output_dir',
        'output_sample_rate',
        'thread_count',
    ]
)


def options():
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Set output extension based on codec used
    extension = config['audio']['output_codec']
    if config['audio']['output_codec'] == 'aac' or config['audio']['output_codec'] == 'alac':
        extension = 'm4a'

    # Parse sample rate
    if config['audio']['output_sample_rate'] is None or 0 < config['audio']['output_sample_rate'] <= 5644800:
        output_sample_rate = config['audio']['output_sample_rate']
    else:
        log.fatal(f'Unsupported output_sample_rate: "{ config["audio"]["output_sample_rate"] }".'
                  'Valid options are "null" or a number between 1 and 5644800, inclusive.')
        exit(1)

    # Parse sample rate
    if not config['audio']['bitrate_type'] in ('cbr', 'vbr'):
        log.fatal('Invalid bitrate type: "{0}". Valid options: "cbr" or "vbr"'.format(config['audio']['bitrate_type']))
        exit(1)

    # Parse thread count
    if config['advance']['thread_count'] == 'max':
        thread_count = multiprocessing.cpu_count()
    else:
        thread_count = config['advance']['thread_count']

    # Parse match_method type
    if not (config['advance']['match_method'] == 'date_size' or config['advance']['match_method'] == 'hash'):
        log.fatal('Invalid match method: "{0}". Valid options: "date_size" or "hash"'.format(
            config['advance']['match_method']))
        exit(1)

    # Parse extensions to ignore completely
    ignore_extensions = []
    if config['advance']['ignore_extensions']:
        ignore_extensions = [x.lower().lstrip('.') for x in config['advance']['ignore_extensions']]

    # Parse custom command
    custom_command = ''
    if config['advance']['custom_command_enabled']:
        custom_command = config['ADVANCE']['custom_command']
        if '[INPUT]' not in custom_command or '[OUTPUT]' not in custom_command:
            log.fatal('Custom command does not contain [INPUT] or [OUTPUT] string argument.')
            exit(1)

    return Options(
        bitrate_type=config['audio']['bitrate_type'],
        bitrate=config['audio']['bitrate'],
        codec=config['audio']['output_codec'],
        convert_extensions=config['audio']['convert_extensions'].lower().replace(' ', '').split(','),
        custom_command=custom_command,
        extension=extension,
        ffmpeg_path=config['path']['ffmpeg'],
        ignore_extensions=ignore_extensions,
        input_dir=Path(config['path']['input']).expanduser(),
        match_method=config['advance']['match_method'],
        output_dir=Path(config['path']['output']).expanduser(),
        output_sample_rate=output_sample_rate,
        thread_count=thread_count,
    )
