"""
Signal spectogram.
"""
import dsp.dft as fourier


def real_spectogram(signal, sampling_frequency, window, overlap=0, dft_count=None):
    """
    Calculates the spectogram of a real signal.
    :param signal: Real signal.
    :param sampling_frequency: Sampling frequency.
    :param window: Window, decides the length of each segment. Must be a power
                   of two if `dft_count` is None.
    :param overlap: Number of points overlap between segments.
    :param dft_count: Length of the DFT, if a cropped or zero padded DFT is desired.
    :return: (Spectogram[time][frequency] power spectral density with unit V^2/Hz
              time axis values,
              frequency axis values).
    """
    if dft_count is None:
        dft_count = len(window)
    real_dft_count = dft_count // 2 + 1
    scale = 1.0 / (sum(_square(window)) * sampling_frequency)
    stft = fourier.stft(signal, window, overlap, dft_count)
    spectogram = [[m * scale * (1 if i == 0 or i == real_dft_count - 1 else 2)
                   # Do not double DC (0) and Nyqvist (dft_count / 2) bins.
                   for i, m in enumerate(_square(fourier.magnitude(dft[:real_dft_count])))]
                  for dft in stft]
    frequencies = fourier.frequency_bin_centers(dft_count, sampling_frequency)[:real_dft_count]
    times = fourier.time_bin_centers(len(spectogram), len(window), overlap, sampling_frequency)
    return (spectogram, times, frequencies)


def _square(data):
    """
    Squares the data element-wise.
    :param data: Data.
    :return: Squared data.
    """
    return (e ** 2 for e in data)
