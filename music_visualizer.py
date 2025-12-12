#!/usr/bin/env python3
"""
Music file visualizer for Wiz lights.
Plays an audio file (MP3/WAV/FLAC) while syncing lights to the music.
Perfect sync since we're analyzing the actual audio file, not mic input!

Usage:
    python music_visualizer.py --file song.mp3 [--mode MODE] [OPTIONS]
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import sys
import argparse
import time
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor

from wiz_control import WizLight
from audio_analysis import AudioAnalyzer
from color_mapping import (
    FrequencyToRGBMapper,
    MultiLightMapper,
    PulseModeMapper,
    StrobeModeMapper,
    SpectrumPulseMapper,
    SimplePulseMapper,
    StereoSplitMapper,
    ComplementaryPulseMapper,
    BeatLeaderFollowerMapper,
    FrequencyDanceMapper,
    TurboSpectrumGradient, # <--- AHORA LO IMPORTAMOS CORRECTAMENTE
)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("music_visualizer")


class MusicVisualizer:
    """Music file visualizer with perfect audio-light sync."""

    def __init__(
        self,
        audio_file,
        light_ips,
        mode="frequency_bands",
        smoothing=0.3,
        brightness_boost=1.5,
        sensitivity=1.0,
        loop=False,
    ):
        self.audio_file = audio_file
        self.light_ips = light_ips
        self.lights = [WizLight(ip) for ip in light_ips]
        self.mode = mode
        self.loop = loop
        self.running = False
        self.paused = False

        # Load audio file
        print(f"Loading audio file: {audio_file}")
        self.audio_data, self.sample_rate = sf.read(audio_file, always_2d=True)

        if self.audio_data.shape[1] > 1:
            self.audio_data = np.mean(self.audio_data, axis=1)
        else:
            self.audio_data = self.audio_data[:, 0]

        self.total_samples = len(self.audio_data)
        self.duration = self.total_samples / self.sample_rate

        print(f"✅ Loaded: {self.duration:.1f} seconds, {self.sample_rate} Hz")

        # Audio analysis
        self.analyzer = AudioAnalyzer(
            sample_rate=self.sample_rate,
            buffer_size=2048,
            smoothing=smoothing,
        )

        # Mappers
        if mode == "multi" and len(light_ips) > 1:
            self.mapper = MultiLightMapper()
        elif mode == "pulse":
            self.mapper = PulseModeMapper(sensitivity=sensitivity)
        elif mode == "strobe":
            self.mapper = StrobeModeMapper(sensitivity=sensitivity)
        elif mode == "spectrum_pulse":
            self.mapper = SpectrumPulseMapper(brightness_emphasis=brightness_boost, sensitivity=sensitivity)
        elif mode == "spectrum_pulse_v3":
            self.mapper = SimplePulseMapper(min_brightness=10, max_brightness=100, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8)
        elif mode == "stereo_split":
            self.mapper = StereoSplitMapper(min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8)
        elif mode == "complementary_pulse":
            self.mapper = ComplementaryPulseMapper(min_brightness=15, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8)
        elif mode == "beat_leader_follower":
            self.mapper = BeatLeaderFollowerMapper(min_brightness=10, max_brightness=70, peak_decay=0.985, gamma=0.7, noise_gate=0.05, max_step=15, delay_frames=4)
        elif mode == "frequency_dance":
            self.mapper = FrequencyDanceMapper(min_brightness=15, max_brightness=70, peak_decay=0.985, gamma=0.9, noise_gate=0.05, max_step=8)
        elif mode == "spectrum_gradient":
            print("🎤 Modo Groove + Vocal Kick Activado")
            self.mapper = TurboSpectrumGradient(min_brightness=10, max_brightness=100)
        else:
            self.mapper = FrequencyToRGBMapper(mode=mode, brightness_boost=brightness_boost)

        # --- Cola optimizada ---
        self.color_queue = queue.Queue(maxsize=1)

        # --- Worker thread con parada limpia ---
        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=len(self.lights))
        self.update_thread = threading.Thread(target=self._light_update_worker, daemon=False)
        self.update_thread.start()

        # --- ⭐ Tu throttle personalizado ---
        self.min_update_interval = 0.035   # ← PERFECTO para tus 2 bombillas A60 E27 8.5W
        self._last_update_time = 0.0

        self.current_position = 0
        self.current_bass = 0
        self.current_mids = 0
        self.current_treble = 0
        self.current_color = (0, 0, 0, 0)

    def _enqueue_color_replace(self, colors):
        try:
            try:
                self.color_queue.get_nowait()
            except:
                pass
            self.color_queue.put_nowait(colors)
        except:
            pass

    def _light_update_worker(self):
        try:
            while not self._stop_event.is_set():
                try:
                    colors = self.color_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                futures = []
                if isinstance(colors, list) and len(colors) == len(self.lights):
                    for light, col in zip(self.lights, colors):
                        r, g, b, bri = col
                        futures.append(self._executor.submit(self._safe_set_color, light, r, g, b, bri))
                else:
                    if isinstance(colors, list):
                        r, g, b, bri = colors[0]
                    else:
                        r, g, b, bri = colors
                    for light in self.lights:
                        futures.append(self._executor.submit(self._safe_set_color, light, r, g, b, bri))

                for f in futures:
                    try:
                        f.result(timeout=0.5)
                    except:
                        pass
        finally:
            try:
                self._executor.shutdown(wait=True)
            except:
                pass
            logger.info("Light update worker stopped")

    def _safe_set_color(self, light, r, g, b, brightness):
        try:
            light.set_color(r, g, b, brightness)
        except Exception as e:
            logger.warning(f"set_color failed for {light.ip}: {e}")

    def _process_audio_chunk(self, chunk):
        bass, mids, treble = self.analyzer.analyze(chunk)
        amplitude = self.analyzer.get_amplitude(chunk)

        self.current_bass = bass
        self.current_mids = mids
        self.current_treble = treble

        dual_modes = [
            "multi", "stereo_split", "complementary_pulse",
            "beat_leader_follower", "frequency_dance", "spectrum_gradient"
        ]

        if self.mode in dual_modes and len(self.lights) > 1:
            if hasattr(self.mapper, "map_lights"):
                colors = self.mapper.map_lights(bass, mids, treble, len(self.lights))
            else:
                colors = self.mapper.map(bass, mids, treble, amplitude)
        else:
            colors = self.mapper.map(bass, mids, treble, amplitude)

        now = time.time()
        if now - self._last_update_time >= self.min_update_interval:
            self._enqueue_color_replace(colors)
            self._last_update_time = now

        self.current_color = colors

    def _print_progress(self):
        elapsed = self.current_position / self.sample_rate
        progress = (elapsed / self.duration) * 100

        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        elapsed_str = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        total_str = f"{int(self.duration // 60)}:{int(self.duration % 60):02d}"

        bass_bar = "█" * int(self.current_bass * 10)
        mids_bar = "█" * int(self.current_mids * 10)
        treble_bar = "█" * int(self.current_treble * 10)

        try:
            brightness = 0
            cc = self.current_color
            if isinstance(cc, list):
                if len(cc) > 0 and isinstance(cc[0], (list, tuple)) and len(cc[0]) > 3:
                    brightness = int(cc[0][3])
                elif len(cc) > 3 and isinstance(cc[3], (int, float)):
                    brightness = int(cc[3])
                else:
                    first = cc[0] if len(cc) > 0 else None
                    if isinstance(first, (list, tuple)) and len(first) > 3:
                        brightness = int(first[3])
            elif isinstance(cc, (tuple,)):
                if len(cc) > 3:
                    brightness = int(cc[3])
            else:
                brightness = 0
        except Exception:
            brightness = 0

        if brightness < 0:
            brightness = 0
        if brightness > 100:
            brightness = 100

        brightness_bar = "█" * int(brightness / 10)

        RED = "\033[91m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        K = "\033[K"

        print("\033[H", end="")
        print(f"\n🎵 {CYAN}Music Visualizer{RESET}{K}")
        print(f"File: {self.audio_file}{K}")
        print(f"Mode: {self.mode}{K}")
        print(f"\n{bar} {progress:5.1f}%{K}")
        print(f"Time: {elapsed_str} / {total_str}{K}")
        print(f"\n{RED}Bass:   {bass_bar:<20}{RESET}{K}")
        print(f"{GREEN}Mids:   {mids_bar:<20}{RESET}{K}")
        print(f"{BLUE}Treble: {treble_bar:<20}{RESET}{K}")
        print(f"{YELLOW}Bright: {brightness_bar:<20} {brightness:3d}%{RESET}{K}")
        print(f"\nControls: [Space] Pause | [Q] Quit | [R] Restart{K}")

    def start(self):
        self.running = True
        self.current_position = 0

        print("\033[2J\033[?25l", end="")

        print("\n🎵 Starting playback...")
        print(f"Mode: {self.mode}")
        print(f"Lights: {len(self.lights)} connected")

        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        stream.start()

        try:
            while self.running:
                if not self.paused:
                    chunk_size = int(self.sample_rate * 0.05)
                    if self.current_position + chunk_size > self.total_samples:
                        if self.loop:
                            remaining = chunk_size - (self.total_samples - self.current_position)
                            chunk = np.concatenate([self.audio_data[self.current_position:], self.audio_data[:remaining]])
                            self.current_position = remaining
                        else:
                            chunk = self.audio_data[self.current_position:]
                            self.current_position = self.total_samples
                            arr = chunk.astype("float32")
                            if arr.ndim == 1:
                                arr = arr.reshape(-1, 1)
                            stream.write(arr)
                            self._process_audio_chunk(chunk)
                            break
                    else:
                        chunk = self.audio_data[self.current_position:self.current_position + chunk_size]
                        self.current_position += chunk_size

                    arr = chunk.astype("float32")
                    if arr.ndim == 1:
                        arr = arr.reshape(-1, 1)
                    stream.write(arr)

                    self._process_audio_chunk(chunk)
                    self._print_progress()
                else:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            try:
                self.stop()
            except:
                pass
            try:
                stream.stop()
                stream.close()
            except:
                pass
            print("\033[?25h\n\n✨ Playback stopped.")

    def stop(self):
        self.running = False
        try:
            self._stop_event.set()
            if self.update_thread.is_alive():
                self.update_thread.join(timeout=1.0)
        except:
            pass


def discover_lights():
    print("🔍 Discovering Wiz lights...")
    wiz = WizLight()
    lights = wiz.discover()

    if not lights:
        print("❌ No lights found on network!")
        return []

    print(f"✅ Found {len(lights)} light(s):")
    for i, light in enumerate(lights, 1):
        ip = light["ip"]
        state = light["response"].get("result", {}).get("state", "unknown")
        print(f"  {i}. {ip} (state: {'on' if state else 'off'})")
    return [light["ip"] for light in lights]


def main():
    parser = argparse.ArgumentParser(description="Music file visualizer for Wiz lights")
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--mode", default="frequency_bands")
    parser.add_argument("--lights", type=str, default="all")
    parser.add_argument("--smoothing", type=float, default=0.3)
    parser.add_argument("--brightness-boost", type=float, default=1.5)
    parser.add_argument("--sensitivity", type=float, default=1.0)
    parser.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    import os
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    if args.lights == "all":
        light_ips = discover_lights()
    else:
        light_ips = [ip.strip() for ip in args.lights.split(",")]
        print(f"Using lights: {', '.join(light_ips)}")

    if not light_ips:
        print("No lights to control. Exiting.")
        sys.exit(1)

    visualizer = MusicVisualizer(
        audio_file=args.file,
        light_ips=light_ips,
        mode=args.mode,
        smoothing=args.smoothing,
        brightness_boost=args.brightness_boost,
        sensitivity=args.sensitivity,
        loop=args.loop,
    )

    try:
        visualizer.start()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()