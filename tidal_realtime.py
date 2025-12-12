#!/usr/bin/env python3
"""
TIDAL/SYSTEM REAL-TIME VISUALIZER (WASAPI LOOPBACK)
"""

import soundcard as sc
import numpy as np
import time
import threading
import queue
import logging
import warnings
import sys
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, make_response
from i18n_manager import t

# --- SILENCIADOR DE ERRORES ---
warnings.filterwarnings("ignore", module="soundcard")
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from wiz_control import WizLight
from color_mapping import (
    SpectrumPulseMapper,
    TurboSpectrumGradient
)

# --- CONFIGURACIÓN ---
SAMPLE_RATE = 44100
CHUNK_SIZE = 4096
THROTTLE_TIME = 0.035
SILENCE_THRESHOLD = 0.005 

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tidal_realtime")

app = Flask(__name__)
track_info = {"artist": "?", "track": t("waiting_tidal")}

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://desktop.tidal.com'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

@app.route('/update_track', methods=['POST', 'OPTIONS'])
def receive_track_info():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response())

    global track_info
    try:
        data = request.json
        track_info['artist'] = data.get('artist', 'Desconocido')
        track_info['track'] = data.get('track', 'Desconocido')
    except Exception:
        pass
        
    response = make_response("OK")
    return add_cors_headers(response)

def run_server():
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error: {e}")

class RealTimeVisualizer:
    def __init__(self, light_ips):
        self.light_ips = light_ips
        self.lights = [WizLight(ip) for ip in light_ips]
        
        self.current_mode = "spectrum_gradient"
        self.crest_factor_history = []
        self.last_mode_switch = time.time()
        self.is_silent = False 
        
        self.mappers = {
            "spectrum_pulse": SpectrumPulseMapper(brightness_emphasis=1.5, sensitivity=1.0),
            "spectrum_gradient": TurboSpectrumGradient(min_brightness=10, max_brightness=100)
        }
        
        self._executor = ThreadPoolExecutor(max_workers=len(self.lights))
        self._last_update = 0
        self.running = True

    def _auto_dj_logic(self, audio_chunk):
        spectrum = np.fft.rfft(audio_chunk)
        freqs = np.fft.rfftfreq(len(audio_chunk), 1/SAMPLE_RATE)
        
        bass_spectrum = np.copy(spectrum)
        bass_spectrum[freqs > 150] = 0
        bass_waveform = np.fft.irfft(bass_spectrum)
        
        peak = np.max(np.abs(bass_waveform))
        rms = np.sqrt(np.mean(bass_waveform**2))
        crest = peak / (rms + 0.0001)
        
        self.crest_factor_history.append(crest)
        if len(self.crest_factor_history) > 40:
            self.crest_factor_history.pop(0)
            
        if time.time() - self.last_mode_switch > 3.0:
            avg_crest = sum(self.crest_factor_history) / len(self.crest_factor_history)
            
            new_mode = self.current_mode
            if avg_crest > 3.0: 
                new_mode = "spectrum_pulse"
            elif avg_crest < 2.8: 
                new_mode = "spectrum_gradient"
                
            if new_mode != self.current_mode:
                print(f"\n✨ {track_info['track']} by {track_info['artist']}")
                print(t("mode_change", new_mode.upper(), avg_crest))
                self.current_mode = new_mode
                self.last_mode_switch = time.time()

    def _process_audio(self, audio_chunk):
        mono_chunk = np.mean(audio_chunk, axis=1)
        rms_amplitude = np.sqrt(np.mean(mono_chunk**2))
        
        if rms_amplitude < SILENCE_THRESHOLD:
            if not self.is_silent:
                self._send_colors((0, 0, 0, 0))
                self.is_silent = True
            return
        
        self.is_silent = False 
        self._auto_dj_logic(mono_chunk)
        
        fft_data = np.abs(np.fft.rfft(mono_chunk))
        freqs = np.fft.rfftfreq(len(mono_chunk), 1/SAMPLE_RATE)
        
        bass = np.sum(fft_data[np.where((freqs >= 20) & (freqs <= 150))])
        mids = np.sum(fft_data[np.where((freqs > 150) & (freqs <= 4000))])
        treble = np.sum(fft_data[np.where((freqs > 4000))])
        
        scale = 1.0 / (np.max(fft_data) + 10) 
        b_val = min(bass * scale * 2.0, 1.0)
        m_val = min(mids * scale * 2.0, 1.0)
        t_val = min(treble * scale * 2.0, 1.0)
        amp_val = rms_amplitude * 5.0
        
        mapper = self.mappers.get(self.current_mode, self.mappers["spectrum_gradient"])
        
        if hasattr(mapper, "map_lights"):
            colors = mapper.map_lights(b_val, m_val, t_val, len(self.lights))
        else:
            colors = mapper.map(b_val, m_val, t_val, amp_val)
            
        now = time.time()
        if now - self._last_update >= THROTTLE_TIME:
            self._send_colors(colors)
            self._last_update = now

    def _send_colors(self, colors):
        def send(light, c):
            try:
                if isinstance(c, (list, tuple)) and len(c) == 4:
                    light.set_color(*c)
            except: pass

        if isinstance(colors, list) and len(colors) == len(self.lights):
            for i, light in enumerate(self.lights):
                self._executor.submit(send, light, colors[i])
        else:
            c = colors[0] if isinstance(colors, list) else colors
            for light in self.lights:
                self._executor.submit(send, light, c)

    def start(self):
        try:
            default_speaker = sc.default_speaker()
            print(t("speaker_detected", default_speaker.name))
            
            loopback_mic = sc.get_microphone(id=str(default_speaker.id), include_loopback=True)
            print(t("loopback_connected", loopback_mic.name))
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            print(t("server_active"))
            print(t("press_ctrl_c"))

            with loopback_mic.recorder(samplerate=SAMPLE_RATE) as mic:
                while self.running:
                    data = mic.record(numframes=CHUNK_SIZE)
                    self._process_audio(data)
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(f"Error: {e}")
            print(t("advice_music"))
        finally:
            self.stop()

    def stop(self):
        self.running = False
        self._executor.shutdown(wait=False)
        print(t("system_stopped"))

def discover_lights():
    print(t("searching_lights"))
    wiz = WizLight()
    lights = wiz.discover()
    if not lights: return []
    return [l["ip"] for l in lights]

if __name__ == "__main__":
    ips = discover_lights()
    if not ips:
        sys.exit(1)
        
    print(t("lights_connected", len(ips)))
    viz = RealTimeVisualizer(ips)
    viz.start()
