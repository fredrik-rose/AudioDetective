"""
Fingerprint visualizer.
"""
import random as rnd
import sys

import collections as collect
import matplotlib.pyplot as plt
import numpy as np


def visualize_fingerprint(spectogram, time_axis, frequency_axis, time_indices, frequency_indices,
                          fingerprints, parameters):
    """
    Visualizes the fingerprinter algorithm.
    :param spectogram: Spectogram[time][frequency].
    :param time_axis: Spectogram time axis values.
    :param frequency_axis: Spectogram frequency axis values.
    :param time_indices: Feature point time indices.
    :param frequency_indices: Feature point frequency indices.
    :param fingerprints: Fingerprints.
    :param parameters: Parameters.
    """
    points = _index_points_to_value_points(
        zip(time_indices, frequency_indices), time_axis, frequency_axis, parameters.time_bin_size,
        parameters.frequency_bin_size)
    target_zones = _extract_target_zones(fingerprints)
    target_zones = _target_zones_indices_to_values(
        target_zones, time_axis, frequency_axis, parameters.time_bin_size,
        parameters.frequency_bin_size)
    plt.figure(1)
    _plot_log_spectogram(spectogram, time_axis, frequency_axis)
    plt.figure(2)
    _plot_spectogram(spectogram, time_axis, frequency_axis)
    _plot_points(points)
    plt.figure(3)
    _plot_points(points)
    _plot_target_zones(target_zones)
    plt.axis((time_axis[0], time_axis[-1], frequency_axis[0], frequency_axis[-1]))
    _add_axes_labels("sec", "Hz")
    plt.show()


def visualize_match(histogram, filtered_histogram, bin_edges, these, those, score, parameters):
    """
    Visualizes the fingerprint matcher algorithm.
    :param histogram: Histogram over time deltas.
    :param filtered_histogram: Filtered histogram over time deltas.
    :param bin_edges: Bin edges of the histogram.
    :param these: Fingerprints to match.
    :param those: Fingerprints to match with.
    :param score: Matching score.
    :param parameters: Parameters.
    """
    these_target_zones = _extract_target_zones(these)
    those_target_zones = _extract_target_zones(those)
    these_points = _extract_points_from_target_zones(these_target_zones)
    those_points = _extract_points_from_target_zones(those_target_zones)
    delta_time = bin_edges[list(filtered_histogram).index(score)]
    granularity = parameters.histogram_filter_size // 2
    target_zones_matches = _extract_target_zone_matches(these, those, delta_time, granularity)
    matches_target_zones = _extract_target_zones(target_zones_matches)
    these_matched_points = _extract_points_from_target_zones(matches_target_zones)
    shifted_matches_target_zones = _shift_target_zones_times(matches_target_zones, -delta_time)
    time_matches = _extract_time_matches(these, those)
    plt.figure(1)
    _plot_points(these_points)
    _plot_target_zones(these_target_zones)
    _add_axes_labels("indices", "indices")
    plt.figure(2)
    _plot_points(those_points)
    _plot_target_zones(those_target_zones)
    _add_axes_labels("indices", "indices")
    plt.title("Fingerprints to match with")
    plt.figure(3)
    _plot_time_matches(time_matches)
    plt.figure(4)
    _plot_histogram(histogram, filtered_histogram, bin_edges)
    plt.figure(5)
    _plot_points(these_points)
    _plot_target_zones(matches_target_zones, 1)
    _add_axes_labels("indices", "indices")
    plt.title("Fingerprint matches")
    plt.figure(6)
    _plot_points(those_points)
    _plot_target_zones(shifted_matches_target_zones, 1)
    _add_axes_labels("indices", "indices")
    plt.title("Shifted fingerprint matches")
    plt.figure(7)
    _plot_points(these_points, '.y')
    _plot_points(these_matched_points, 'xb')
    _add_axes_labels("indices", "indices")
    plt.title("Matched points")
    plt.show()


def _convert_psd_to_db(spectogram):
    """
    Converts a PSD spectogram to a dB spectogram.
    :param spectogram: Spectogram.
    :return: dB spectogram.
    """
    return 10 * np.log10(spectogram + sys.float_info.epsilon)


def _index_points_to_value_points(points, time_axis, frequency_axis, time_scale, frequency_scale):
    """
    Convert index points to value points.
    :param points: Index points.
    :param time_axis: Time axis values.
    :param frequency_axis: Frequency axis values.
    :param time_scale: Time index scale value.
    :param frequency_scale: Frequency index scale value.
    :return: Value points.
    """
    def _index_to_value(index, axis, scale):
        """
        Converts an index to a value.
        :param index: Index.
        :param axis: Axis values.
        :param scale: Index scale value.
        :return: Value.
        """
        return axis[index * scale]

    return [(_index_to_value(point[0], time_axis, time_scale),
             _index_to_value(point[1], frequency_axis, frequency_scale))
            for point in points]


def _extract_target_zones(fingerprints):
    """
    Extracts target zones from fingerprints.
    :param fingerprints: Fingerprints.
    :return: Target zones [(anchor point, [target zone points])].
    """
    target_zone_indices = collect.defaultdict(list)
    for descriptor, times in fingerprints.items():
        for anchor_time in times:
            values = [int(i) for i in descriptor.split(",")]
            anchor_frequency = values[0]
            frequency = values[1]
            delta_time = values[2]
            time = anchor_time + delta_time
            target_zone_indices[(anchor_time, anchor_frequency)].append((time, frequency))
    return [(anchor, points) for anchor, points in target_zone_indices.items()]


