"""
Various window functions.
"""
import math


def hamming(count):
    """
    Creates a Hamming window.
    :param count: Window length.
    :return: Window.
    """
    return cosine((0.54, -0.46), count)


def fir(count, cutoff_frequency):
    """
    Creates a FIR window.
    :param count: Window length, i.e. filter order + 1, must be odd.
    :param cutoff_frequency: Cutoff frequency, 1 corresponds to the Nyquist frequency ]0,1[.
    :return: Window.
    """
    assert _is_odd(count)
    assert 0 < cutoff_frequency < 1
    order = count - 1
    window = [cutoff_frequency] * count
    for i in range(0, order // 2):
        sample = i - (order / 2)
        coefficient = math.sin(math.pi * cutoff_frequency * sample) / (math.pi * sample)
        window[i] = coefficient
        window[-(i + 1)] = coefficient
    return window


def cosine(coefficients, count):
    """
    Creates a cosine window.
    :param coefficients: Cosine coefficients.
    :param count: Window length.
    :return: Window.
    """
    def symmetric_cosine(coefficients, count):
        """
        Creates a symmetric cosine window, for use in filter design.
        :param coefficients: Cosine coefficients.
        :param count: Window length, must be odd.
        :return: Window.
        """
        assert _is_odd(count)
        return [sum(coefficient * math.cos((2 * math.pi * k * n) / (count - 1))
                    for k, coefficient in enumerate(coefficients))
                for n in range(count)]

    def periodic_cosine(coefficients, count):
        """
        Creates a periodic (DFT-even) cosine window, for use in spectral analysis.
        :param coefficients: Cosine coefficients.
        :param count: Window length, must be even.
        :return: Window.
        """
        assert _is_even(count)
        return symmetric_cosine(coefficients, count + 1)[:-1]

    return periodic_cosine(coefficients, count) if _is_even(count)\
        else symmetric_cosine(coefficients, count)


def _is_even(number):
    """
    Check if a number is even.
    :param number: Number.
    :return: True if even, false otherwise.
    """
    return number % 2 == 0


def _is_odd(number):
    """
    Check if a number is odd.
    :param number: Number.
    :return: True if odd, false otherwise.
    """
    return not _is_even(number)
