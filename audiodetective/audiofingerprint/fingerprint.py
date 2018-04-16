"""
Audio fingerprinter.
"""
import collections as collect
import numpy as np

import audiodetective.audiofingerprint.features as features
import audiodetective.audiofingerprint.visualize as visualizer
import audiodetective.dsp.spectogram as spec
import audiodetective.dsp.windows as win


FingerprintParameters = collect.namedtuple('FingerprintParameters',
                                           ['window_length',
                                            'window_overlap',
                                            'time_bin_size',
                                            'frequency_bin_size',
                                            'target_zone_min_time_offset',
                                            'target_zone_max_time_offset',
                                            'target_zone_max_frequency_offset',
                                            'target_zone_size'])


def get_default_parameters():
    """
    Gets default parameters for the audio fingerprinter.
    :return: Parameters.
    """
    return FingerprintParameters(window_length=1024,
                                 window_overlap=512,
                                 time_bin_size=1,
                                 frequency_bin_size=1,
                                 target_zone_min_time_offset=32,
                                 target_zone_max_time_offset=128,
                                 target_zone_max_frequency_offset=128,
                                 target_zone_size=8)


def fingerprint(signal, sampling_frequency, parameters: FingerprintParameters, visualize=False):
    """
    Calculates a fingerprint for an audio signal.
    :param signal: Audio signal.
    :param sampling_frequency: Audio signal sampling frequency.
    :param parameters: Parameters.
    :param visualize: Visualize algorithm if true.
    :return: Audio fingerprint, {descriptor: [times]}.
    """
    spectogram, time_axis, frequency_axis = _spectogram_from_signal(
        signal, sampling_frequency, parameters.window_length, parameters.window_overlap)
    feature_points = features.extract_feature_points(
        spectogram, time_axis, frequency_axis, features.get_default_parameters())
    times = _quantize(feature_points[0], parameters.time_bin_size).tolist()
    frequencies = _quantize(feature_points[1], parameters.frequency_bin_size).tolist()
    fingerprints = _fingerprint_from_points(
        times, frequencies,
        (parameters.target_zone_min_time_offset, parameters.target_zone_max_time_offset),
        parameters.target_zone_max_frequency_offset,
        parameters.target_zone_size)
    if visualize:
        visualizer.visualize_fingerprint(
            spectogram, time_axis, frequency_axis, times, frequencies, fingerprints, parameters)
    return fingerprints


def _spectogram_from_signal(signal, sampling_frequency, window_length, overlap):
    """
    Calculates a spectogram from a signal.
    :param signal: Signal.
    :param sampling_frequency: Signal sampling frequency.
    :param window_length: Window length to use for the STFT.
    :param overlap: Overlap of the window [0, window_length-1].
    :return: (Spectogram[time][frequency], time axis values,  frequency axis values).
    """
    window = win.hamming(window_length)
    spectogram, times, frequencies = spec.real_spectogram(
        signal, sampling_frequency, window, overlap)
    # Remove DC and Nyqvist.
    return (np.array(spectogram)[:, 1:-2], np.array(times), np.array(frequencies)[1:-2])


def _quantize(values, bin_size):
    """
    Quantizes values.
    :param values: Values.
    :param bin_size: Number of values in each bin.
    :return: Quantized values.
    """
    return values // bin_size


def _fingerprint_from_points(times, frequencies, target_zone_time_offsets,
                             target_zone_frequency_offset, target_zone_size):
    """
    Calculates fingerprints from time-frequency points.
    :param times: Time values of the points.
    :param frequencies: Frequency values of the points.
    :param target_zone_time_offsets: Target zone time offsets from anchor (min, max).
    :param target_zone_frequency_offset: Target zone max frequency offset from anchor.
    :param target_zone_size: Max number of points in a target zone.
    :return: Fingerprints, {descriptor: [times]}.
    """
    def find_points_in_target_zone(anchor, points, time_offsets, max_frequency_offset, size):
        """
        Finds the points in the target zone for a given anchor.
        :param anchor: Anchor point.
        :param points: Points.
        :param time_offsets: Target zone time offsets from anchor (min, max).
        :param max_time_offset: Target zone max time offset from anchor.
        :param max_frequency_offset: Target zone max frequency offset from anchor.
        :param size: Max number of points in a target zone.
        :return: Points in target zone.
        """
        min_time = anchor[0] + time_offsets[0]
        max_time = anchor[0] + time_offsets[1]
        target_zone = []
        for point in points:
            if (min_time <= point[0] <= max_time
                    and abs(anchor[1] - point[1]) <= max_frequency_offset):
                target_zone.append(point)
                if len(target_zone) >= size:
                    break
        return target_zone

    points = sorted(zip(times, frequencies), key=lambda point: (point[0], point[1]))
    fingerprints = collect.defaultdict(set)
    for anchor in points:
        anchor_time = anchor[0]
        anchor_frequency = anchor[1]
        target_zone = find_points_in_target_zone(
            anchor, points, target_zone_time_offsets, target_zone_frequency_offset,
            target_zone_size)
        for point in target_zone:
            descriptor = _fingerprint_descriptor(point[0], point[1], anchor_frequency, anchor_time)
            fingerprints[descriptor].add(anchor_time)
    return dict(fingerprints)


def _fingerprint_descriptor(time, frequency, anchor_frequency, anchor_time):
    """
    Calculates a fingerprint descriptor for a anchor-point relation.
    :param frequency: Point frequency.
    :param time: Point time.
    :param anchor_frequency: Anchor frequency.
    :param anchor_time: Anchor time.
    :return: Descriptor.
    """
    delta_time = time - anchor_time
    return "{},{},{}".format(anchor_frequency, frequency, delta_time)
