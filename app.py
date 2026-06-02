from flask import Flask, request
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "datos_recolectados.json"
ADMIN_KEY = "miclase2026"

# Página que pide permiso de cámara y micrófono
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo Infostealer - Acceso a Cámara/Mic</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #0a0e1a;
            color: #00ffcc;
            text-align: center;
            margin-top: 10%;
        }
        h1 { font-size: 2.5em; }
        p { font-size: 1.2em; }
        button {
            background: #00ffcc;
            color: #0a0e1a;
            padding: 15px 30px;
            font-size: 1.2em;
            border: none;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover {
            background: #0a0e1a;
            color: #00ffcc;
            border: 1px solid #00ffcc;
        }
    </style>
</head>
<body>
    <h1>🎥 VERIFICACIÓN DE SEGURIDAD</h1>
    <p>Para continuar con la presentación interactiva, debes habilitar cámara y micrófono.</p>
    <button id="solicitarPermiso">Habilitar cámara y micrófono</button>
    <p id="estado" style="margin-top: 20px; font-size: 0.9em;"></p>
    <script>
        document.getElementById('solicitarPermiso').addEventListener('click', async () => {
            const estadoDiv = document.getElementById('estado');
            estadoDiv.innerHTML = 'Solicitando permisos...';
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                estadoDiv.innerHTML = '✅ Permisos concedidos. Ahora puedes seguir la presentación.';
                // Opcional: detener el stream después de un momento
                setTimeout(() => {
                    stream.getTracks().forEach(track => track.stop());
                    estadoDiv.innerHTML += ' (Los permisos han sido liberados por seguridad).';
                }, 3000);
                // Enviar notificación al servidor de que se concedieron permisos
                fetch('/registrar_permiso', { method: 'POST' });
            } catch (err) {
                estadoDiv.innerHTML = '❌ Permiso denegado o error: ' + err.message;
                fetch('/registrar_permiso_denegado', { method: 'POST' });
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    datos = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)

    # Registramos la visita aunque no haya concedido permiso aún
    datos.append({
        "hora": hora,
        "ip": ip,
        "navegador": user_agent[:100],
        "permiso": "Pendiente"
    })

    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=4)

    print(f"[!] Capturado: {ip} - {hora}")

    return LANDING_PAGE

@app.route('/registrar_permiso', methods=['POST'])
def registrar_permiso():
    ip = request.remote_addr
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        # Actualizar el último registro del usuario (por IP)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["permiso"] = "Concedido"
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return "OK", 200

@app.route('/registrar_permiso_denegado', methods=['POST'])
def registrar_permiso_denegado():
    ip = request.remote_addr
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["permiso"] = "Denegado"
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return "OK", 200

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
    html += "<tr><th>Hora</th><th>IP</th><th>Navegador/Dispositivo</th><th>Permiso Cámara/Mic</th></tr>"
    for d in datos:
        html += f"<tr><td>{d['hora']}</td><td>{d['ip']}</td><td>{d['navegador']}</td><td>{d.get('permiso', 'No solicitado')}</td></tr>"
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
        os.remove(DATA_FILE)
    app.run(host='0.0.0.0', port=5000)
