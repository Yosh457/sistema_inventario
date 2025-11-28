# blueprints/inventario.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Categoria, Producto, Equipo, Movimiento
from utils import registrar_log, gestor_required

# Definimos el Blueprint
inventario_bp = Blueprint('inventario', __name__, template_folder='../templates', url_prefix='/inventario')

# --- PANEL PRINCIPAL (DASHBOARD) ---
@inventario_bp.route('/panel')
@login_required
@gestor_required
def panel():
    """Vista principal para el Gestor de Inventario"""
    # Aquí luego agregaremos resúmenes de stock
    return render_template('inventario/panel.html')

# --- GESTIÓN DE CATEGORÍAS ---

@inventario_bp.route('/categorias')
@login_required
@gestor_required
def lista_categorias():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('inventario/categorias/lista.html', categorias=categorias)

@inventario_bp.route('/categorias/crear', methods=['POST'])
@login_required
@gestor_required
def crear_categoria():
    nombre = request.form.get('nombre')
    
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'danger')
        return redirect(url_for('inventario.lista_categorias'))
        
    # Verificar duplicados
    if Categoria.query.filter_by(nombre=nombre).first():
        flash('Esa categoría ya existe.', 'danger')
        return redirect(url_for('inventario.lista_categorias'))
        
    nueva_cat = Categoria(nombre=nombre)
    
    try:
        db.session.add(nueva_cat)
        db.session.commit()
        registrar_log("Crear Categoría", f"Creó la categoría '{nombre}'")
        flash('Categoría creada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear: {str(e)}', 'danger')
        
    return redirect(url_for('inventario.lista_categorias'))

@inventario_bp.route('/categorias/editar/<int:id>', methods=['POST'])
@login_required
@gestor_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    nuevo_nombre = request.form.get('nombre')
    
    if nuevo_nombre:
        categoria.nombre = nuevo_nombre
        db.session.commit()
        registrar_log("Editar Categoría", f"Renombró categoría ID {id} a '{nuevo_nombre}'")
        flash('Categoría actualizada.', 'success')
    
    return redirect(url_for('inventario.lista_categorias'))

@inventario_bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
@gestor_required
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    
    # Validar si tiene productos asociados antes de borrar
    if categoria.productos:
        flash('No puedes eliminar esta categoría porque tiene productos asociados.', 'danger')
        return redirect(url_for('inventario.lista_categorias'))
        
    db.session.delete(categoria)
    db.session.commit()
    registrar_log("Eliminar Categoría", f"Eliminó la categoría '{categoria.nombre}'")
    flash('Categoría eliminada.', 'success')
    
    return redirect(url_for('inventario.lista_categorias'))