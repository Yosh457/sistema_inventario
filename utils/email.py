import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import url_for

def enviar_correo_reseteo(usuario, token):
    remitente = os.getenv("EMAIL_USUARIO")
    contrasena = os.getenv("EMAIL_CONTRASENA")
    
    if not remitente or not contrasena:
        print("ERROR: Credenciales de correo faltantes en .env")
        return

    msg = MIMEMultipart()
    msg['Subject'] = 'Restablecimiento de Contraseña - Sistema Inventario'
    msg['From'] = formataddr(('Sistema Inventario', remitente))
    msg['To'] = usuario.email

    url_reseteo = url_for('auth.resetear_clave', token=token, _external=True)

    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #2563eb;">Recuperación de Contraseña</h2>
        <p>Hola <strong>{usuario.nombre_completo}</strong>,</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
        <p><a href="{url_reseteo}">Click aquí para restablecer</a></p>
    </div>
    """
    msg.attach(MIMEText(cuerpo_html, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, contrasena)
            server.send_message(msg)
    except Exception as e:
        print(f"Error enviando correo: {e}")