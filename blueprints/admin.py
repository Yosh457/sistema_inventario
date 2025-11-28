# blueprints/admin.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils import admin_required

# Definimos el blueprint 'admin'
admin_bp = Blueprint('admin', __name__, template_folder='../templates', url_prefix='/admin')

@admin_bp.route('/panel')
@login_required
@admin_required
def panel():
    # Aquí cargaremos datos reales más adelante
    return render_template('admin/panel.html')