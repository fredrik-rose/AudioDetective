"""
Audio detective client.
"""
import math

import sounddevice as sd

from audiodetective.common import common
from audiodetective.server import server


_MIN_FINGERPRINT_MATCHES_PER_SECOND = 2


def audio_detective(time, database_path, verbose=False, visualize=False, echo=False):
    """
    Records and identifies a sound.
    :param time: Record time.
    :param database_path: Path to database.
    :param verbose: Print information if true.
    :param visualize: Visualize algorithm if true.
    :param echo: Play the recorded sound if true.
    """
    # FIXME: Why should the client calculate the fingerprint?
    # Sending the points is less data and if bandwidth is not a problem just send the recorded sound.
    input("Play sound, press Enter to record...")
    signal = _record(time, common.SAMPLING_FREQUENCY, echo)
    fingerprint = common.fingerprint(signal, visualize)
    title = server.find_audio(fingerprint, database_path,
                              _MIN_FINGERPRINT_MATCHES_PER_SECOND * time, verbose, visualize)
    if title is not None:
        print("\n{}".format(title))
    else:
        print("\nSorry, did not recognize sound :(")


def _record(time, sampling_frequency, echo=False):
    """
    Records a sound signal.
    :param time: Record time.
    :param sampling_frequency: Sampling frequency.
    :param echo: Play the recorded sound if true.
    :return: Recorded signal.
    """
    count = math.ceil(time * sampling_frequency)
    print("Listening for {} seconds... ".format(time), end="", flush=True)
    signal = sd.rec(count, samplerate=sampling_frequency, channels=1, dtype='int16', blocking=True)
    print("Done.", flush=True)
    if echo:
        input("Press Enter to play back recorded sound...")
        sd.play(signal, sampling_frequency, blocking=True)
        print("Done.", flush=True)
    return signal.flatten().tolist()
