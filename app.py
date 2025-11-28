# app.py
import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, flash
from flask_wtf.csrf import CSRFError

# Importamos extensiones y modelos
from extensions import login_manager, csrf
from models import db, Usuario

def create_app():
    app = Flask(__name__)
    load_dotenv() # Carga las variables del .env

    # --- CONFIGURACIÓN ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Configuración de Base de Datos MySQL
    db_pass = os.getenv('MYSQL_PASSWORD')
    db_name = 'inventario_tic_db'
    # Usamos pymysql como driver
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_pass}@localhost/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- INICIALIZACIÓN ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configuración de Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # --- REGISTRO DE BLUEPRINTS ---
    # NOTA: Estas líneas están comentadas hasta que creemos los archivos en la carpeta blueprints/
    
    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from blueprints.admin import admin_bp
    app.register_blueprint(admin_bp)

    # from blueprints.inventario import inventario_bp
    # app.register_blueprint(inventario_bp)

    # --- RUTAS GLOBALES ---
    @app.route('/')
    def index():
        return redirect(url_for('auth.login')) 

    # --- ERRORES ---
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('La sesión expiró. Intenta enviar el formulario de nuevo.', 'warning')
        return redirect(url_for('auth.login'))
    
    @app.after_request
    def add_header(response):
        """Desactiva el caché para evitar problemas al volver atrás en el navegador"""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return app

# Loader de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)