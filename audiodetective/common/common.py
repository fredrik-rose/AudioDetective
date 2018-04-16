"""
Stuff common for both server and client.
"""
import audiodetective.audiofingerprint.fingerprint as finger
import audiodetective.dsp.decimation as dec


SAMPLING_FREQUENCY = 44100

_DOWNSAMPLING_FACTOR = 4


def fingerprint(signal, visualize=False):
    """
    Fingerprints a signal.
    :param signal: Signal, must be sampled with frequency SAMPLING_FREQUENCY.
    :param visualize: Visualize fingerprint algorithm if true.
    :return: Fingerprint of signal.
    """
    signal, sampling_frequency = _pre_process(signal, SAMPLING_FREQUENCY, _DOWNSAMPLING_FACTOR)
    if visualize:
        _plot_signal(signal, sampling_frequency)
    return finger.fingerprint(signal, sampling_frequency, finger.get_default_parameters(), visualize)


def _pre_process(signal, sampling_frequency, downsampling_factor):
    """
    Pre-processes a signal.
    :param signal: Signal.
    :param sampling_frequency: Sampling frequency.
    :param downsampling_factor: Downsampling factor.
    :return: (signal, sampling frequency).
    """
    decimated_signal = dec.decimate(signal, downsampling_factor)
    sampling_frequency /= downsampling_factor
    return (decimated_signal, sampling_frequency)


def _plot_signal(signal, sampling_frequency):
    """
    Plots a signal.
    :param signal: Signal
    :param sampling_frequency: Sampling frequency
    """
    import matplotlib.pyplot as plt
    plt.title("Signal")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.plot([n / sampling_frequency for n in range(len(signal))], signal, '.-')
    plt.grid()
    plt.show()