def _target_zones_indices_to_values(target_zone_indices, time_axis, frequency_axis, time_scale,
                                    frequency_scale):
    """
    Converts target zone indices to values.
    :param target_zone_indices: Target zone indices.
    :param time_axis: Time axis values.
    :param frequency_axis: Frequency axis values.
    :param time_scale: Time index scale value.
    :param frequency_scale: Frequency index scale value.
    :return: Target zone values.
    """
    return [(_index_points_to_value_points([anchor_index], time_axis, frequency_axis, time_scale,
                                           frequency_scale)[0],
             _index_points_to_value_points(point_indices, time_axis, frequency_axis, time_scale,
                                           frequency_scale))
            for anchor_index, point_indices in target_zone_indices]


def _extract_points_from_target_zones(target_zones):
    """
    Extracts points from target zones.
    :param target_zones: Target zones.
    :return: Points.
    """
    extracted_points = set()
    for anchor, points in target_zones:
        extracted_points.add(anchor)
        for point in points:
            extracted_points.add(point)
    return list(extracted_points)


def _extract_target_zone_matches(these, those, delta_time, granularity):
    """
    Extracts target zone matches from fingerprints.
    :param these: Fingerprints to match.
    :param those: Fingerprints to match with.
    :param delta_time: Time difference of a match.
    :param granularity: Time granularity of a match.
    :return: Target zone matches.
    """
    matches = collect.defaultdict(set)
    for descriptor, times in these.items():
        if descriptor in those:
            for this in times:
                for that in those[descriptor]:
                    if delta_time - granularity <= this - that <= delta_time + granularity:
                        matches[descriptor].add(this)
    return dict(matches)


def _shift_target_zones_times(target_zones, shift):
    """
    Shifts target zones times.
    :param target_zones: Target zones.
    :param shift: Shift.
    :return: Shifted target zones.
    """
    return [((anchor[0] + shift, anchor[1]), [(point[0] + shift, point[1]) for point in points])
            for anchor, points in target_zones]


def _extract_time_matches(these, those):
    """
    Extracts time index matches from fingerprints.
    :param these: Fingerprints to match.
    :param those: Fingerprints to match with.
    :return: Time matches.
    """
    matches = []
    for descriptor, times in these.items():
        if descriptor in those:
            for this_time in times:
                for that_time in those[descriptor]:
                    matches.append((this_time, that_time))
    return matches


def _add_axes_labels(time_unit="", frequency_unit=""):
    """
    Adds axes labels.
    :param time_unit: Unit of the time axis.
    :param frequency_unit: Unit of the frequency axis.
    """
    plt.xlabel("Time [{}]".format(time_unit))
    plt.ylabel("Frequency [{}]".format(frequency_unit))


def _plot_spectogram(spectogram, time_axis, frequency_axis):
    """
    Plots a spectogram.
    :param spectogram: Spectogram[time][frequency].
    :param time_axis: Time axis values.
    :param frequency_axis: Frequency axis values.
    """
    # pylint: disable=maybe-no-member
    plt.pcolormesh(time_axis, frequency_axis, np.swapaxes(spectogram, 0, 1), cmap=plt.cm.hot)
    color_bar = plt.colorbar()
    color_bar.set_label("Amplitude", rotation=270)
    plt.title("Spectogram")
    plt.xlabel("Time [sec]")
    plt.ylabel("Frequency [Hz]")


def _plot_log_spectogram(spectogram, time_axis, frequency_axis):
    """
    Plots a log spectogram.
    :param spectogram: Spectogram[time][frequency].
    :param time_axis: Time axis values.
    :param frequency_axis: Frequency axis values.
    """
    _plot_spectogram(_convert_psd_to_db(spectogram), time_axis, frequency_axis)


def _plot_points(points, style='x'):
    """
    Plots points.
    :param points: Time-frequency points.
    """
    times, frequencies = zip(*points)
    plt.plot(times, frequencies, style)


def _plot_target_zones(target_zones, reduce_factor=8):
    """
    Plots target zones.
    :param target_zones: Target zones.
    :param reduce_factor: Decides how much to reduce (skip plotting) target zones.
    """
    color_map = plt.get_cmap('jet_r')
    for i, (anchor, points) in enumerate(target_zones):
        if rnd.randint(1, reduce_factor) % reduce_factor:
            continue
        color = color_map(float(i) / len(target_zones))
        for point in points:
            plt.plot([anchor[0], point[0]], [anchor[1], point[1]], c=color)
    plt.title("Fingerprints")


def _plot_time_matches(time_matches):
    """
    Plots time matches.
    :param time_matches: Time matches.
    """
    counter = collect.defaultdict(int)
    for this_time, that_time in time_matches:
        counter[(this_time, that_time)] += 1
    ordered_times = collect.defaultdict(list)
    for time, count in counter.items():
        ordered_times[count].append(time)
    for count, times in ordered_times.items():
        these, those = zip(*times)
        plt.scatter(those, these, facecolors='blue', s=count*16)
    plt.title("Time match relations")
    plt.xlabel("Fingerprint to match with times [indices]")
    plt.ylabel("Fingerprint times [indices]")


def _plot_histogram(histogram, filtered_histogram, bin_edges):
    """
    Plots a histogram.
    :param histogram: Histogram.
    :param filtered_histogram: Filtered histogram.
    :param bin_edges: Histogram bin edges.
    """
    plt.bar(bin_edges, histogram)
    plt.plot(bin_edges, filtered_histogram, color='g', label="Filtered histogram")
    plt.legend()
    plt.title("Histogram of delta times")
    plt.xlabel("Delta time [indices]")
    plt.ylabel("#")
    plt.grid()
