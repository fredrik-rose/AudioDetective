"""
Discrete Fourier Transform (DFT), for use in e.g. spectral analysis.
"""
import math
import cmath


def fft(signal, count=None):
    """
    Calculates the DFT using the Cooley–Tukey radix-2 decimation-in-time
    algorithm.
    :param signal: Signal, length must be a power of two if `count` is None.
    :param count: Length of the DFT, if smaller than the length of the input,
                  the signal is cropped. If it is larger, the signal is zero
                  padded. Must be a power of two.
    :return: DFT on complex form.
    """
    def cooley_tukey(signal):
        """
        Calculates the DFT.
        :param signal: Signal, length must be a power of two.
        :return: DFT on complex form.
        """
        count = len(signal)
        assert _is_power_of_two(count)
        if count == 1:
            return signal
        else:
            even = cooley_tukey(signal[0::2])
            odd = cooley_tukey(signal[1::2])
            twiddle_factor = [cmath.exp(-2j * math.pi * (k / count)) for k in range(count // 2)]
            return [e + (t * o) for e, o, t in zip(even, odd, twiddle_factor)] + \
                   [e - (t * o) for e, o, t in zip(even, odd, twiddle_factor)]

    if count is None:
        count = len(signal)
    signal = zero_pad(signal, count)
    return cooley_tukey(signal[:count])


def stft(signal, window, overlap=0, dft_count=None):
    """
    Calculates the short-time Fourier transform (STFT). A narrow window gives good
    time resolution but poor frequency resolution. A wide window gives good
    frequency resolution but poor time resolution. Note that no scaling is
    performed to compensate for the window.
    :param signal: Signal.
    :param window: Window, decides the length of each segment. Length must be a
                   power of two if `transform_count` is None.
    :param overlap: Number of points overlap between segments.
    :param dft_count: Length of the DFT, if a zero padded or cropped DFT is
                      desired. Must be a power of two.
    :return: stft[time][frequency] on complex form.
    """
    count = len(window)
    assert overlap < count
    return [fft(_multiply(signal[i:i + count], window), dft_count)
            for i in range(0, len(signal) - count, count - overlap)]


def dft(signal):
    """
    Calculates the DFT (slowly).
    :param signal: Signal.
    :return: DFT on complex form.
    """
    count = len(signal)
    return [sum(x * cmath.exp(-2j * math.pi * (k / count) * n) for n, x in enumerate(signal))
            for k in range(count)]


def zero_pad(signal, count):
    """
    Zero pads a signal.
    :param signal: Signal.
    :param count: Length of padded signal.
    :return: Zero padded signal.
    """
    return signal + [0] * (count - len(signal))


def magnitude(dft_output):
    """
    Calculates the magnitude of a DFT.
    :param dft_output: DFT on complex form.
    :return: Magnitude.
    """
    return [abs(x) for x in dft_output]


def phase(dft_output):
    """
    Returns the phase of a DFT.
    :param dft_output: DFT on complex form.
    :return: Phase.
    """
    return [math.atan2(x.imag, x.real) for x in dft_output]


def frequency_bin_centers(count, sampling_frequency):
    """
    Calculates the DFT frequency bin centers.
    :param count: Length of the DFT.
    :param sampling_frequency: Sampling frequency.
    :return: Frequency bin centers.
    """
    frequency_resolution = sampling_frequency / count
    return [k * frequency_resolution for k in range(count)]


def time_bin_centers(count, segment_count, overlap, sampling_frequency):
    """
    Calculates the STFT time bin centers.
    :param count: Length of the STFT.
    :param segment_count: Segment length.
    :param overlap: Number of points overlap between segments.
    :param sampling_frequency: Sampling frequency.
    :return: Time bin centers.
    """
    return [((k * (segment_count - overlap)) + (segment_count / 2)) * (1.0 / sampling_frequency)
            for k in range(count)]


def ceil_power_of_two(number):
    """
    Ceil a number to the next power of two.
    :param number: Number.
    :return: Next power of two.
    """
    return 1 << (number - 1).bit_length()


def _multiply(factor_a, factor_b):
    """
    Multiply arguments element-wise.
    :param factor_a: First operand.
    :param factor_b: Second operand.
    :return: Multiplied operands.
    """
    return [a * b for a, b in zip(factor_a, factor_b)]


def _is_power_of_two(number):
    """
    Checks if a number is a power of two.
    :param number: Number.
    :return: True if number is a power of two, false otherwise.
    """
    return number != 0 and ((number & (number - 1)) == 0)
