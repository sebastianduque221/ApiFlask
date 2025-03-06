from flask import session, redirect, url_for, flash
from functools import wraps

def validar_acceso(ruta_permitida):
    """Decorador para validar el acceso del usuario a una ruta específica."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar si el usuario está logueado
            usuario_email = session.get("usuarioEmail")
            rutas_permitidas = session.get("rutas_permitidas", [])

            # Permitir acceso sin restricciones a la página de login
            if ruta_permitida == "/login":
                return func(*args, **kwargs)

            # Si el usuario no está logueado, redirigir a login
            if not usuario_email:
                flash("Sesión no válida. Redirigiendo al login...", "error")
                return redirect(url_for("login"))

            # Verificar si la ruta actual está en las rutas permitidas
            if ruta_permitida not in rutas_permitidas:
                flash("No tienes permisos para acceder a esta página", "error")
                return redirect(url_for("index"))

            # Si todo está correcto, permitir el acceso
            return func(*args, **kwargs)
        return wrapper
    return decorator
