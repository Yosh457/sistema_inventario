# blueprints/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Usuario, Rol, Log, UsuarioGlobal
from utils import registrar_log, admin_required

# Definimos el blueprint
admin_bp = Blueprint('admin', __name__, template_folder='../templates', url_prefix='/admin')

@admin_bp.route('/panel')
@login_required
@admin_required
def panel():
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '')
    rol_filtro = request.args.get('rol_filtro', '')
    estado_filtro = request.args.get('estado_filtro', '')

    # Join con la tabla global para poder buscar por nombre/email
    query = Usuario.query.join(Usuario.identidad)

    # 1. Filtro de Búsqueda (Nombre o Email en la Global)
    if busqueda:
        query = query.filter(
            or_(
                UsuarioGlobal.nombre_completo.ilike(f'%{busqueda}%'),
                UsuarioGlobal.email.ilike(f'%{busqueda}%')
            )
        )
    
    # 2. Filtro de Rol (Local)
    if rol_filtro:
        query = query.filter(Usuario.rol_id == rol_filtro)

    # 3. Filtro de Estado (Local)
    if estado_filtro == 'activo':
        query = query.filter(Usuario.activo == True)
    elif estado_filtro == 'inactivo':
        query = query.filter(Usuario.activo == False)
    
    # Ordenar por nombre (Global)
    pagination = query.order_by(UsuarioGlobal.nombre_completo).paginate(page=page, per_page=10, error_out=False)
    
    roles_para_filtro = Rol.query.order_by(Rol.nombre).all()

    return render_template('admin/panel.html', 
                           pagination=pagination,
                           roles_para_filtro=roles_para_filtro,
                           busqueda=busqueda,
                           rol_filtro=rol_filtro,
                           estado_filtro=estado_filtro)

# --- VINCULAR USUARIO (Antes Crear) ---
@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    roles = Rol.query.order_by(Rol.nombre).all()

    if request.method == 'POST':
        usuario_global_id = request.form.get('usuario_global_id')
        rol_id = request.form.get('rol_id')

        if not usuario_global_id or not rol_id:
            flash('Debes seleccionar un funcionario y un rol.', 'danger')
            return redirect(url_for('admin.crear_usuario'))

        # Validación: Verificar si ya existe localmente (aunque el filtro GET ayuda, es bueno asegurar)
        if Usuario.query.filter_by(usuario_global_id=usuario_global_id).first():
            flash('Este funcionario ya tiene acceso al sistema.', 'warning')
            return redirect(url_for('admin.crear_usuario'))

        # Crear el vínculo local
        nuevo_usuario_local = Usuario(
            usuario_global_id=usuario_global_id,
            rol_id=rol_id,
            activo=True
        )
        
        try:
            db.session.add(nuevo_usuario_local)
            db.session.commit()
            
            # Obtenemos nombre para el log
            usr_glob = UsuarioGlobal.query.get(usuario_global_id)
            nombre_log = usr_glob.nombre_completo if usr_glob else "ID " + str(usuario_global_id)
            
            registrar_log("Vinculación Usuario", f"Admin otorgó acceso a {nombre_log}")
            flash('Funcionario vinculado exitosamente.', 'success')
            return redirect(url_for('admin.panel'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al vincular: {str(e)}', 'danger')

    # GET: Buscar usuarios globales que NO estén en la tabla local
    # 1. Obtener IDs ya registrados localmente
    ids_locales = db.session.query(Usuario.usuario_global_id).all()
    ids_locales_lista = [id[0] for id in ids_locales] # Aplanar lista

    # 2. Consultar globales excluyendo los locales
    if ids_locales_lista:
        usuarios_disponibles = UsuarioGlobal.query.filter(
            UsuarioGlobal.id.notin_(ids_locales_lista),
            UsuarioGlobal.activo == True # Solo usuarios activos globales
        ).order_by(UsuarioGlobal.nombre_completo).all()
    else:
        usuarios_disponibles = UsuarioGlobal.query.filter_by(activo=True).order_by(UsuarioGlobal.nombre_completo).all()

    return render_template('admin/crear_usuario.html', 
                           roles=roles, 
                           usuarios_disponibles=usuarios_disponibles)

# --- EDITAR PERMISOS USUARIO ---
@admin_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario_local = Usuario.query.get_or_404(id)
    roles = Rol.query.order_by(Rol.nombre).all()

    if request.method == 'POST':
        # Solo permitimos editar el Rol localmente. 
        # Nombre, Email y Password se gestionan en la Global.
        
        nuevo_rol_id = request.form.get('rol_id')
        
        if nuevo_rol_id:
            usuario_local.rol_id = nuevo_rol_id
            
            try:
                db.session.commit()
                registrar_log("Edición Permisos", f"Admin cambió rol de {usuario_local.nombre_completo}")
                flash('Permisos actualizados correctamente.', 'success')
                return redirect(url_for('admin.panel'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('admin/editar_usuario.html', usuario=usuario_local, roles=roles)

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
    
    # Usamos la tabla local para el filtro, pero el nombre viene del proxy
    todos_los_usuarios = Usuario.query.all()
    # Ordenamos en Python porque el nombre es propiedad virtual
    todos_los_usuarios.sort(key=lambda u: u.nombre_completo) 
    
    acciones_posibles = [
        "Inicio de Sesión", "Cierre de Sesión", "Vinculación Usuario", 
        "Edición Permisos", "Cambio Estado", 
        "Crear Categoría", "Editar Categoría", "Eliminar Categoría",
        "Crear Producto", "Editar Producto", "Eliminar Producto",
        "Ingreso Stock", "Salida Stock", "Devolución/Baja"
    ]

    return render_template('admin/ver_logs.html',
                           pagination=pagination,
                           todos_los_usuarios=todos_los_usuarios,
                           acciones_posibles=acciones_posibles,
                           filtros={'usuario_id': usuario_filtro, 'accion': accion_filtro})