from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify
from flask_bootstrap import Bootstrap
import os
from services.api_service import ApiService
from services.validacion_acceso import validar_acceso

from config import config

app = Flask(__name__)
app.config.from_object(config[os.getenv("FLASK_ENV", "development")])
Bootstrap(app)

# Inicializa ApiService para conectar con la API externa
api_service = ApiService(app.config["API_BASE_URL"])

# Ruta principal
@app.route("/")
def index():
    return render_template("index.html")

# Ruta de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        datos = request.json  # Obtener el correo y contraseña del cliente
        correo = datos.get("Correo")
        contrasena = datos.get("Contrasena")

        # Realiza la verificación contra la API externa
        try:
            respuesta = api_service.post("proyecto/usuario/verificar-contrasena", {
                "campoUsuario": "email",
                "campoContrasena": "contrasena",
                "valorUsuario": correo,
                "valorContrasena": contrasena
            })
            if respuesta["success"]:
                # Si la verificación es exitosa, guarda el usuario en la sesión
                session["usuarioEmail"] = correo
                session["rutas_permitidas"] = ["/dashboard", "/weather", "/persona", "/list-table"]
                
                # Aquí podrías realizar una solicitud adicional para obtener roles y rutas específicas del usuario

                flash("Inicio de sesión exitoso", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Usuario o contraseña incorrectos.", "danger")
                return redirect(url_for("login"))
        except Exception as e:
            flash("Error al iniciar sesión. Intenta nuevamente.", "danger")
            return redirect(url_for("login"))

    # GET request, renderiza el formulario de login
    return render_template("login.html")

# Ruta de cierre de sesión
@app.route("/logout")
def logout():
    # Limpiar la sesión del usuario
    session.clear()
    
    # Redirigir al usuario a la página de login con un mensaje de confirmación
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("login"))

# Ruta protegida del dashboard
@app.route("/dashboard")
@validar_acceso("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Ruta para la página de clima
@app.route("/weather")
@validar_acceso("/weather")
def weather():
    return render_template("weather.html")

# API para obtener datos del clima desde la API externa
@app.route("/api/weather")
def get_weather_data():
    try:
        weather_data = api_service.get("weather")
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Página para gestionar personas
@app.route("/persona")
@validar_acceso("/persona")
def persona():
    return render_template("persona.html")

# Endpoint para obtener todas las personas usando la API externa
@app.route("/api/personas", methods=["GET"])
def obtener_personas():
    try:
        personas = api_service.get("proyecto/persona")
        return jsonify(personas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para agregar una nueva persona usando la API externa
@app.route("/api/personas", methods=["POST"])
def agregar_persona():
    nueva_persona = request.json
    try:
        response = api_service.post("proyecto/persona", nueva_persona)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para actualizar una persona usando la API externa
@app.route("/api/personas/<codigo>", methods=["PUT"])
def actualizar_persona(codigo):
    persona_actualizada = request.json
    try:
        response = api_service.put(f"proyecto/persona/{codigo}", persona_actualizada)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para eliminar una persona usando la API externa
@app.route("/api/personas/<codigo>", methods=["DELETE"])
def eliminar_persona(codigo):
    try:
        response = api_service.delete(f"proyecto/persona/{codigo}")
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para la página de listado de datos
@app.route("/list-table")
@validar_acceso("/list-table")
def list_table():
    return render_template("list_table.html")

# Endpoint para obtener los datos de la lista desde la API externa
@app.route("/api/list-data", methods=["GET"])
def obtener_datos_lista():
    try:
        data = api_service.get("proyecto/persona")  # Reemplaza con el endpoint correcto
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta dinámica para cargar diferentes páginas
@app.route("/<path:page>")
def render_page(page):
    try:
        return render_template(f"{page}.html")
    except:
        return render_template("404.html"), 404

# Manejador de error 404 global
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
