#!/usr/bin/env python3
"""
Color mapping module for converting audio features to RGB values.
Maps frequency bands to color channels for audio-reactive lighting.
"""

import numpy as np


class FrequencyToRGBMapper:
    """Maps audio frequency bands to RGB color values."""

    def __init__(self, mode="frequency_bands", brightness_boost=1.5):
        """
        Initialize the color mapper.

        Args:
            mode: Mapping mode - 'frequency_bands', 'energy', or 'rainbow'
            brightness_boost: Multiplier for brightness (default: 1.5)
        """
        self.mode = mode
        self.brightness_boost = brightness_boost
        self.min_brightness = 10  # Minimum brightness to keep lights visible

    def map(self, bass, mids, treble, amplitude=None):
        """
        Map frequency bands to RGB color.

        Args:
            bass: Bass intensity (0.0-1.0)
            mids: Mids intensity (0.0-1.0)
            treble: Treble intensity (0.0-1.0)
            amplitude: Overall amplitude (0.0-1.0), optional

        Returns:
            tuple: (r, g, b, brightness) - RGB values 0-255, brightness 0-100
        """
        if self.mode == "frequency_bands":
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)
        elif self.mode == "energy":
            return self._energy_mapping(bass, mids, treble, amplitude)
        elif self.mode == "rainbow":
            return self._rainbow_mapping(bass, mids, treble, amplitude)
        else:
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)

    def _frequency_bands_mapping(self, bass, mids, treble, amplitude):
        """
        Map frequency bands directly to RGB channels.
        Bass → Red, Mids → Green, Treble → Blue
        """
        # Apply non-linear scaling for more dramatic effects
        bass_scaled = self._apply_curve(bass, power=1.5)
        mids_scaled = self._apply_curve(mids, power=1.5)
        treble_scaled = self._apply_curve(treble, power=1.5)

        # Map to RGB (0-255)
        r = int(np.clip(bass_scaled * 255, 0, 255))
        g = int(np.clip(mids_scaled * 255, 0, 255))
        b = int(np.clip(treble_scaled * 255, 0, 255))

        # Calculate brightness from overall energy
        if amplitude is not None:
            brightness = int(
                np.clip(
                    self.min_brightness + amplitude * 90 * self.brightness_boost, 0, 100
                )
            )
        else:
            # Use average of all bands
            avg_intensity = (bass + mids + treble) / 3
            brightness = int(
                np.clip(
                    self.min_brightness + avg_intensity * 90 * self.brightness_boost,
                    0,
                    100,
                )
            )

        return r, g, b, brightness

    def _energy_mapping(self, bass, mids, treble, amplitude):
        """
        Map energy to warm/cool colors.
        High energy → Warm (red/orange)
        Low energy → Cool (blue/purple)
        """
        total_energy = (bass + mids + treble) / 3

        # Warm colors for high energy
        if total_energy > 0.5:
            r = int(255 * total_energy)
            g = int(165 * total_energy)  # Orange tint
            b = int(50 * (1 - total_energy))
        else:
            # Cool colors for low energy
            r = int(128 * total_energy)
            g = int(50 * total_energy)
            b = int(255 * (1 - total_energy))

        brightness = int(
            np.clip(
                self.min_brightness + total_energy * 90 * self.brightness_boost, 0, 100
            )
        )

        return r, g, b, brightness

    def _rainbow_mapping(self, bass, mids, treble, amplitude):
        """
        Create rainbow effect based on dominant frequency.
        """
        # Find dominant frequency band
        bands = [bass, mids, treble]
        dominant_idx = np.argmax(bands)
        dominant_intensity = bands[dominant_idx]

        # Map to rainbow colors
        if dominant_idx == 0:  # Bass dominant → Red/Purple
            r = int(255 * dominant_intensity)
            g = int(50 * dominant_intensity)
            b = int(200 * dominant_intensity)
        elif dominant_idx == 1:  # Mids dominant → Green/Yellow
            r = int(200 * dominant_intensity)
            g = int(255 * dominant_intensity)
            b = int(50 * dominant_intensity)
        else:  # Treble dominant → Cyan/Blue
            r = int(50 * dominant_intensity)
            g = int(200 * dominant_intensity)
            b = int(255 * dominant_intensity)

        brightness = int(
            np.clip(
                self.min_brightness + dominant_intensity * 90 * self.brightness_boost,
                0,
                100,
            )
        )

        return r, g, b, brightness

    def _apply_curve(self, value, power=2.0):
        """
        Apply power curve for more dramatic color changes.
        Lower values get compressed, higher values get emphasized.
        """
        return np.power(value, power)


class BeatReactiveMapper:
    """Mapper that reacts to beats with flashes and pulses."""

    def __init__(self, base_mapper, flash_duration=0.1):
        """
        Initialize beat-reactive mapper.

        Args:
            base_mapper: Base FrequencyToRGBMapper instance
            flash_duration: Duration of beat flash in seconds
        """
        self.base_mapper = base_mapper
        self.flash_duration = flash_duration
        self.beat_timer = 0
        self.is_flashing = False

    def map(self, bass, mids, treble, amplitude=None, is_beat=False):
        """
        Map with beat detection.

        Args:
            bass, mids, treble: Frequency intensities
            amplitude: Overall amplitude
            is_beat: Whether a beat was detected

        Returns:
            tuple: (r, g, b, brightness)
        """
        # Get base color
        r, g, b, brightness = self.base_mapper.map(bass, mids, treble, amplitude)

        # Flash white on beat
        if is_beat:
            self.is_flashing = True
            self.beat_timer = 0
            return 255, 255, 255, 100  # Full white flash

        # Return to normal color after flash
        return r, g, b, brightness


class MultiLightMapper:
    """Mapper for controlling multiple lights with different frequency bands."""

    def __init__(self):
        """Initialize multi-light mapper."""
        pass

    def map_lights(self, bass, mids, treble, num_lights=3):
        """
        Create color mapping for multiple lights.

        Args:
            bass, mids, treble: Frequency intensities
            num_lights: Number of lights to control

        Returns:
            list: List of (r, g, b, brightness) tuples for each light
        """
        colors = []

        if num_lights >= 1:
            # Light 1: Bass-heavy (red/purple)
            r = int(bass * 255)
            g = int(bass * 50)
            b = int(bass * 200)
            brightness = int(np.clip(10 + bass * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 2:
            # Light 2: Mids (green/yellow)
            r = int(mids * 200)
            g = int(mids * 255)
            b = int(mids * 50)
            brightness = int(np.clip(10 + mids * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 3:
            # Light 3: Treble (cyan/blue)
            r = int(treble * 50)
            g = int(treble * 200)
            b = int(treble * 255)
            brightness = int(np.clip(10 + treble * 90, 0, 100))
            colors.append((r, g, b, brightness))

        # Additional lights cycle through combinations
        for i in range(3, num_lights):
            offset = i % 3
            if offset == 0:
                r, g, b = int(bass * 255), int(treble * 255), int(mids * 255)
            elif offset == 1:
                r, g, b = int(mids * 255), int(bass * 255), int(treble * 255)
            else:
                r, g, b = int(treble * 255), int(mids * 255), int(bass * 255)

            avg = (bass + mids + treble) / 3
            brightness = int(np.clip(10 + avg * 90, 0, 100))
            colors.append((r, g, b, brightness))

        return colors
