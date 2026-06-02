from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "datos_recolectados.json"
ADMIN_KEY = "miclase2026"  # Cámbiala

# Página simple que se muestra al escanear el QR (solo mensaje, sin pedir nada)
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo Infostealer</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e1a;
            color: #00ffcc;
            text-align: center;
            margin-top: 20%;
        }
        h1 { font-size: 2.5em; }
        p { font-size: 1.2em; }
    </style>
</head>
<body>
    <h1>🛸 BIENVENIDO A LA EXPOSICIÓN DE INFOSTEALER</h1>
    <p>Tus datos han sido capturados automáticamente con fines educativos.</p>
    <p><small>No te preocupes, es una simulación controlada.</small></p>
    <script>
        // Opcional: mostrar un mensaje adicional en consola
        console.log("Demo Infostealer - Captura automática");
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Capturar datos automáticamente al cargar la página
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    datos = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)

    datos.append({
        "hora": hora,
        "ip": ip,
        "navegador": user_agent[:100],
        "tipo": "Escaneo QR"
    })

    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=4)

    print(f"[!] Capturado: {ip} - {hora}")

    return LANDING_PAGE

@app.route('/admin/<clave>')
def admin(clave):
    if clave != ADMIN_KEY:
        return "Acceso denegado", 403
    if not os.path.exists(DATA_FILE):
        return "<h3>No hay datos aún. Espera a que escaneen el QR.</h3>"
    with open(DATA_FILE, "r") as f:
        datos = json.load(f)
    html = "<h2>📦 Datos capturados automáticamente (simulación infostealer)</h2>"
    html += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
    html += "<tr><th>Hora</th><th>IP</th><th>Navegador/Dispositivo</th></tr>"
    for d in datos:
        html += f"<tr><td>{d['hora']}</td><td>{d['ip']}</td><td>{d['navegador']}</td></tr>"
    html += "</table><br>"
    html += "<p><a href='/borrar_datos' onclick='return confirm(\"¿Borrar todos los datos?\")'>🗑️ Borrar todos los datos (transparencia)</a></p>"
    return html

@app.route('/borrar_datos')
def borrar_datos():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return "<h3>✅ Todos los datos han sido eliminados. La simulación terminó.</h3><p><a href='/'>Volver</a></p>"

if __name__ == '__main__':
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)  # Empieza limpio
    app.run(host='0.0.0.0', port=5000)