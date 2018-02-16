"""
Audio fingerprint matcher.
"""
import collections as collect
import numpy as np
import scipy.ndimage.filters as filters

import audiofingerprint.visualize as visualizer


MatchParameters = collect.namedtuple('MatchParameters',
                                     ['histogram_filter_size'])


def get_default_parameters():
    """
    Gets default parameters for audio fingerprint matcher.
    :return: Parameters.
    """
    return MatchParameters(histogram_filter_size=3)


def match(these, those, parameters: MatchParameters, visualize=False):
    """
    Matches these fingerprints with those fingerprints. Note that both fingerprints
    must have been created with the same sampling frequency and parameters.
    :param these: Fingerprints to match.
    :param those: Fingerprints to match with.
    :param parameters: Parameters.
    :param visualize: Visualize algorithm if true.
    :return: Match score, higher means closer match.
    """
    delta_times = []
    for descriptor, times in these.items():
        if descriptor in those:
            for this_time in times:
                for that_time in those[descriptor]:
                    delta_times.append(this_time - that_time)
    if len(delta_times) == 0:
        return 0
    histogram, bin_edges = np.histogram(
        delta_times, range(min(delta_times), max(delta_times) + 2, 1))
    filtered_histogram = filters.generic_filter(
        histogram, sum, parameters.histogram_filter_size, mode='constant', cval=0)
    score = max(filtered_histogram)
    if visualize:
        visualizer.visualize_match(
            histogram, filtered_histogram, bin_edges[:-1], these, those, score, parameters)
    return score
