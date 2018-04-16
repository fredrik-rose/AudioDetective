"""
Audio teacher.
"""
import datetime
import os
import subprocess as sp
import time

import numpy as np

from audiodetective.common import common
from audiodetective.server import database as db


_VALID_FILE_TYPES = ('.mp3', '.flac')
_BUFFER_SIZE = 10**8


def teach(directory, database_path, clear_database=False, visualize=False):
    """
    Create fingerprints for audios in a directory and adds them to the database.
    :param directory: Path to directory.
    :param database_path: Path to database.
    :param clear_database: Clear the database if true.
    :param visualize: Visualize fingerprint algorithm if true.
    """
    number_of_files = _number_of_audio_files_in_directory(directory)
    database = db.FingerprintDatabase(database_path, clear_database)
    file_number = 1
    total_start = time.time()
    for directory_path, _, file_names in os.walk(directory):
        for file in file_names:
            if os.path.splitext(file)[1] in _VALID_FILE_TYPES:
                title = os.path.splitext(file)[0]
                print("Learning {} ({}/{})... ".format(title, file_number, number_of_files), end="", flush=True)
                file_number += 1
                start = time.time()
                signal = _signal_from_mp3(os.path.join(directory_path, file), common.SAMPLING_FREQUENCY)
                fingerprint = common.fingerprint(signal, visualize)
                database.add_song(title, fingerprint)
                end = time.time()
                print("Done, took {:.1f} seconds.".format(end - start))
    total_time = round(time.time() - total_start)
    print("Learned {} songs, took {}. ".format(file_number - 1, str(datetime.timedelta(seconds=total_time))),
          end="", flush=True)


def _number_of_audio_files_in_directory(directory):
    """
    Counts the number of audio files in a directory (recursively).
    :param directory: Path to directory.
    :return: Number of files in directory.
    """
    return sum(sum(os.path.splitext(f)[1] in _VALID_FILE_TYPES for f in files) for _, _, files in os.walk(directory))


def _signal_from_mp3(path, sampling_frequency):
    """
    Reads a signal from a MP3 file using FFmpeg.
    :param path: Path to file.
    :param sampling_frequency: Sampling frequency.
    :return: Signal.
    """
    command = ['ffmpeg',
               '-i', path,
               '-f', 's16le',
               '-acodec', 'pcm_s16le',
               '-ar', '{}'.format(sampling_frequency),
               '-ac', '1',
               '-']
    # NOTE: stderr is redirected to remove output from FFmpeg.
    pipe = sp.Popen(command, stdout=sp.PIPE, stderr=open(os.devnull, "w"), bufsize=_BUFFER_SIZE)
    raw_audio = pipe.stdout.read()
    signal = np.fromstring(raw_audio, dtype="int16").tolist()
    return signal
