"""
Demo various DSP functions.
"""
import math
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as sig
import dsp.decimation as dec
import dsp.dft as fourier
import dsp.spectogram as spec
import dsp.windows as win


def demo_all():
    """
    Runs all demos.
    :return: None.
    """
    demo_discrete_fourier_transform()
    demo_windows()
    demo_decimation()
    demo_spectogram()


def demo_discrete_fourier_transform():
    """
    Demo the discrete fourier transform.
    :return: None.
    """
    def verify(signal):
        """
        Verifies DFT against NumPy's implementation.
        :param signal: Signal.
        :return: None.
        """
        count = len(signal) * 2
        assert np.max(np.abs(np.fft.fft(signal, count) - fourier.fft(signal, count))) < 1e-10

    def plot(signal, sampling_frequency):
        """
        Plots a signal and its DFT.
        :param signal: Signal.
        :param sampling_frequency: Sampling frequency.
        :return: None.
        """
        plt.figure(1)
        plt.subplot(211)
        plot_signal(signal, sampling_frequency)
        plt.subplot(212)
        plot_dft(*real_dft(signal, sampling_frequency))
        plt.show()

    amplitude0 = 2.0
    amplitude1 = 1.0
    amplitude2 = 0.5
    frequency1 = 1.0
    frequency2 = 2.0
    continuous_signal = lambda t: amplitude0 + \
                                  amplitude1 * math.sin(frequency1 * 2.0 * math.pi * t) + \
                                  amplitude2 * math.sin(frequency2 * 2.0 * math.pi * t)
    sampling_frequency = 8  # Larger than the Nyquist rate.
    sampling_count = 128  # A multiple of the period of the discrete signal.
    signal = sample(continuous_signal, sampling_count, sampling_frequency)
    verify(signal)
    plot(signal, sampling_frequency)


def demo_windows():
    """
    Demo various windows.
    :return: None.
    """
    def verify():
        """
        Verifies windows against SciPy's implementation.
        :return: None.
        """
        assert np.max(np.abs(win.hamming(12) - sig.hamming(12, False))) < 1e-15
        assert np.max(np.abs(win.hamming(13) - sig.hamming(13, True))) < 1e-15
        assert np.max(dec.anti_aliasing_window(0.3, 64) - sig.firwin(65, 0.3, window='hamming')) \
               < 1e-4
        assert np.max(win.fir(65, 0.3) - sig.firwin(65, 0.3, window='boxcar')) < 1e-3

    def plot(window, name):
        """
        Plots a window and its DFT.
        :param window: Window.
        :param name: Name of the window.
        :return: None.
        """
        plt.figure(1)
        plt.subplot(211)
        plot_window(window, name)
        plt.subplot(212)
        plot_dft(*window_dft(window, 1024))
        plt.show()

    count = 64
    cutoff_frequency = 0.3
    verify()
    plot(win.hamming(count), 'Hamming')
    plot(win.fir(count + 1, cutoff_frequency), 'FIR')
    plot(dec.anti_aliasing_window(cutoff_frequency, count), 'FIR + Hamming')


def demo_decimation():
    """
    Demo signal decimation.
    :return: None.
    """
    def plot(signal, sampling_frequency, decimated_signal, decimated_sampling_frequency):
        """
        Plots a signal and its dft for the original and the decimated version.
        :param signal: Signal.
        :param sampling_frequency: Sampling frequency.
        :param decimated_signal: Decimated signal.
        :param decimated_sampling_frequency: Decimated sampling frequency.
        :return: None.
        """
        dft_count = 1024
        plt.figure(1)
        plt.subplot(221)
        plot_signal(signal, sampling_frequency)
        plt.subplot(222)
        plot_dft(*real_dft(signal, sampling_frequency, dft_count))
        plt.subplot(223)
        plot_signal(decimated_signal, decimated_sampling_frequency)
        plt.subplot(224)
        plot_dft(*real_dft(decimated_signal, decimated_sampling_frequency, dft_count))
        plt.show()

    amplitude1 = 1.0
    amplitude2 = 0.5
    frequency1 = 100
    frequency2 = 435
    sampling_frequency = 1000
    sampling_count = 64
    downsampling_factor = 2
    decimated_sampling_frequency = sampling_frequency / downsampling_factor
    # frequency2 is larger than the downsampled Nyquist rate and will cause aliasing.
    continuous_signal = lambda t: amplitude1 * math.sin(frequency1 * 2.0 * np.pi * t) + \
                                  amplitude2 * math.sin(frequency2 * 2.0 * np.pi * t)
    signal = sample(continuous_signal, sampling_count, sampling_frequency)
    aliased_signal = dec.downsample(signal, downsampling_factor)
    decimated_signal = dec.decimate(signal, downsampling_factor, 128)
    plot(signal, sampling_frequency, aliased_signal, decimated_sampling_frequency)
    plot(signal, sampling_frequency, decimated_signal, decimated_sampling_frequency)


