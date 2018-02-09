"""
Spectogram feature extractor.
"""
import collections as collect
import numpy as np


FeatureParameters = collect.namedtuple('FeatureParameters',
                                       ['time_window_size',
                                        'suppression_time_window_size',
                                        'min_frequency_window_size',
                                        'frequency_divisor',
                                        'suppression_percentile'])


def get_default_parameters():
    """
    Gets default parameters for feature extraction.
    :return: Parameters.
    """
    return FeatureParameters(time_window_size=0.25,
                             suppression_time_window_size=4,
                             min_frequency_window_size=32,
                             frequency_divisor=4,
                             suppression_percentile=75)


def extract_feature_points(spectogram, times, frequencies, parameters: FeatureParameters):
    """
    Extract feature points from spectogram.
    :param spectogram: Spectogram[time][frequency].
    :param times: Spectogram time axis values.
    :param frequencies: Spectogram frequency axis values.
    :param parameters: Parameters.
    :return: Feature points ([time_indices], [frequency_indices]).
    """
    # TODO: Apply low pass filter?
    # from scipy.ndimage import filters
    # smoothed_spectogram = filters.gaussian_filter(spectogram, (0.5, 1))
    filtered_spectogram = _non_max_suppression(spectogram, times, frequencies,
                                               parameters.min_frequency_window_size,
                                               parameters.frequency_divisor,
                                               parameters.time_window_size)
    suppressed_histogram = _weak_suppression(spectogram, times,
                                             parameters.suppression_time_window_size,
                                             parameters.suppression_percentile)
    filtered_spectogram[suppressed_histogram == 0] = 0
    feature_points = np.nonzero(filtered_spectogram)
    return feature_points


def _non_max_suppression(spectogram, times, frequencies, min_frequency_window_size,
                         frequency_divisor, time_window_size):
    """
    Max filters a spectogram.
    :param spectogram: Spectogram[time][frequency].
    :param times: Spectogram time axis values.
    :param frequencies: Spectogram frequency axis values.
    :param min_frequency_window_size: Min frequency window size.
    :param frequency_divisor: Frequency window divisor.
    :param time_window_size: Time window size.
    :return: Filtered spectogram.
    """
    filtered_spectogram = _max_filter_log_frequency(spectogram, frequencies,
                                                    min_frequency_window_size, frequency_divisor)
    filtered_spectogram = _max_filter_time(filtered_spectogram, times, time_window_size)
    filtered_spectogram[spectogram != filtered_spectogram] = 0
    return filtered_spectogram


def _max_filter_log_frequency(spectogram, frequencies, min_window_size, frequency_divisor):
    """
    Max filters a spectogram along the frequency axis, using a logarithmic window.
    :param spectogram: Spectogram[time][frequency].
    :param frequencies: Spectogram frequency axis values.
    :param min_window_size: Min frequency window size.
    :param frequency_divisor: The window size at a frequency is the frequency divided by this value.
    :return: Filtered spectogram.
    """
    filtered_spectogram = np.zeros(spectogram.shape)
    for i, frequency in enumerate(frequencies):
        window_size = max(frequency / frequency_divisor, min_window_size)
        footprint = np.absolute(frequencies - frequency) <= window_size
        filtered_spectogram[:, i] = np.amax(spectogram[:, footprint], 1)
    return filtered_spectogram


def _max_filter_time(spectogram, times, window_size):
    """
    Max filters a spectogram along the time axis.
    :param spectogram: Spectogram[time][frequency].
    :param times: Spectogram time axis values.
    :param window_size: Time window size.
    :return: Filtered spectogram.
    """
    filtered_spectogram = np.zeros(spectogram.shape)
    for i, time in enumerate(times):
        footprint = np.absolute(times - time) <= window_size
        filtered_spectogram[i, :] = np.amax(spectogram[footprint, :], 0)
    return filtered_spectogram


def _weak_suppression(spectogram, times, time_window_size, suppression_percentile):
    """
    Filters out (sets to zero) weak values of a spectogram.
    :param spectogram: Spectogram[time][frequency].
    :param times: Spectogram time axis values.
    :param time_window_size: Time window size.
    :param suppression_percentile: Percentile in the window, all smaller values is suppressed.
    :return: Suppressed spectogram.
    """
    filtered_spectogram = spectogram.copy()
    for i, time in enumerate(times):
        footprint = np.absolute(times - time) <= time_window_size
        threshold = np.percentile(spectogram[footprint, :], suppression_percentile)
        filtered_spectogram[i, :][spectogram[i, :] < threshold] = 0
    return filtered_spectogram
