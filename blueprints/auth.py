# blueprints/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import pytz
import secrets
import re

# Importamos modelos y la base de datos
from models import db, Usuario, Rol

# Importamos nuestras utilidades desde el paquete utils
from utils import registrar_log, enviar_correo_reseteo

# Definimos el Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# --- VALIDACIONES LOCALES ---
def es_password_segura(password):
    """
    Valida que la contraseña tenga:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos un número
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password): 
        return False
    if not re.search(r"[0-9]", password): 
        return False
    return True

def obtener_ruta_redireccion(usuario):
    """Define a dónde va el usuario después de loguearse según su Rol."""
    if not usuario.rol:
        return url_for('auth.login')
    
    nombre_rol = usuario.rol.nombre
    
    if nombre_rol == "Admin":
        # Aún no creamos admin_bp, pero apuntamos allá
        return url_for('admin.panel') 
    elif nombre_rol == "Gestor":
        # Aún no creamos inventario_bp, pero apuntamos allá
        return url_for('inventario.panel') 
    else:
        # Por defecto
        return url_for('auth.login')

# --- RUTAS DE AUTENTICACIÓN ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está logueado, lo mandamos a su panel
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscamos el usuario en la BD
        usuario = Usuario.query.filter_by(email=email).first()

        # Verificaciones
        if usuario:
            # Validar si está activo
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Validar contraseña
            if usuario.check_password(password):
                login_user(usuario)
                
                # Registramos el evento
                registrar_log("Inicio de Sesión", f"Usuario {usuario.nombre_completo} inició sesión.")

                # Verificar si requiere cambio de clave obligatorio
                if usuario.cambio_clave_requerido:
                    return redirect(url_for('auth.cambiar_clave'))
                
                flash(f'Bienvenido, {usuario.nombre_completo}', 'success')
                return redirect(obtener_ruta_redireccion(usuario))
        
        # Si falla algo
        flash('Correo o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    registrar_log("Cierre de Sesión", f"Usuario {current_user.nombre_completo} cerró sesión.")
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))

# --- GESTIÓN DE CONTRASEÑAS ---

@auth_bp.route('/cambiar_clave', methods=['GET', 'POST'])
@login_required
def cambiar_clave():
    # Solo permitimos entrar aquí si el flag está activo
    if not current_user.cambio_clave_requerido:
        return redirect(obtener_ruta_redireccion(current_user))
        
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')

        if not es_password_segura(nueva_password):
            flash('Error: La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.', 'danger')
            return render_template('auth/cambiar_clave.html')
        
        current_user.set_password(nueva_password)
        current_user.cambio_clave_requerido = False
        db.session.commit()
        
        registrar_log("Cambio de Clave", "El usuario actualizó su contraseña obligatoria.")
        
        logout_user()
        flash('Contraseña actualizada. Por favor, inicia sesión de nuevo.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/cambiar_clave.html')

@auth_bp.route('/solicitar-reseteo', methods=['GET', 'POST'])
def solicitar_reseteo():
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    if request.method == 'POST':
        email = request.form.get('email')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            token = secrets.token_hex(16)
            
            # Hora Chile para expiración (1 hora)
            chile_tz = pytz.timezone('America/Santiago')
            ahora_chile = datetime.now(chile_tz).replace(tzinfo=None)
            expiracion = ahora_chile + timedelta(hours=1)
            
            usuario.reset_token = token
            usuario.reset_token_expiracion = expiracion
            db.session.commit()
            
            enviar_correo_reseteo(usuario, token)
            
            flash(f'Se ha enviado un enlace a {email}. Revisa tu bandeja.', 'success')
        else:
            # Por seguridad, a veces es mejor no decir si existe o no, 
            # pero para uso interno/corporativo es útil avisar.
            flash(f'El correo {email} no está registrado en el sistema.', 'danger')
            
        return redirect(url_for('auth.login'))
        
    return render_template('auth/solicitar_reseteo.html')

@auth_bp.route('/resetear-clave/<token>', methods=['GET', 'POST'])
def resetear_clave(token):
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    usuario = Usuario.query.filter_by(reset_token=token).first()
    
    # Validar Token
    chile_tz = pytz.timezone('America/Santiago')
    ahora_chile = datetime.now(chile_tz).replace(tzinfo=None)
    
    if not usuario or not usuario.reset_token_expiracion or usuario.reset_token_expiracion < ahora_chile:
        flash('El enlace es inválido o ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.solicitar_reseteo'))
        
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')

        if not es_password_segura(nueva_password):
            flash('Error: La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.', 'danger')
            return render_template('auth/resetear_clave.html')
        
        usuario.set_password(nueva_password)
        usuario.reset_token = None
        usuario.reset_token_expiracion = None
        db.session.commit()
        
        registrar_log("Recuperación Clave", f"El usuario {usuario.nombre_completo} reseteó su clave vía correo.")
        
        flash('Tu contraseña ha sido restablecida. Inicia sesión.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/resetear_clave.html')