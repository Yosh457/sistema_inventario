# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Importamos la función de hora desde nuestro paquete utils
from utils import obtener_hora_chile

# Instancia de la base de datos
db = SQLAlchemy()

# --- MODELOS DE USUARIOS Y ROLES ---

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    usuarios = db.relationship('Usuario', back_populates='rol')

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=obtener_hora_chile)
    
    # Gestión de contraseña segura
    cambio_clave_requerido = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(32), nullable=True)
    reset_token_expiracion = db.Column(db.DateTime, nullable=True)

    # Relaciones
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    rol = db.relationship('Rol', back_populates='usuarios')

    # Métodos
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=obtener_hora_chile) 
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_nombre = db.Column(db.String(255))
    accion = db.Column(db.String(255), nullable=False)
    detalles = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref=db.backref('logs', lazy=True))


# --- MODELOS DE INVENTARIO ---

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    
    productos = db.relationship('Producto', back_populates='categoria')
    # Una categoría tiene muchas subcategorías
    subcategorias = db.relationship('Subcategoria', back_populates='categoria', cascade="all, delete-orphan")

class Subcategoria(db.Model):
    __tablename__ = 'subcategorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    categoria = db.relationship('Categoria', back_populates='subcategorias')
    
    productos = db.relationship('Producto', back_populates='subcategoria')

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen = db.Column(db.String(255), nullable=True)
    
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    
    # Define si se controla por número de serie (True) o por volumen (False)
    tiene_serie = db.Column(db.Boolean, default=False) 

    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    categoria = db.relationship('Categoria', back_populates='productos')

    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategorias.id'), nullable=True)
    subcategoria = db.relationship('Subcategoria', back_populates='productos')
    
    # Relaciones
    equipos = db.relationship('Equipo', back_populates='producto')
    movimientos = db.relationship('Movimiento', back_populates='producto')

class Equipo(db.Model):
    """Solo para productos con tiene_serie = True"""
    __tablename__ = 'equipos'
    id = db.Column(db.Integer, primary_key=True)
    numero_serie = db.Column(db.String(100), unique=True, nullable=False)
    estado = db.Column(db.Enum('Disponible', 'Asignado', 'Malo', 'Baja'), default='Disponible')
    
    asignado_a = db.Column(db.String(255), nullable=True) 
    ubicacion = db.Column(db.String(100), nullable=True) 

    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    producto = db.relationship('Producto', back_populates='equipos')

class Movimiento(db.Model):
    """Kardex: Historial de movimientos"""
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=obtener_hora_chile)
    tipo = db.Column(db.Enum('Entrada', 'Salida', 'Ajuste', 'Devolución', 'Baja'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255)) 
    
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    producto = db.relationship('Producto', back_populates='movimientos')
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario')