import requests
import sys

# --- PEGA TU CLAVE AQUÍ ---
API_KEY = "5bd0b11fc68375c4757413419c1d156c" 
# Ejemplo: API_KEY = "3b4c5d6e7f8g9h0i..."
# ---------------------------

print("🔍 PROBANDO CONEXIÓN A LAST.FM...")

if API_KEY == "PEGAR_TU_CLAVE_AQUI" or API_KEY == "TU_API_KEY_AQUI":
    print("❌ ERROR: Aún no has puesto la API Key en el código.")
    print("Edita este archivo y pon tu clave en la línea 5.")
    sys.exit()

try:
    # Probamos con una canción famosa que seguro existe
    params = {
        'method': 'track.getInfo',
        'api_key': API_KEY,
        'artist': 'Queen',
        'track': 'Bohemian Rhapsody',
        'format': 'json'
    }
    
    response = requests.get("https://ws.audioscrobbler.com/2.0/", params=params, timeout=5)
    data = response.json()

    # Análisis de respuesta
    if response.status_code == 200 and 'track' in data:
        print("✅ ¡ÉXITO! Tu API Key funciona perfectamente.")
        print(f"Canción detectada: {data['track']['name']} - {data['track']['artist']['name']}")
        tags = [t['name'] for t in data['track']['toptags']['tag']]
        print(f"Tags recibidos: {', '.join(tags[:3])}")
        print("\n👉 SOLUCIÓN: Copia tu API_KEY y pégala en la línea 12 de 'auto_dj_smart.py'")
    
    elif 'error' in data:
        print(f"❌ ERROR DE LAST.FM (Código {data['error']}):")
        print(f"Mensaje: {data['message']}")
        if data['error'] == 10:
            print("💡 Pista: Tu API Key es inválida. Copiala de nuevo con cuidado.")
    
    else:
        print(f"⚠️ Respuesta extraña: {response.status_code}")
        print(data)

except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: {e}")
    print("Revisa tu internet o si algún firewall bloquea Python.")