"""
Signal decimation functions.
"""
import dsp.windows as windows


def decimate(signal, downsampling_factor, filter_order=30):
    """
    Decimates a signal.
    :param signal: Signal.
    :param downsampling_factor: Downsampling factor.
    :param filter_order: FIR low pass filter order, must be even.
    :return: Decimated signal.
    """
    cutoff_frequency = 1 / downsampling_factor
    filtered_signal = anti_aliasing_filter(signal, cutoff_frequency, filter_order)
    return downsample(filtered_signal, downsampling_factor)


def anti_aliasing_filter(signal, cutoff_frequency, filter_order):
    """
    Filters a signal with an anti-aliasing (low-pass) filter.
    :param signal: Signal.
    :param cutoff_frequency: Cutoff frequency, 1 corresponds to the Nyquist frequency ]0,1[.
    :param filter_order: FIR low pass filter order, must be even.
    :return: Anti-aliased signal.
    """
    window = anti_aliasing_window(cutoff_frequency, filter_order)
    return convolve(signal, window)


def downsample(signal, factor):
    """
    Downsamples a signal.
    :param signal: Signal.
    :param factor: Downsampling factor.
    :return: Downsampled signal.
    """
    return signal[::factor]


def anti_aliasing_window(cutoff_frequency, filter_order):
    """
    Creates an anti-aliasing window.
    :param cutoff_frequency: Cutoff frequency, 1 corresponds to the Nyquist frequency ]0,1[.
    :param filter_order: FIR low pass filter order, must be even.
    :return: Window.
    """
    fir_window = windows.fir(filter_order + 1, cutoff_frequency)
    hamming_window = windows.hamming(len(fir_window))
    return [fir * hamming for fir, hamming in zip(fir_window, hamming_window)]


def convolve(signal, kernel):
    """
    Convolves a signal with a kernel.
    :param signal: Signal.
    :param kernel: Kernel.
    :return: signal * kernel.
    """
    padding = [0] * (len(kernel) // 2)
    padded_signal = padding + signal + padding
    flipped_kernel = kernel[::-1]
    return [sum(s * k for s, k in zip(padded_signal[n:n + len(kernel)], flipped_kernel))
            for n in range(len(signal))]
