# blueprints/inventario.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
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

# --- GESTIÓN DE PRODUCTOS ---

def allowed_file(filename):
    """Verifica si la extensión del archivo es válida para imágenes"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@inventario_bp.route('/productos')
@login_required
@gestor_required
def lista_productos():
    # Obtener productos con su categoría (join implícito por la relación)
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template('inventario/productos/lista.html', productos=productos)

@inventario_bp.route('/productos/crear', methods=['GET', 'POST'])
@login_required
@gestor_required
def crear_producto():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        categoria_id = request.form.get('categoria_id')
        descripcion = request.form.get('descripcion')
        stock_minimo = request.form.get('stock_minimo')
        tiene_serie = request.form.get('tiene_serie') == '1' # Checkbox
        
        # Validación: Código único
        if codigo and Producto.query.filter_by(codigo=codigo).first():
            flash('El código ingresado ya existe en otro producto.', 'danger')
            return render_template('inventario/productos/crear_producto.html', categorias=categorias, datos_previos=request.form)

        # Manejo de Imagen
        imagen_filename = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Renombramos para evitar duplicados (usando codigo o nombre)
                ext = filename.rsplit('.', 1)[1].lower()
                nuevo_nombre = f"{codigo}_{nombre.replace(' ', '_')}.{ext}"
                
                # Guardar
                ruta_guardado = os.path.join(current_app.root_path, 'static/uploads/productos')
                os.makedirs(ruta_guardado, exist_ok=True) # Crea la carpeta si no existe por seguridad
                file.save(os.path.join(ruta_guardado, nuevo_nombre))
                imagen_filename = nuevo_nombre

        nuevo_prod = Producto(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            categoria_id=categoria_id,
            stock_minimo=stock_minimo,
            tiene_serie=tiene_serie,
            imagen=imagen_filename,
            stock_actual=0 # Empieza en 0 hasta que hagamos ingresos
        )

        try:
            db.session.add(nuevo_prod)
            db.session.commit()
            registrar_log("Crear Producto", f"Creó el producto '{nombre}' (SKU: {codigo})")
            flash('Producto creado correctamente.', 'success')
            return redirect(url_for('inventario.lista_productos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'danger')

    return render_template('inventario/productos/crear_producto.html', categorias=categorias)

@inventario_bp.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@gestor_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.categoria_id = request.form.get('categoria_id')
        producto.descripcion = request.form.get('descripcion')
        producto.stock_minimo = request.form.get('stock_minimo')
        # Nota: El código y tiene_serie idealmente no deberían cambiarse fácilmente 
        # si ya hay movimientos, pero por ahora lo permitiremos con cuidado.
        producto.codigo = request.form.get('codigo')
        producto.tiene_serie = request.form.get('tiene_serie') == '1'

        # Manejo de Nueva Imagen
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                # Borrar imagen anterior si existe
                if producto.imagen:
                    try:
                        os.remove(os.path.join(current_app.root_path, 'static/uploads/productos', producto.imagen))
                    except:
                        pass # Si no existe el archivo físico, seguimos
                
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                nuevo_nombre = f"{producto.codigo}_{producto.nombre.replace(' ', '_')}.{ext}"
                
                ruta_guardado = os.path.join(current_app.root_path, 'static/uploads/productos')
                file.save(os.path.join(ruta_guardado, nuevo_nombre))
                producto.imagen = nuevo_nombre

        db.session.commit()
        registrar_log("Editar Producto", f"Editó el producto '{producto.nombre}'")
        flash('Producto actualizado.', 'success')
        return redirect(url_for('inventario.lista_productos'))

    return render_template('inventario/productos/editar_producto.html', producto=producto, categorias=categorias)

@inventario_bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
@gestor_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    
    # Validar si hay stock o movimientos antes de borrar
    # (Para evitar inconsistencias graves en la BD)
    if producto.stock_actual > 0:
        flash('No puedes eliminar un producto con stock activo. Debes darlo de baja primero.', 'danger')
        return redirect(url_for('inventario.lista_productos'))

    db.session.delete(producto)
    db.session.commit()
    registrar_log("Eliminar Producto", f"Eliminó el producto '{producto.nombre}'")
    flash('Producto eliminado.', 'success')
    return redirect(url_for('inventario.lista_productos'))

# --- CONTROL DE STOCK ---

@inventario_bp.route('/producto/<int:id>/ingreso', methods=['GET', 'POST'])
@login_required
@gestor_required
def ingreso_stock(id):
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        motivo = request.form.get('motivo')
        # Obtenemos el proveedor o ubicación si quisieras agregarlo después
        
        # --- CASO 1: PRODUCTO SERIALIZADO (Notebooks) ---
        if producto.tiene_serie:
            seriales_raw = request.form.get('seriales') # Textarea
            # Separamos por líneas y limpiamos espacios vacíos
            lista_seriales = [s.strip() for s in seriales_raw.split('\n') if s.strip()]
            
            if not lista_seriales:
                flash('Debes ingresar al menos un número de serie.', 'danger')
                return redirect(url_for('inventario.ingreso_stock', id=id))
            
            cantidad_agregada = 0
            errores = []

            for serie in lista_seriales:
                # Verificar si ya existe ese serial en la BD
                if Equipo.query.filter_by(numero_serie=serie).first():
                    errores.append(f"El serial {serie} ya existe.")
                    continue
                
                nuevo_equipo = Equipo(
                    numero_serie=serie,
                    producto_id=producto.id,
                    estado='Disponible',
                    ubicacion='Bodega Central' # Default por ahora
                )
                db.session.add(nuevo_equipo)
                cantidad_agregada += 1
            
            if cantidad_agregada > 0:
                # Actualizamos el contador total del producto
                producto.stock_actual += cantidad_agregada
                
                # Registramos el Movimiento en el Kardex
                movimiento = Movimiento(
                    tipo='Entrada',
                    cantidad=cantidad_agregada,
                    motivo=f"{motivo} (Series: {', '.join(lista_seriales[:3])}...)", # Guardamos un resumen
                    producto_id=producto.id,
                    usuario_id=current_user.id
                )
                db.session.add(movimiento)
                db.session.commit()
                
                registrar_log("Ingreso Stock", f"Ingresó {cantidad_agregada} unidades a {producto.nombre}")
                flash(f'Se ingresaron {cantidad_agregada} equipos correctamente.', 'success')
            
            if errores:
                for error in errores:
                    flash(error, 'warning')

        # --- CASO 2: PRODUCTO A GRANEL (Cables) ---
        else:
            try:
                cantidad = int(request.form.get('cantidad'))
                if cantidad <= 0:
                    flash('La cantidad debe ser mayor a 0.', 'danger')
                    return redirect(url_for('inventario.ingreso_stock', id=id))
                
                producto.stock_actual += cantidad
                
                movimiento = Movimiento(
                    tipo='Entrada',
                    cantidad=cantidad,
                    motivo=motivo,
                    producto_id=producto.id,
                    usuario_id=current_user.id
                )
                db.session.add(movimiento)
                db.session.commit()
                
                registrar_log("Ingreso Stock", f"Ingresó {cantidad} unidades a {producto.nombre}")
                flash(f'Stock actualizado. Nuevo total: {producto.stock_actual}', 'success')
                
            except ValueError:
                flash('Cantidad inválida.', 'danger')

        return redirect(url_for('inventario.ver_producto', id=id))

    return render_template('inventario/movimientos/ingreso.html', producto=producto)

@inventario_bp.route('/producto/<int:id>/detalle')
@login_required
@gestor_required
def ver_producto(id):
    producto = Producto.query.get_or_404(id)
    # Obtenemos últimos 50 movimientos
    movimientos = Movimiento.query.filter_by(producto_id=id).order_by(Movimiento.fecha.desc()).limit(50).all()
    
    # Si es seriado, obtenemos los equipos
    equipos = []
    if producto.tiene_serie:
        equipos = Equipo.query.filter_by(producto_id=id).all()
        
    return render_template('inventario/productos/ver_detalle.html', 
                           producto=producto, 
                           movimientos=movimientos, 
                           equipos=equipos)