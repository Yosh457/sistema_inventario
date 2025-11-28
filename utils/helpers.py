import pytz
from datetime import datetime
from flask_login import current_user
# Importamos db y Log dentro de la función para evitar errores de importación circular
# o los importamos aquí si la estructura lo permite. 
# Para evitar ciclos, usaremos imports locales dentro de las funciones si es necesario.

def obtener_hora_chile():
    chile_tz = pytz.timezone('America/Santiago')
    return datetime.now(chile_tz).replace(tzinfo=None)

def registrar_log(accion, detalles):
    """Registra una acción en la base de datos."""
    # Importación local para evitar "Circular Import" con models.py
    from models import db, Log 
    
    if current_user.is_authenticated:
        try:
            nuevo_log = Log(
                usuario_id=current_user.id,
                usuario_nombre=current_user.nombre_completo,
                accion=accion,
                detalles=detalles
            )
            db.session.add(nuevo_log)
            db.session.commit()
        except Exception as e:
            print(f"Error al registrar log: {e}")
            db.session.rollback()