from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def check_password_change(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.cambio_clave_requerido:
            flash('Por seguridad, debes cambiar tu contraseña antes de continuar.', 'warning')
            return redirect(url_for('auth.cambiar_clave'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol.nombre != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def gestor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permite acceso si es Admin O Gestor
        if not current_user.is_authenticated or current_user.rol.nombre not in ['Admin', 'Gestor']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function