# blueprints/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Usuario, Rol, Log
from utils import registrar_log, admin_required

# Definimos el blueprint
admin_bp = Blueprint('admin', __name__, template_folder='../templates', url_prefix='/admin')

@admin_bp.route('/panel')
@login_required
@admin_required
def panel():
    # Paginación
    page = request.args.get('page', 1, type=int)
    
    # Filtros
    busqueda = request.args.get('busqueda', '')
    rol_filtro = request.args.get('rol_filtro', '')
    estado_filtro = request.args.get('estado_filtro', '')

    query = Usuario.query

    # 1. Filtro de Búsqueda
    if busqueda:
        query = query.filter(
            or_(
                Usuario.nombre_completo.ilike(f'%{busqueda}%'),
                Usuario.email.ilike(f'%{busqueda}%')
            )
        )
    
    # 2. Filtro de Rol
    if rol_filtro:
        query = query.filter(Usuario.rol_id == rol_filtro)

    # 3. Filtro de Estado
    if estado_filtro == 'activo':
        query = query.filter(Usuario.activo == True)
    elif estado_filtro == 'inactivo':
        query = query.filter(Usuario.activo == False)
    
    # Ordenar y paginar
    pagination = query.order_by(Usuario.id).paginate(page=page, per_page=10, error_out=False)
    
    # Obtener roles para el select
    roles_para_filtro = Rol.query.order_by(Rol.nombre).all()

    return render_template('admin/panel.html', 
                           pagination=pagination,
                           roles_para_filtro=roles_para_filtro,
                           busqueda=busqueda,
                           rol_filtro=rol_filtro,
                           estado_filtro=estado_filtro)

# --- CREAR USUARIO ---
@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    roles = Rol.query.order_by(Rol.nombre).all()

    if request.method == 'POST':
        nombre = request.form.get('nombre_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        rol_id = request.form.get('rol_id')
        forzar_cambio = request.form.get('forzar_cambio_clave') == '1'

        # Validación Correo
        if Usuario.query.filter_by(email=email).first():
            flash('Error: El correo ya está registrado.', 'danger')
            return render_template('admin/crear_usuario.html', roles=roles, datos_previos=request.form)

        # Crear Usuario
        nuevo_usuario = Usuario(
            nombre_completo=nombre,
            email=email,
            rol_id=rol_id,
            cambio_clave_requerido=forzar_cambio,
            activo=True
        )
        nuevo_usuario.set_password(password)
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            registrar_log("Creación Usuario", f"Admin creó al usuario {nombre} ({email})")
            flash('Usuario creado con éxito.', 'success')
            return redirect(url_for('admin.panel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    return render_template('admin/crear_usuario.html', roles=roles)

# --- EDITAR USUARIO ---
@admin_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario_a_editar = Usuario.query.get_or_404(id)
    roles = Rol.query.order_by(Rol.nombre).all()

    if request.method == 'POST':
        email_nuevo = request.form.get('email')
        
        # Validar duplicados si cambia el email
        usuario_existente = Usuario.query.filter_by(email=email_nuevo).first()
        if usuario_existente and usuario_existente.id != id:
            flash('Error: Ese correo ya pertenece a otro usuario.', 'danger')
            return render_template('admin/editar_usuario.html', usuario=usuario_a_editar, roles=roles)

        # Actualizar datos
        usuario_a_editar.nombre_completo = request.form.get('nombre_completo')
        usuario_a_editar.email = email_nuevo
        usuario_a_editar.rol_id = request.form.get('rol_id')
        usuario_a_editar.cambio_clave_requerido = request.form.get('forzar_cambio_clave') == '1'

        # Actualizar password solo si escribió algo
        password = request.form.get('password')
        if password and password.strip():
            usuario_a_editar.set_password(password)
            flash('Contraseña actualizada.', 'info')

        try:
            db.session.commit()
            registrar_log("Edición Usuario", f"Admin editó a {usuario_a_editar.nombre_completo}")
            flash('Usuario actualizado con éxito.', 'success')
            return redirect(url_for('admin.panel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('admin/editar_usuario.html', usuario=usuario_a_editar, roles=roles)

# --- ACTIVAR / DESACTIVAR ---
@admin_bp.route('/toggle_activo/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_activo(id):
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.panel'))
        
    usuario.activo = not usuario.activo
    db.session.commit()
    
    estado = "activado" if usuario.activo else "desactivado"
    registrar_log("Cambio Estado", f"Usuario {usuario.nombre_completo} fue {estado}.")
    flash(f'Usuario {usuario.nombre_completo} {estado}.', 'success')
    return redirect(url_for('admin.panel'))

# --- VISUALIZACIÓN DE LOGS ---
@admin_bp.route('/ver_logs')
@login_required
@admin_required
def ver_logs():
    # Paginación
    page = request.args.get('page', 1, type=int)
    
    # Filtros desde la URL
    usuario_filtro = request.args.get('usuario_id')
    accion_filtro = request.args.get('accion')

    # Query Base: Ordenar por fecha descendente (lo más nuevo primero)
    query = Log.query.order_by(Log.timestamp.desc())

    # Aplicar Filtro Usuario
    if usuario_filtro and usuario_filtro.isdigit():
        query = query.filter(Log.usuario_id == int(usuario_filtro))
    
    # Aplicar Filtro Acción
    if accion_filtro:
        query = query.filter(Log.accion == accion_filtro)

    # Paginamos
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    
    # Datos para los selectores del filtro
    todos_los_usuarios = Usuario.query.order_by(Usuario.nombre_completo).all()
    
    # Lista de acciones registradas en el sistema (Actualiza esta lista si agregas nuevas acciones)
    acciones_posibles = [
        "Inicio de Sesión",
        "Cierre de Sesión",
        "Creación Usuario",
        "Edición Usuario",
        "Cambio Estado", # Activar/Desactivar
        "Cambio de Clave",
        "Recuperación Clave"
    ]

    return render_template('admin/ver_logs.html',
                           pagination=pagination,
                           todos_los_usuarios=todos_los_usuarios,
                           acciones_posibles=acciones_posibles,
                           filtros={'usuario_id': usuario_filtro, 'accion': accion_filtro})