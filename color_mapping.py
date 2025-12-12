#!/usr/bin/env python3
"""
Color mapping module for converting audio features to RGB values.
Maps frequency bands to color channels for audio-reactive lighting.
"""

import numpy as np
import time
import colorsys


class FrequencyToRGBMapper:
    """Maps audio frequency bands to RGB color values."""

    def __init__(self, mode="frequency_bands", brightness_boost=1.5):
        self.mode = mode
        self.brightness_boost = brightness_boost
        self.min_brightness = 10 

    def map(self, bass, mids, treble, amplitude=None):
        if self.mode == "frequency_bands":
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)
        elif self.mode == "energy":
            return self._energy_mapping(bass, mids, treble, amplitude)
        elif self.mode == "rainbow":
            return self._rainbow_mapping(bass, mids, treble, amplitude)
        else:
            return self._frequency_bands_mapping(bass, mids, treble, amplitude)

    def _frequency_bands_mapping(self, bass, mids, treble, amplitude):
        bass_scaled = self._apply_curve(bass, power=1.5)
        mids_scaled = self._apply_curve(mids, power=1.5)
        treble_scaled = self._apply_curve(treble, power=1.5)

        r = int(np.clip(bass_scaled * 255, 0, 255))
        g = int(np.clip(mids_scaled * 255, 0, 255))
        b = int(np.clip(treble_scaled * 255, 0, 255))

        if amplitude is not None:
            brightness = int(np.clip(self.min_brightness + amplitude * 90 * self.brightness_boost, 0, 100))
        else:
            avg_intensity = (bass + mids + treble) / 3
            brightness = int(np.clip(self.min_brightness + avg_intensity * 90 * self.brightness_boost, 0, 100))

        return r, g, b, brightness

    def _energy_mapping(self, bass, mids, treble, amplitude):
        total_energy = (bass + mids + treble) / 3
        if total_energy > 0.5:
            r = int(255 * total_energy)
            g = int(165 * total_energy) 
            b = int(50 * (1 - total_energy))
        else:
            r = int(128 * total_energy)
            g = int(50 * total_energy)
            b = int(255 * (1 - total_energy))

        brightness = int(np.clip(self.min_brightness + total_energy * 90 * self.brightness_boost, 0, 100))
        return r, g, b, brightness

    def _rainbow_mapping(self, bass, mids, treble, amplitude):
        bands = [bass, mids, treble]
        dominant_idx = np.argmax(bands)
        dominant_intensity = bands[dominant_idx]

        if dominant_idx == 0: 
            r, g, b = int(255 * dominant_intensity), int(50 * dominant_intensity), int(200 * dominant_intensity)
        elif dominant_idx == 1: 
            r, g, b = int(200 * dominant_intensity), int(255 * dominant_intensity), int(50 * dominant_intensity)
        else: 
            r, g, b = int(50 * dominant_intensity), int(200 * dominant_intensity), int(255 * dominant_intensity)

        brightness = int(np.clip(self.min_brightness + dominant_intensity * 90 * self.brightness_boost, 0, 100))
        return r, g, b, brightness

    def _apply_curve(self, value, power=2.0):
        return np.power(value, power)


class BeatReactiveMapper:
    def __init__(self, base_mapper, flash_duration=0.1):
        self.base_mapper = base_mapper
        self.flash_duration = flash_duration
        self.beat_timer = 0
        self.is_flashing = False

    def map(self, bass, mids, treble, amplitude=None, is_beat=False):
        r, g, b, brightness = self.base_mapper.map(bass, mids, treble, amplitude)
        if is_beat:
            self.is_flashing = True
            self.beat_timer = 0
            return 255, 255, 255, 100
        return r, g, b, brightness


