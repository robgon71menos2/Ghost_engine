import json
import os

def build_bridge(niche, affiliate_url):
    # Definir rutas absolutas basadas en la ubicación de este script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    
    template_path = os.path.join(ROOT_DIR, "templates", "ultra_fast_bridge.html")
    dist_dir = os.path.join(ROOT_DIR, "dist")
    
    if not os.path.exists(template_path):
        print(f"❌ Error: No se encuentra la plantilla en {template_path}")
        return

    with open(template_path, "r") as f:
        html_content = f.read()

    final_html = html_content.replace("{{OFFER_LINK}}", affiliate_url)
    
    os.makedirs(dist_dir, exist_ok=True)
    
    with open(os.path.join(dist_dir, "index.html"), "w") as f:
        f.write(final_html)
    print(f"✅ Landing generada con éxito en: {dist_dir}/index.html")

if __name__ == "__main__":
    # Cargar ofertas desde su ubicación real
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE_DIR, "offers.json"), "r") as f:
        offers = json.load(f)
    
    build_bridge("tech", offers["tech"])