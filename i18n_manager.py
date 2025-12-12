"""
Internationalization Manager (i18n)
Detects system locale and serves the appropriate language strings.
"""
import locale
import os
import sys

# Dictionary of all texts in the app
# Structure: "key": {"en": "English Text", "es": "Texto en Español"}
TRANSLATIONS = {
    # --- COMMON ---
    "system_ready": {
        "en": "✅ 1. System ready. Libraries loaded.",
        "es": "✅ 1. Sistema listo. Librerías cargadas."
    },
    "error_no_file": {
        "en": "\n❌ ERROR: No file provided.",
        "es": "\n❌ ERROR: No arrastraste ninguna canción."
    },
    "usage_hint": {
        "en": "👉 Usage: Type 'python auto_dj.py', space, then drag & drop a file.",
        "es": "👉 Uso: Escribe 'python auto_dj.py', da un espacio y arrastra la canción."
    },
    "analyzing": {
        "en": "💿 2. Analyzing file: {}",
        "es": "💿 2. Analizando archivo: {}"
    },
    "reading_data": {
        "en": "⏳ 3. Reading audio data (fast)...",
        "es": "⏳ 3. Leyendo datos de audio (esto es rápido)..."
    },
    "energy_detected": {
        "en": "📊 4. Energy detected (RMS): {:.5f}",
        "es": "📊 4. Energía detectada (RMS): {:.5f}"
    },
    "launching": {
        "en": "🚀 Launching visualizer...",
        "es": "🚀 Lanzando visualizador..."
    },
    "press_enter": {
        "en": "\nLaunch lights? (Press ENTER for YES, close window for NO)",
        "es": "\n¿Lanzar luces? (Presiona ENTER para SÍ, o cierra la ventana para NO)"
    },
    
    # --- GENRES (AUTO DJ) ---
    "genre_ambient": {"en": "Very Soft / Ambient", "es": "Muy Suave / Ambiental"},
    "genre_dynamic": {"en": "Dynamic / Pop / Jazz", "es": "Dinámica / Pop / Jazz"},
    "genre_metal":   {"en": "Very Loud / Metal / EDM", "es": "Muy Fuerte / Metal / EDM"},
    "genre_rock":    {"en": "Rock / Modern Pop", "es": "Rock / Pop Moderno"},
    "suggestion":    {"en": "🤖 SUGGESTION: Sensitivity={:.2f} | Brightness={}x", "es": "🤖 SUGERENCIA: Sensibilidad={:.2f} | Brillo={}x"},

    # --- TIDAL / REALTIME ---
    "waiting_tidal": {"en": "Waiting for Tidal...", "es": "Esperando Tidal..."},
    "speaker_detected": {"en": "🎧 Speaker detected: {}", "es": "🎧 Altavoz detectado: {}"},
    "loopback_connected": {"en": "🎤 Loopback connected: {}", "es": "🎤 Loopback conectado: {}"},
    "server_active": {"en": "🌐 Plugin Server active on port 5000", "es": "🌐 Servidor de Plugin activo en puerto 5000"},
    "press_ctrl_c": {"en": "\n[Press Ctrl+C to stop]", "es": "\n[Presiona Ctrl+C para detener]"},
    "mode_change": {"en": "🤖 Mode Switch: {} (Crest: {:.2f})", "es": "🤖 Cambio de Modo: {} (Crest: {:.2f})"},
    "system_stopped": {"en": "\n👋 System stopped.", "es": "\n👋 Sistema detenido."},
    "searching_lights": {"en": "🔍 Searching for Wiz lights...", "es": "🔍 Buscando luces Wiz..."},
    "lights_connected": {"en": "✅ Connected to {} lights.", "es": "✅ Conectado a {} luces."},
    "advice_music": {"en": "💡 Tip: Make sure music is playing.", "es": "💡 Consejo: Asegúrate de tener música sonando."},

    # --- AUTO DJ SMART ---
    "file_label": {"en": "📂 File: {}", "es": "📂 Archivo: {}"},
    "consulting_lastfm": {"en": "🌍 Consulting Last.fm (Visual)...", "es": "🌍 Consultando Last.fm (Visual)..."},
    "scanning_audio": {"en": "\n⏳ Scanning Audio (Finding Climax & Dynamics)...", "es": "\n⏳ Escaneando Audio (Buscando Clímax & Dinámica)..."},
    "genre_unknown": {"en": "Unknown Genre", "es": "Género Desconocido"},
    "scanner_result": {"en": "🧬 SCANNER:    Climax at {:.1f}s | Crest Factor={:.1f}", "es": "🧬 ESCÁNER:    Clímax en {:.1f}s | Crest Factor={:.1f}"},
    "mode_switching": {"en": "👁️  MODE:       SWITCHING TO '{}'", "es": "👁️  MODO:       CAMBIANDO A '{}'"},
    "reason": {"en": "🤖 REASON:     {}", "es": "🤖 MOTIVO:     {}"},
    "reason_bass": {"en": "Bass Dominant (>40%)", "es": "Dominante en Bajos (>40%)"},
    "reason_punch": {"en": "Rhythmic Punch (Crest {:.1f} > 3.0)", "es": "Golpe Rítmico (Crest {:.1f} > 3.0)"},
    "reason_wall": {"en": "Dynamic / Wall (Crest {:.1f})", "es": "Dinámica / Muro (Crest {:.1f})"},
    "tuned_analysis": {"en": "Tuned Analysis", "es": "Análisis Ajustado"},
    "autodj_stopped": {"en": "\n\n👋 Auto DJ stopped.", "es": "\n\n👋 Auto DJ detenido correctamente."},
}

def get_system_language():
    """Detects system language, defaults to 'en'."""
    try:
        # Get default locale (e.g., ('es_ES', 'cp1252'))
        lang_code = locale.getdefaultlocale()[0]
        if lang_code and 'es' in lang_code.lower():
            return 'es'
        return 'en'
    except:
        return 'en'

# Global variable to store detected language
CURRENT_LANG = get_system_language()

def t(key, *args):
    """
    Translates a key to the current system language.
    Supports format arguments (like .format()).
    """
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(CURRENT_LANG, entry.get("en", key))
    
    if args:
        try:
            return text.format(*args)
        except:
            return text
    return text
