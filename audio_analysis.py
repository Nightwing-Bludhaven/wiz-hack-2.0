#!/usr/bin/env python3
"""
Audio analysis module for extracting frequency bands from audio signals.
Uses FFT to split audio into bass, mids, and treble for light visualization.
"""

import numpy as np


class AudioAnalyzer:
    """Analyzes audio signals and extracts frequency band information."""

    def __init__(self, sample_rate=22050, buffer_size=2048, smoothing=0.3):
        """
        Initialize the audio analyzer.

        Args:
            sample_rate: Audio sample rate in Hz (default: 22050)
            buffer_size: Number of samples per analysis (default: 2048)
            smoothing: Exponential smoothing factor (0-1, higher = smoother)
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.smoothing = smoothing

        # Smoothed values for preventing jitter
        self.smoothed_bass = 0.0
        self.smoothed_mids = 0.0
        self.smoothed_treble = 0.0
        self.smoothed_amplitude = 0.0

        # Auto-gain control
        self.max_bass = 1.0
        self.max_mids = 1.0
        self.max_treble = 1.0
        self.gain_decay = 0.995  # Slowly decay max values

    def analyze(self, audio_chunk):
        """
        Analyze an audio chunk and extract frequency bands.

        Args:
            audio_chunk: numpy array of audio samples

        Returns:
            tuple: (bass, mids, treble) normalized to 0.0-1.0 range
        """
        # Compute FFT
        fft_data = np.fft.rfft(audio_chunk)
        fft_magnitude = np.abs(fft_data)

        # Get frequency bins
        frequencies = np.fft.rfftfreq(len(audio_chunk), 1 / self.sample_rate)

        # Extract frequency bands
        # Bass: 20-250 Hz (kick drums, bass guitar)
        bass_mask = (frequencies >= 20) & (frequencies < 250)
        bass = np.mean(fft_magnitude[bass_mask]) if bass_mask.any() else 0

        # Mids: 250-4000 Hz (vocals, most instruments)
        mids_mask = (frequencies >= 250) & (frequencies < 4000)
        mids = np.mean(fft_magnitude[mids_mask]) if mids_mask.any() else 0

        # Treble: 4000-20000 Hz (cymbals, hi-hats)
        treble_mask = (frequencies >= 4000) & (frequencies < 20000)
        treble = np.mean(fft_magnitude[treble_mask]) if treble_mask.any() else 0

        # Update max values for auto-gain
        self.max_bass = max(bass, self.max_bass * self.gain_decay)
        self.max_mids = max(mids, self.max_mids * self.gain_decay)
        self.max_treble = max(treble, self.max_treble * self.gain_decay)

        # Normalize to 0-1 range
        bass_norm = bass / self.max_bass if self.max_bass > 0 else 0
        mids_norm = mids / self.max_mids if self.max_mids > 0 else 0
        treble_norm = treble / self.max_treble if self.max_treble > 0 else 0

        # Apply exponential smoothing
        self.smoothed_bass = (
            self.smoothing * bass_norm + (1 - self.smoothing) * self.smoothed_bass
        )
        self.smoothed_mids = (
            self.smoothing * mids_norm + (1 - self.smoothing) * self.smoothed_mids
        )
        self.smoothed_treble = (
            self.smoothing * treble_norm + (1 - self.smoothing) * self.smoothed_treble
        )

        # Clamp to 0-1 range
        self.smoothed_bass = np.clip(self.smoothed_bass, 0.0, 1.0)
        self.smoothed_mids = np.clip(self.smoothed_mids, 0.0, 1.0)
        self.smoothed_treble = np.clip(self.smoothed_treble, 0.0, 1.0)

        return self.smoothed_bass, self.smoothed_mids, self.smoothed_treble

    def get_amplitude(self, audio_chunk):
        """
        Calculate the RMS amplitude of an audio chunk.

        Args:
            audio_chunk: numpy array of audio samples

        Returns:
            float: RMS amplitude normalized to 0.0-1.0 range
        """
        rms = np.sqrt(np.mean(audio_chunk**2))

        # Smooth the amplitude
        self.smoothed_amplitude = (
            self.smoothing * rms + (1 - self.smoothing) * self.smoothed_amplitude
        )

        # Normalize (assuming max RMS of ~0.5 for typical audio)
        return np.clip(self.smoothed_amplitude * 2, 0.0, 1.0)

    def detect_beat(self, audio_chunk, threshold=1.5):
        """
        Simple energy-based beat detection.

        Args:
            audio_chunk: numpy array of audio samples
            threshold: Energy ratio needed to trigger beat (default: 1.5)

        Returns:
            bool: True if beat detected
        """
        # Calculate instantaneous energy
        energy = np.sum(audio_chunk**2)

        # Check against recent average (simplified version)
        # In production, you'd maintain a buffer of recent energies
        is_beat = energy > threshold * np.mean(audio_chunk**2)

        return is_beat
