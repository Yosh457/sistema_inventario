# utils/pdf_generator.py
from fpdf import FPDF
from datetime import datetime
import os

class ActaEntregaPDF(FPDF):
    def header(self):
        # Logo
        # Usamos os.getcwd() para buscar desde la raíz del proyecto
        logo_path = os.path.join(os.getcwd(), 'static', 'Logo_Red_APS_2.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        
        self.set_font('Arial', 'B', 15)
        self.cell(80) # Mover a la derecha
        self.cell(30, 10, 'Acta de Entrega de Equipos', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_acta_entrega(movimiento, equipo=None):
    pdf = ActaEntregaPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Datos Generales
    fecha = movimiento.fecha.strftime("%d/%m/%Y %H:%M")
    producto_nombre = movimiento.producto.nombre
    
    # Extraer destinatario del motivo (Formato: "Entrega a: JUAN PEREZ | Motivo: ...")
    # Hacemos un parseo simple
    destinatario = "Funcionario"
    motivo_texto = movimiento.motivo
    if "Entrega a:" in movimiento.motivo:
        try:
            partes = movimiento.motivo.split('|')
            destinatario = partes[0].replace("Entrega a:", "").strip()
            motivo_texto = partes[1].replace("Motivo:", "").strip() if len(partes) > 1 else ""
        except:
            pass

    # Cuerpo del Documento
    texto_cuerpo = f"""
    En Alto Hospicio, a {fecha}, se hace entrega del siguiente equipamiento tecnológico a cargo del Departamento de Salud Municipal.
    
    El funcionario/a {destinatario} recibe a conformidad el siguiente bien:
    
    Producto: {producto_nombre}
    Motivo: {motivo_texto}
    """
    
    if equipo:
        texto_cuerpo += f"\nNúmero de Serie: {equipo.numero_serie}"
        texto_cuerpo += f"\nEstado: {equipo.estado}"
    
    texto_cuerpo += f"\n\nCantidad entregada: {movimiento.cantidad}"

    # Usamos latin-1 para evitar problemas con tildes básicos en FPDF
    # Si tuvieras caracteres muy raros, podrías necesitar una fuente unicode,
    # pero para español básico esto suele bastar.
    pdf.multi_cell(0, 10, texto_cuerpo)
    
    pdf.ln(20)
    
    # Sección de Firmas
    pdf.cell(0, 10, "_"*30 + " "*40 + "_"*30, 0, 1, 'C')
    pdf.cell(0, 10, "Firma Recibe" + " "*65 + "Firma Entrega (TIC)", 0, 1, 'C')
    
    # Retornar el PDF como bytes explícitos
    # fpdf2 retorna bytes por defecto si no le pasas nombre de archivo,
    # pero para asegurarnos usamos bytes.
    return bytes(pdf.output())