class MultiLightMapper:
    def __init__(self):
        pass

    def map_lights(self, bass, mids, treble, num_lights=3):
        colors = []
        if num_lights >= 1:
            r = int(bass * 255)
            g = int(bass * 50)
            b = int(bass * 200)
            brightness = int(np.clip(10 + bass * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 2:
            r = int(mids * 200)
            g = int(mids * 255)
            b = int(mids * 50)
            brightness = int(np.clip(10 + mids * 90, 0, 100))
            colors.append((r, g, b, brightness))

        if num_lights >= 3:
            r = int(treble * 50)
            g = int(treble * 200)
            b = int(treble * 255)
            brightness = int(np.clip(10 + treble * 90, 0, 100))
            colors.append((r, g, b, brightness))

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


class PulseModeMapper:
    def __init__(self, base_color=(255, 200, 150), sensitivity=1.0):
        self.base_color = base_color
        self.min_brightness = 10
        self.max_brightness = 100
        self.sensitivity = sensitivity

    def map(self, bass, mids, treble, amplitude=None):
        r, g, b = self.base_color
        if amplitude is not None:
            energy = amplitude
        else:
            energy = (bass + mids + treble) / 3

        power = 1.5 / self.sensitivity if self.sensitivity > 0 else 1.5
        brightness_range = self.max_brightness - self.min_brightness
        brightness = int(np.clip(self.min_brightness + (energy**power) * brightness_range, self.min_brightness, self.max_brightness))
        return r, g, b, brightness


class StrobeModeMapper:
    def __init__(self, strobe_color=(255, 255, 255), threshold=1.3, sensitivity=1.0):
        self.strobe_color = strobe_color
        self.threshold = threshold / sensitivity if sensitivity > 0 else threshold
        self.min_brightness = 5
        self.max_brightness = 100
        self.last_energy = 0.0

    def map(self, bass, mids, treble, amplitude=None, is_beat=False):
        r, g, b = self.strobe_color
        current_energy = amplitude if amplitude is not None else (bass + mids + treble) / 3
        energy_ratio = (current_energy / self.last_energy if self.last_energy > 0.01 else 1.0)
        self.last_energy = current_energy * 0.7 + self.last_energy * 0.3

        if energy_ratio > self.threshold or current_energy > 0.7:
            brightness = self.max_brightness
        else:
            low_brightness = int(np.clip(current_energy * 40, self.min_brightness, self.max_brightness * 0.3))
            brightness = int(np.clip(low_brightness, self.min_brightness, self.max_brightness))
        return r, g, b, brightness


class SpectrumPulseMapper:
    """
    Mejorado: Colores basados en frecuencia, pero el brillo manda.
    Incluye 'Smart Sensitivity' para detectar intros sin bajo (ej. ladridos)
    con INYECCIÓN DE POTENCIA para que brillen fuerte.
    """
    def __init__(self, brightness_emphasis=2.0, sensitivity=1.0):
        self.brightness_emphasis = brightness_emphasis
        self.min_brightness = 5
        self.max_brightness = 100
        self.sensitivity = sensitivity

    def map(self, bass, mids, treble, amplitude=None):
        bands = {"bass": bass, "mids": mids, "treble": treble}
        dominant = max(bands, key=bands.get)

        if dominant == "bass":
            base_color = (200, 50, 150) 
        elif dominant == "treble":
            base_color = (50, 150, 255) 
        else:
            base_color = (255, 180, 50) 

        r, g, b = [int(c * 0.8) for c in base_color]

        # CÁLCULO INTELIGENTE DE ENERGÍA
        if bass > 0.3:
            energy = bass
        else:
            bark_signal = (mids * 2.0) + (treble * 0.8) 
            if bark_signal > 0.35:
                r, g, b = 255, 255, 220 # Flash
                energy = min(bark_signal * 2.5, 1.0)
            else:
                energy = bark_signal * 0.5 

        if amplitude is not None:
            energy = (energy * 0.7) + (amplitude * 0.3)

        power = (1.0 / self.brightness_emphasis) / self.sensitivity if self.sensitivity > 0 else (1.0 / self.brightness_emphasis)
        brightness_range = self.max_brightness - self.min_brightness
        brightness = int(np.clip(self.min_brightness + (energy**power) * brightness_range, self.min_brightness, self.max_brightness))

        return r, g, b, brightness


class SimplePulseMapper:
    def __init__(self, min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b = self.min_b
        self._last_rgb = (220, 120, 60)

    def _pick_color(self, bass, mids, treble):
        if bass >= mids and bass >= treble: base = (255, 40, 40)
        elif treble >= mids: base = (50, 100, 255)
        else: base = (60, 255, 80)
        r = int(0.8 * base[0] + 0.2 * self._last_rgb[0])
        g = int(0.8 * base[1] + 0.2 * self._last_rgb[1])
        b = int(0.8 * base[2] + 0.2 * self._last_rgb[2])
        self._last_rgb = (r, g, b)
        return self._last_rgb

    def map(self, bass, mids, treble, amplitude):
        level = float(np.clip(amplitude, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        if self._peak <= 1e-6 or level < self.noise_gate * self._peak:
            target_b = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b = int(self.min_b + shaped * (self.max_b - self.min_b))

        delta = np.clip(target_b - self._prev_b, -self.max_step, self.max_step)
        brightness = int(np.clip(self._prev_b + delta, self.min_b, self.max_b))
        self._prev_b = brightness
        r, g, b = self._pick_color(bass, mids, treble)
        return r, g, b, brightness


class StereoSplitMapper:
    def __init__(self, min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        warm_energy = bass * 0.6 + mids * 0.4
        if bass > mids * 1.2: color1 = (255, 60, 30)
        elif bass > mids * 0.8: color1 = (255, 120, 40)
        else: color1 = (255, 200, 80)

        cool_energy = mids * 0.4 + treble * 0.6
        if treble > mids * 1.2: color2 = (80, 100, 255)
        elif treble > mids * 0.8: color2 = (80, 180, 255)
        else: color2 = (100, 255, 200)

        level1 = float(np.clip(warm_energy, 0.0, 1.0))
        level2 = float(np.clip(cool_energy, 0.0, 1.0))
        self._peak = max(max(level1, level2), self._peak * self.peak_decay)

        if self._peak <= 1e-6 or level1 < self.noise_gate * self._peak: target_b1 = self.min_b
        else:
            norm1 = np.clip(level1 / (self._peak + 1e-6), 0.0, 1.0)
            shaped1 = norm1**self.gamma
            target_b1 = int(self.min_b + shaped1 * (self.max_b - self.min_b))

        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        if self._peak <= 1e-6 or level2 < self.noise_gate * self._peak: target_b2 = self.min_b
        else:
            norm2 = np.clip(level2 / (self._peak + 1e-6), 0.0, 1.0)
            shaped2 = norm2**self.gamma
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [(color1[0], color1[1], color1[2], brightness1), (color2[0], color2[1], color2[2], brightness2)]

    def map(self, bass, mids, treble, amplitude):
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class ComplementaryPulseMapper:
    def __init__(self, min_brightness=15, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b = self.min_b

    def _get_complementary_color(self, r, g, b):
        return (255 - r, 255 - g, 255 - b)

    def map_lights(self, bass, mids, treble, num_lights=2):
        total_energy = bass + mids + treble
        if total_energy < 1e-6: total_energy = 1e-6

        if bass >= mids and bass >= treble: main_color = (255, 50, 50)
        elif treble >= mids: main_color = (50, 100, 255)
        else: main_color = (80, 255, 100)

        comp_color = self._get_complementary_color(*main_color)
        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        if self._peak <= 1e-6 or level < self.noise_gate * self._peak: target_b = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b = int(self.min_b + shaped * (self.max_b - self.min_b))

        delta = np.clip(target_b - self._prev_b, -self.max_step, self.max_step)
        brightness_main = int(np.clip(self._prev_b + delta, self.min_b, self.max_b))
        self._prev_b = brightness_main
        brightness_comp = int(np.clip(self.max_b - (brightness_main - self.min_b), self.min_b, self.max_b))

        return [(main_color[0], main_color[1], main_color[2], brightness_main), (comp_color[0], comp_color[1], comp_color[2], brightness_comp)]

    def map(self, bass, mids, treble, amplitude):
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class BeatLeaderFollowerMapper:
    def __init__(self, min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.7, noise_gate=0.05, max_step=15, delay_frames=4):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self.delay_frames = delay_frames
        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b
        self._history = []
        self._last_color = (60, 255, 80)

    def map_lights(self, bass, mids, treble, num_lights=2):
        total_energy = bass + mids + treble
        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))

        if bass >= mids and bass >= treble: follower_color = (255, 60, 60)
        elif treble >= mids: follower_color = (80, 120, 255)
        else: follower_color = (80, 255, 120)

        r = int(0.7 * follower_color[0] + 0.3 * self._last_color[0])
        g = int(0.7 * follower_color[1] + 0.3 * self._last_color[1])
        b = int(0.7 * follower_color[2] + 0.3 * self._last_color[2])
        self._last_color = (r, g, b)

        leader_color = (255, 240, 220)
        self._peak = max(level, self._peak * self.peak_decay)

        if self._peak <= 1e-6 or level < self.noise_gate * self._peak: target_b1 = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            target_b1 = int(self.min_b + shaped * (self.max_b - self.min_b))

        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        self._history.append((level, r, g, b))
        if len(self._history) > self.delay_frames: self._history.pop(0)

        if len(self._history) >= self.delay_frames: delayed_level, delayed_r, delayed_g, delayed_b = self._history[0]
        else: delayed_level, delayed_r, delayed_g, delayed_b = level, r, g, b

        if self._peak <= 1e-6 or delayed_level < self.noise_gate * self._peak: target_b2 = self.min_b
        else:
            norm2 = np.clip(delayed_level / (self._peak + 1e-6), 0.0, 1.0)
            shaped2 = norm2**1.1
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        delta2 = np.clip(target_b2 - self._prev_b2, -5, 5)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [(leader_color[0], leader_color[1], leader_color[2], brightness1), (delayed_r, delayed_g, delayed_b, brightness2)]

    def map(self, bass, mids, treble, amplitude):
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class FrequencyDanceMapper:
    def __init__(self, min_brightness=15, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        total_energy = bass + mids + treble
        if total_energy < 1e-6: total_energy = 1e-6

        bass_weight = (bass + mids * 0.3) / total_energy
        treble_weight = (treble + mids * 0.3) / total_energy
        dominance = treble_weight / (bass_weight + treble_weight) if (bass_weight + treble_weight) > 0 else 0.5

        bass_influence = 1.0 - dominance
        color1_r = int(np.clip(180 + bass_influence * 75, 80, 255))
        color1_g = int(np.clip(50 + (1 - abs(dominance - 0.5) * 2) * 80, 50, 130))
        color1_b = int(np.clip(50 + (1 - bass_influence) * 100, 50, 150))

        treble_influence = dominance
        color2_r = int(np.clip(80 + (1 - treble_influence) * 100, 50, 180))
        color2_g = int(np.clip(80 + (1 - abs(dominance - 0.5) * 2) * 80, 80, 160))
        color2_b = int(np.clip(150 + treble_influence * 105, 150, 255))

        level = float(np.clip(total_energy / 3.0, 0.0, 1.0))
        self._peak = max(level, self._peak * self.peak_decay)

        if self._peak <= 1e-6 or level < self.noise_gate * self._peak: base_brightness = self.min_b
        else:
            norm = np.clip(level / (self._peak + 1e-6), 0.0, 1.0)
            shaped = norm**self.gamma
            base_brightness = int(self.min_b + shaped * (self.max_b - self.min_b))

        brightness_range = base_brightness - self.min_b
        target_b1 = int(self.min_b + brightness_range * (1.0 - dominance))
        target_b2 = int(self.min_b + brightness_range * dominance)

        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [(color1_r, color1_g, color1_b, brightness1), (color2_r, color2_g, color2_b, brightness2)]

    def map(self, bass, mids, treble, amplitude):
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class SpectrumGradientMapper:
    """
    🌊 Spectrum gradient mapper - visual frequency gradient.
    """
    def __init__(self, min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8):
        self.min_b = int(min_brightness)
        self.max_b = int(max_brightness)
        self.peak_decay = float(peak_decay)
        self.gamma = float(gamma)
        self.noise_gate = float(noise_gate)
        self.max_step = int(max_step)
        self._peak_low = 0.2
        self._peak_high = 0.2
        self._prev_b1 = self.min_b
        self._prev_b2 = self.min_b

    def map_lights(self, bass, mids, treble, num_lights=2):
        low_energy = bass + mids * 0.3
        if bass > mids: color1 = (255, int(40 + bass * 80), 30)
        else: color1 = (255, int(100 + mids * 100), 50)

        high_energy = treble + mids * 0.3
        if treble > mids: color2 = (int(60 + treble * 40), int(80 + treble * 100), 255)
        else: color2 = (int(120 + mids * 80), int(80 + mids * 120), 255)

        level_low = float(np.clip(low_energy, 0.0, 1.0))
        level_high = float(np.clip(high_energy, 0.0, 1.0))
        self._peak_low = max(level_low, self._peak_low * self.peak_decay)
        self._peak_high = max(level_high, self._peak_high * self.peak_decay)

        if self._peak_low <= 1e-6 or level_low < self.noise_gate * self._peak_low: target_b1 = self.min_b
        else:
            norm1 = np.clip(level_low / (self._peak_low + 1e-6), 0.0, 1.0)
            shaped1 = norm1**self.gamma
            target_b1 = int(self.min_b + shaped1 * (self.max_b - self.min_b))

        delta1 = np.clip(target_b1 - self._prev_b1, -self.max_step, self.max_step)
        brightness1 = int(np.clip(self._prev_b1 + delta1, self.min_b, self.max_b))
        self._prev_b1 = brightness1

        if self._peak_high <= 1e-6 or level_high < self.noise_gate * self._peak_high: target_b2 = self.min_b
        else:
            norm2 = np.clip(level_high / (self._peak_high + 1e-6), 0.0, 1.0)
            shaped2 = norm2**self.gamma
            target_b2 = int(self.min_b + shaped2 * (self.max_b - self.min_b))

        delta2 = np.clip(target_b2 - self._prev_b2, -self.max_step, self.max_step)
        brightness2 = int(np.clip(self._prev_b2 + delta2, self.min_b, self.max_b))
        self._prev_b2 = brightness2

        return [(color1[0], color1[1], color1[2], brightness1), (color2[0], color2[1], color2[2], brightness2)]

    def map(self, bass, mids, treble, amplitude):
        colors = self.map_lights(bass, mids, treble, 1)
        return colors[0]


class TurboSpectrumGradient:
    """
    Versión 'Groove + Kick':
    - Fluye suave en las partes tranquilas.
    - Detecta el 'Estribillo' (Energía alta en Medios/Agudos) para dar un Flash.
    """
    def __init__(self, min_brightness=10, max_brightness=100, **kwargs):
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.hue_offset = 0.0
        self.last_update = time.time()
        self.smoothed_brightness = min_brightness

    def _get_rgb_brightness(self, bass, mids, treble, amp):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        # 1. MOVIMIENTO (BAILE)
        speed = 0.02 + (bass * 0.6)
        self.hue_offset += speed * dt
        if self.hue_offset > 1.0:
            self.hue_offset -= 1.0

        # 2. DEFINICIÓN DEL COLOR
        hue = self.hue_offset
        saturation = 1.0

        # 3. DETECTOR DE "ESTRIBILLO" (I'M JUST A FREAK)
        scream_energy = mids + (treble * 0.8)
        target_brightness = self.min_brightness + (amp * (self.max_brightness - self.min_brightness))

        if scream_energy > 0.8:
            target_brightness = target_brightness * 1.5
            saturation = 0.6
            self.hue_offset += 0.05

        target_brightness = min(target_brightness, 255)

        if target_brightness > self.smoothed_brightness:
            alpha = 0.3
        else:
            alpha = 0.1

        self.smoothed_brightness = (self.smoothed_brightness * (1-alpha)) + (target_brightness * alpha)
        final_brightness = int(self.smoothed_brightness)

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1.0)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)

        return r, g, b, final_brightness

    def map(self, bass, mids, treble, amp):
        r, g, b, bri = self._get_rgb_brightness(bass, mids, treble, amp)
        return [r, g, b, bri]

    def map_lights(self, bass, mids, treble, num_lights):
        colors = []
        r, g, b, bri = self._get_rgb_brightness(bass, mids, treble, (bass+mids+treble)/3)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

        for i in range(num_lights):
            local_h = h + (i * 0.05)
            if local_h > 1.0: local_h -= 1.0

            lr, lg, lb = colorsys.hsv_to_rgb(local_h, s, v)
            colors.append([int(lr*255), int(lg*255), int(lb*255), bri])

        return colors