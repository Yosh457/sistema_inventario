# extensions.py
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Inicializamos las extensiones vacías (se conectan en app.py)
login_manager = LoginManager()
csrf = CSRFProtect()