def demo_spectogram():
    """
    Demo spectogram.
    :return: None.
    """
    def verify(signal, sampling_frequency, window, overlap, dft_count, frequencies, times,
               spectogram):
        """
        Verifies a spectogram against SciPy's implementation.
        :param signal: Signal.
        :param sampling_frequency: Sampling frequency.
        :param window: Window.
        :param overlap: Window overlap.
        :param dft_count: Length of DFT.
        :param frequencies: Frequencies to verify.
        :param times: Times to verify.
        :param spectogram: Spectogram to verify.
        :return: None.
        """
        sig_frequencies, sig_times, sig_spectogram = \
            sig.spectrogram(np.array(signal), sampling_frequency, window=window,
                            nperseg=len(window), nfft=dft_count, noverlap=overlap,
                            return_onesided=True, scaling='density', detrend=False, mode='psd')
        assert np.max(np.abs(spectogram - sig_spectogram)) < 1e-13
        assert np.max(np.abs(frequencies - sig_frequencies)) < 1e-14
        assert np.max(np.abs(times - sig_times)) < 1e-14

    def plot(signal, sampling_frequency, frequencies, times, spectogram):
        """
        Plots a signal and its spectogram.
        :param signal: Signal.
        :param sampling_frequency: Sampling frequency.
        :param frequencies: Frequencies.
        :param times: Times.
        :param spectogram: Spectogram.
        :return: None.
        """
        plt.figure(1)
        plt.subplot(211)
        plot_signal(signal, sampling_frequency)
        plt.subplot(212)
        plot_spectogram(times, frequencies, spectogram)
        plt.show()

    def example1():
        """
        Example of a spectogram.
        :return: None.
        """
        amplitude = 2 * math.sqrt(2)
        sampling_frequency = 10000
        sampling_count = 100000
        noise_power = 0.01 * sampling_frequency / 2
        modulation = lambda t: 500 * math.cos(2 * math.pi * 0.25 * t)
        carrier = lambda t: amplitude * math.sin(2 * math.pi * 3e3 * t + modulation(t))
        # pylint: disable=maybe-no-member
        noise = lambda t: np.random.normal(scale=np.sqrt(noise_power)) * math.exp(-t / 5)
        continuous_signal = lambda t: carrier(t) + noise(t)
        signal = sample(continuous_signal, sampling_count, sampling_frequency)
        window = win.hamming(256)
        overlap = len(window) // 8
        spectogram, times, frequencies = \
            spec.real_spectogram(signal, sampling_frequency, window, overlap, len(window))
        spectogram = np.swapaxes(spectogram, 0, 1)
        verify(signal, sampling_frequency, window, overlap, len(window), frequencies, times,
               spectogram)
        plot(signal, sampling_frequency, frequencies, times, spectogram)

    def example2():
        """
        Example of a spectogram.
        :return: None.
        """
        def continuous_signal(time_sample):
            """
            Creates a continuous signal with varying frequency over time.
            :param time_sample: Time.
            :return: Signal value at time.
            """
            if 0 <= time_sample < 5:
                frequency = 10
            elif 5 <= time_sample < 10:
                frequency = 25
            elif 10 <= time_sample < 15:
                frequency = 50
            elif 15 <= time_sample < 20:
                frequency = 100
            else:
                frequency = 0
            return math.sin(frequency * 2.0 * math.pi * time_sample)

        sampling_frequency = 400
        sampling_count = 8000
        signal = sample(continuous_signal, sampling_count, sampling_frequency)
        window_time = 100e-3
        window = win.hamming(int(window_time * sampling_frequency))
        overlap = len(window) // 8
        dft_count = 512
        spectogram, times, frequencies = \
            spec.real_spectogram(signal, sampling_frequency, window, overlap, dft_count)
        spectogram = np.swapaxes(spectogram, 0, 1)
        verify(signal, sampling_frequency, window, overlap, dft_count, frequencies, times,
               spectogram)
        plot(signal, sampling_frequency, frequencies, times, spectogram)

    example1()
    example2()


