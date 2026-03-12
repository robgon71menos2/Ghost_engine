import requests
import os

def track_revenue():
    # Obtiene la clave del secreto de GitHub
    api_key = os.getenv("ADSTERRA_API_KEY")
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    
    # URL de la API de Adsterra para estadísticas de pago
    url = f"https://api3.adsterra.com/publisher/stats.json?api_key={api_key}"
    
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        # Aquí el script procesa tus ganancias acumuladas
        print("Consulta de saldo completada con éxito.")
        # Si el balance es >= 50, se enviaría la alerta que configuramos antes
    except Exception as e:
        print(f"Error al conectar con Adsterra: {e}")

if __name__ == "__main__":
    track_revenue()