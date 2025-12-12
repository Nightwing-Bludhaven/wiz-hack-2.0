import sys
import os
import time
import numpy as np
import soundfile as sf
import subprocess
import requests
import re 
from i18n_manager import t

# --- CONFIGURACIÓN ---
# SECURITY PATCH: Usamos variables de entorno o un placeholder seguro
API_KEY = os.getenv("YOUR_LASTFM_API_KEY_HERE")
API_URL = "https://ws.audioscrobbler.com/2.0/"

# Limpiar consola
os.system('cls' if os.name == 'nt' else 'clear')
print("✅ Auto DJ Smart System")

if len(sys.argv) < 2:
    print(t("error_no_file"))
    time.sleep(3)
    sys.exit()

ruta_archivo = sys.argv[1].replace('"', '')
nombre_archivo = os.path.basename(ruta_archivo)

# --- 1. DATOS DE CANCIÓN ---
artista = ""
cancion = nombre_archivo
try:
    nombre_limpio = os.path.splitext(nombre_archivo)[0]
    partes = nombre_limpio.split(' - ')
    if len(partes) >= 2:
        artista = partes[0].strip()
        raw_cancion = partes[-1].strip()
        cancion = re.sub(r" ?\([^)]+\)", "", raw_cancion)
        cancion = re.sub(r" ?\[[^\]]+\]", "", cancion).strip()
except:
    pass

print(t("file_label", cancion))

# --- 2. LAST.FM (SOLO INFO VISUAL) ---
genero_bonito = "..."
if artista and API_KEY != "YOUR_LASTFM_API_KEY_HERE":
    print(t("consulting_lastfm"))
    tags_encontrados = []
    # (Lógica de requests simplificada para brevedad, misma funcionalidad)
    for q in [cancion, cancion.lower()]:
        try:
            url = f"{API_URL}?method=track.getInfo&api_key={API_KEY}&artist={artista}&track={q}&autocorrect=1&format=json"
            data = requests.get(url, timeout=1.5).json()
            if 'track' in data and 'toptags' in data['track']:
                tags = [tag['name'].title() for tag in data['track']['toptags']['tag']]
                tags = [tag for tag in tags if "Live" not in tag]
                if tags: tags_encontrados = tags; break
        except: continue
    
    if not tags_encontrados:
        try:
            url = f"{API_URL}?method=artist.getTopTags&api_key={API_KEY}&artist={artista}&autocorrect=1&format=json"
            data = requests.get(url, timeout=1.5).json()
            if 'toptags' in data: tags_encontrados = [tag['name'].title() for tag in data['toptags']['tag']]
        except: pass
            
    if tags_encontrados: genero_bonito = ", ".join(tags_encontrados[:2])
    else: genero_bonito = t("genre_unknown")
else:
    genero_bonito = "Offline / No API Key"

# --- 3. ESCÁNER TOTAL ---
print(t("scanning_audio"))

try:
    data, samplerate = sf.read(ruta_archivo)
    if len(data.shape) > 1: audio_mono = np.mean(data, axis=1)
    else: audio_mono = data
    
    peak_index = np.argmax(np.abs(audio_mono))
    start = max(0, peak_index - samplerate) 
    end = min(len(audio_mono), peak_index + samplerate) 
    chunk = audio_mono[start:end] 
    
    rms_global = np.sqrt(np.mean(audio_mono**2))
    
    if len(chunk) > 0:
        spectrum = np.fft.rfft(chunk) 
        freqs = np.fft.rfftfreq(len(chunk), 1/samplerate)
        
        bass_spectrum = np.copy(spectrum)
        bass_spectrum[freqs > 150] = 0 
        bass_waveform = np.fft.irfft(bass_spectrum)
        
        peak_bass = np.max(np.abs(bass_waveform))
        rms_bass = np.sqrt(np.mean(bass_waveform**2))
        crest_factor = peak_bass / (rms_bass + 0.0001)
        
        energy_bass = np.sum(np.abs(spectrum[np.where(freqs <= 150)]))
        total_energy = np.sum(np.abs(spectrum))
        bass_ratio = energy_bass / (total_energy + 0.001)

    else:
        raise Exception("Chunk vacío")

except Exception as e:
    print(f"⚠️ Warning: {e}")
    rms_global = 0.1
    crest_factor = 3.0
    bass_ratio = 0.2

# --- 4. CEREBRO DE DECISIÓN ---
sensibilidad = 0.16 / (rms_global + 0.001)
sensibilidad = np.clip(sensibilidad, 0.5, 6.0)

modo_visual = "spectrum_pulse"
boost_brillo = 1.0
smoothing = "0.22"
tipo_info = t("tuned_analysis")

if bass_ratio > 0.40: 
    tipo_info = t("reason_bass")
    modo_visual = "spectrum_pulse"
    boost_brillo = 1.0
elif crest_factor > 3.0:
    tipo_info = t("reason_punch", crest_factor)
    modo_visual = "spectrum_pulse"
    boost_brillo = 1.1
    smoothing = "0.20"
else:
    tipo_info = t("reason_wall", crest_factor)
    modo_visual = "spectrum_gradient" 
    boost_brillo = 1.4
    sensibilidad = sensibilidad * 1.5
    smoothing = "0.10"

# --- 5. RESULTADOS ---
print("-" * 60)
print(f"🏷️  LAST.FM:    {genero_bonito}")
print(t("scanner_result", peak_index/samplerate, crest_factor))
print("-" * 60)
print(t("mode_switching", modo_visual.upper()))
print(t("reason", tipo_info))
print("-" * 60)

print(t("press_enter"))
input(">> ")

comando = [
    sys.executable, "music_visualizer.py",
    "--file", ruta_archivo,
    "--mode", modo_visual,
    "--sensitivity", str(round(sensibilidad, 2)),
    "--brightness-boost", str(boost_brillo),
    "--smoothing", smoothing
]

try:
    subprocess.call(comando)
except KeyboardInterrupt:
    print(t("autodj_stopped"))