def sample(signal, count, sampling_frequency):
    """
    Samples a signal.
    :param signal: Signal.
    :param count: Number of samples.
    :param sampling_frequency: Sampling frequency.
    :return: Sampled signal.
    """
    return [signal(n / sampling_frequency) for n in range(count)]


def real_dft(signal, sampling_frequency, count=None):
    """
    Calculates the magnitudes of DFT for a real signal.
    :param signal: Real signal.
    :param sampling_frequency: Sampling frequency.
    :param count: Length of DFT.
    :return: (Magnitudes, Frequencies).
    """
    dft = fourier.fft(signal, count)
    dft_magnitude = scaled_magnitude(dft, len(signal))
    half_count = len(dft_magnitude) // 2
    magnitudes = [dft_magnitude[0]] + [2 * a for a in dft_magnitude[1:half_count]]
    frequencies = \
        fourier.frequency_bin_centers(len(dft_magnitude), sampling_frequency)[0:half_count]
    return (magnitudes, frequencies)


def window_dft(window, count=None):
    """
    Calculates a DFT for a window.
    :param window: Window.
    :param count: Length of DFT.
    :return: None.
    """
    dft = fourier.fft(window, count)
    half_count = len(dft) // 2
    magnitudes = decibel(fourier.magnitude(dft)[0:half_count])
    frequencies = fourier.frequency_bin_centers(len(dft), 2)[0:half_count]
    return (magnitudes, frequencies)


def decibel(amplitudes):
    """
    Converts amplitudes to decibel (dB).
    :param amplitudes: Amplitudes.
    :return: Amplitudes converted to dB.
    """
    return [20 * math.log10(x) if x != 0 else -math.inf for x in amplitudes]


def scaled_magnitude(dft_output, count):
    """
    Calculates the scaled magnitude of a DFT.
    :param dft_output: DFT on complex form.
    :param count: Length of the signal (inverse scaling factor).
    :return: Scaled magnitude.
    """
    return [x / count for x in fourier.magnitude(dft_output)]


def plot_signal(signal, sampling_frequency):
    """
    Plots a signal.
    :param signal: Signal.
    :param sampling_frequency: Sampling frequency.
    :return: None.
    """
    plt.title("Signal")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.plot([n / sampling_frequency for n in range(len(signal))], signal, 'o-')
    plt.grid()


def plot_window(window, name=""):
    """
    Plots a window.
    :param window: Window.
    :param name: Name of the window.
    :return: None.
    """
    plt.title("{} Window".format(name))
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    plt.plot(window, 'o-')
    plt.grid()


def plot_dft(magnitudes, frequencies):
    """
    Plots DFT magnitudes against frequencies.
    :param magnitudes: DFT magnitudes.
    :param frequencies: Frequencies.
    :return: None.
    """
    plt.title("DFT")
    plt.xlabel("Frequency")
    plt.ylabel("Magnitude")
    plt.plot(frequencies, magnitudes)
    plt.grid()


def plot_spectogram(times, frequencies, spectogram):
    """
    Plots a spectogram.
    :param times: Times.
    :param frequencies: Frequencies.
    :param spectogram: Spectogram[frequency][time]
    :return: None.
    """
    plt.pcolormesh(times, frequencies, spectogram, cmap='jet')
    plt.colorbar()
    plt.title('Spectogram')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
