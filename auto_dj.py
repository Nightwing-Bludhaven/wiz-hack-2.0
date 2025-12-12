import sys
import os
import time
import numpy as np
import soundfile as sf
import subprocess
from i18n_manager import t  # Importamos el gestor de idiomas

# --- INICIO DEL PROGRAMA ---
os.system('cls' if os.name == 'nt' else 'clear')

print(t("system_ready"))

# Verificamos si hay archivo
if len(sys.argv) < 2:
    print(t("error_no_file"))
    print(t("usage_hint"))
    sys.exit()

ruta_archivo = sys.argv[1].replace('"', '')
nombre_archivo = os.path.basename(ruta_archivo)

print(t("analyzing", nombre_archivo))

# --- LECTURA Y CÁLCULO ---
print(t("reading_data"))
try:
    data, samplerate = sf.read(ruta_archivo)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit()

# Convertir a Mono si es necesario
if len(data.shape) > 1:
    data = np.mean(data, axis=1)

# Calcular RMS
rms = np.sqrt(np.mean(data**2))
print(t("energy_detected", rms))

# --- LÓGICA DE AUTO-DJ ---
sensibilidad_base = 0.16 / (rms + 0.001)
sensibilidad_final = np.clip(sensibilidad_base, 0.5, 3.8)

# Configuración por defecto
boost_brillo = 1.0
smoothing = "0.2"
tipo = "Standard"

if rms < 0.05: 
    tipo = t("genre_ambient")
    boost_brillo = 2.5
    smoothing = "0.3"
elif rms < 0.10:
    tipo = t("genre_dynamic")
    boost_brillo = 1.6
    smoothing = "0.25"
elif rms > 0.22:
    tipo = t("genre_metal")
    boost_brillo = 0.9
    smoothing = "0.15"
else:
    tipo = t("genre_rock")
    boost_brillo = 1.2
    smoothing = "0.2"

print("-" * 50)
print(f"🎹 {tipo}")
print(t("suggestion", sensibilidad_final, boost_brillo))
print("-" * 50)

# --- EJECUCIÓN ---
print(t("press_enter"))
input(">> ") 

print(t("launching"))
comando = [
    sys.executable, "music_visualizer.py",
    "--file", ruta_archivo,
    "--mode", "spectrum_pulse",
    "--sensitivity", str(round(sensibilidad_final, 2)),
    "--brightness-boost", str(boost_brillo),
    "--smoothing", str(smoothing)
]

subprocess.call(comando)
