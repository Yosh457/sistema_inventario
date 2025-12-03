# utils/pdf_generator.py
from fpdf import FPDF
from datetime import datetime
import os

class ActaEntregaPDF(FPDF):
    def __init__(self, titulo_doc="ORDEN DE ENTREGA UNIDAD TICS"):
        super().__init__()
        self.titulo_doc = titulo_doc

    def header(self):
        # Rutas de logos
        logo_maho = os.path.join(os.getcwd(), 'static', 'logoMaho.png')
        logo_aps = os.path.join(os.getcwd(), 'static', 'Logo_Red_APS_2.png')
        
        # Logo Izquierda (Maho)
        if os.path.exists(logo_maho):
            self.image(logo_maho, 10, 8, 50) 
            
        # Logo Derecha (APS)
        if os.path.exists(logo_aps):
            self.image(logo_aps, 155, 8, 45)

        # Título Central DINÁMICO
        self.set_y(15)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.titulo_doc, 0, 1, 'C') # Usamos la variable
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128) # Gris
        self.cell(0, 10, 'Unidad Tics MAHO Salud', 0, 0, 'C')

def generar_acta_entrega(movimiento, equipo=None):
    # 1. Definir el título según el tipo de movimiento
    titulo = "ACTA DE MOVIMIENTO" # Default
    if movimiento.tipo == 'Salida':
        titulo = "ORDEN DE ENTREGA UNIDAD TICS"
    elif movimiento.tipo == 'Devolución':
        titulo = "ACTA DE RECEPCIÓN / DEVOLUCIÓN"
    elif movimiento.tipo == 'Baja':
        titulo = "ORDEN DE BAJA UNIDAD TICS"

    # Pasamos el título al constructor
    pdf = ActaEntregaPDF(titulo_doc=titulo)
    
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- DATOS VARIABLES ---
    fecha_str = movimiento.fecha.strftime("%d/%m/%Y")
    anio_actual = movimiento.fecha.year
    folio = f"{movimiento.id:04d}/{anio_actual}"
    
    # Parseo de destinatario (funciona para Entrega y Devolución)
    nombre_receptor = ""
    unidad_receptor = ""
    
    # Buscamos patrones comunes en el motivo
    texto_origen = movimiento.motivo
    if "Entrega a:" in texto_origen:
        texto_origen = texto_origen.replace("Entrega a:", "")
    elif "Devolución de:" in texto_origen:
        texto_origen = texto_origen.replace("Devolución de:", "")
    
    try:
        if "|" in texto_origen:
            partes = texto_origen.split('|')
            info_persona = partes[0].strip()
        else:
            info_persona = texto_origen

        if "-" in info_persona:
            nombre_receptor, unidad_receptor = info_persona.split('-', 1)
        else:
            nombre_receptor = info_persona
    except:
        pass

    # --- 1. FOLIO Y FECHA ---
    pdf.set_font("Arial", "B", 10)
    pdf.set_y(35)
    
    pdf.set_x(10)
    pdf.cell(18, 8, "Folio N°", 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(30, 8, folio, 1, 0, 'C')
    
    pdf.set_x(150)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(15, 8, "Fecha", 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(35, 8, fecha_str, 1, 1, 'C')
    pdf.ln(5)

    # --- 2. DATOS DEL RECEPTOR (O Quien devuelve) ---
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(255, 0, 0)
    
    # Cambiamos el subtítulo según contexto
    subtitulo_datos = "DATOS DEL RECEPTOR"
    if movimiento.tipo in ['Devolución', 'Baja']:
        subtitulo_datos = "DATOS DE QUIEN ENTREGA / DEVUELVE"
        
    pdf.cell(0, 6, subtitulo_datos, 0, 1, 'C')
    pdf.set_text_color(0, 0, 0)

    # Tabla de datos
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Nombre", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 8, nombre_receptor.strip(), 1, 1)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Rut", 0, 0)
    pdf.cell(60, 8, "", 1, 0)
    
    pdf.set_x(105)
    pdf.cell(20, 8, "Teléfono", 0, 0)
    pdf.cell(0, 8, "", 1, 1)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Correo", 0, 0)
    pdf.cell(60, 8, "", 1, 0)
    
    pdf.set_x(105)
    pdf.cell(20, 8, "Unidad", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 8, unidad_receptor.strip(), 1, 1)

    pdf.ln(5)

    # --- 3. PRODUCTOS ---
    pdf.set_font("Arial", "B", 9)
    titulo_prod = "PRODUCTOS ENTREGADOS DEL ÁREA TIC"
    if movimiento.tipo in ['Devolución', 'Baja']:
        titulo_prod = "PRODUCTOS RECEPCIONADOS POR ÁREA TIC"
        
    pdf.cell(0, 6, titulo_prod, 0, 1, 'C')

    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, pdf.get_y(), 190, 40)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "Contenido:", 0, 1)
    
    pdf.set_font("Arial", "", 10)
    texto_producto = f"- {movimiento.cantidad}x {movimiento.producto.nombre}\n"
    if equipo:
        texto_producto += f"  Serie: {equipo.numero_serie}\n"
        texto_producto += f"  Estado: {equipo.estado}\n" # Agregamos estado para ver si es Baja
    
    desc = (movimiento.producto.descripcion or "").replace('\n', ' ').replace('\r', '')
    texto_producto += f"  ({desc[:80]}...)" if len(desc) > 80 else f"  ({desc})"
    
    pdf.set_xy(12, pdf.get_y())
    pdf.multi_cell(186, 6, texto_producto)
    
    pdf.set_y(pdf.get_y() + 22) 

    # --- 4. OBSERVACIONES ---
    y_observacion = pdf.get_y()
    pdf.rect(10, y_observacion, 190, 20)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_xy(10, y_observacion)
    pdf.cell(30, 6, "Observaciones:", 0, 0)
    
    pdf.set_font("Arial", "", 9)
    try:
        # Limpiamos el texto del motivo para dejar solo la observación real
        motivo_limpio = movimiento.motivo.split('|')[-1]
        motivo_limpio = motivo_limpio.replace("Motivo:", "").strip()
    except:
        motivo_limpio = movimiento.motivo
        
    pdf.set_xy(40, y_observacion)
    pdf.multi_cell(158, 6, motivo_limpio)
    
    pdf.set_y(y_observacion + 20) 

    # Disclaimer
    pdf.set_font("Arial", "", 7)
    disclaimer = "Quien acepta y recibe conforme, se compromete a cuidarlo y hacer buen uso del equipo haciéndose responsable de este."
    if movimiento.tipo in ['Devolución', 'Baja']:
        disclaimer = "Se certifica la recepción del equipamiento por parte de la Unidad de TICs."
        
    pdf.multi_cell(0, 4, disclaimer, 0, 'C')
    pdf.ln(15)

    # --- 5. FIRMA ---
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", "B", 9)
    
    texto_firma = "FIRMA RECEPTOR DE LA ENTREGA"
    if movimiento.tipo in ['Devolución', 'Baja']:
        texto_firma = "FIRMA QUIEN ENTREGA / DEVUELVE"
        
    pdf.cell(0, 5, texto_firma, 0, 1, 'C')
    pdf.ln(10)

    # --- 6. IMAGEN ---
    pdf.set_font("Arial", "B", 9)
    y_actual = pdf.get_y()
    espacio_disponible = 270 - y_actual
    altura_cuadro = max(espacio_disponible, 60)
    
    pdf.rect(10, y_actual, 190, altura_cuadro)
    pdf.set_xy(12, y_actual + 2)
    pdf.cell(0, 5, "Imagen:", 0, 1)
    
    if movimiento.producto.imagen:
        ruta_img = os.path.join(os.getcwd(), 'static', 'uploads', 'productos', movimiento.producto.imagen)
        if os.path.exists(ruta_img):
            alto_max = altura_cuadro - 20 
            try:
                pdf.image(ruta_img, x=70, y=y_actual + 15, h=alto_max, w=0)
            except:
                pass

    return bytes(pdf.output())