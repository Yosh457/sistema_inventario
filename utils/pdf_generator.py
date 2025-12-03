# utils/pdf_generator.py
from fpdf import FPDF
from datetime import datetime
import os

class ActaEntregaPDF(FPDF):
    def header(self):
        # Rutas de logos
        logo_maho = os.path.join(os.getcwd(), 'static', 'logoMaho.png')
        logo_aps = os.path.join(os.getcwd(), 'static', 'Logo_Red_APS_2.png')
        
        # Logo Izquierda (Maho)
        if os.path.exists(logo_maho):
            self.image(logo_maho, 10, 8, 50) # x, y, w
            
        # Logo Derecha (APS)
        if os.path.exists(logo_aps):
            self.image(logo_aps, 155, 8, 45)

        # Título Central
        self.set_y(15)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'ORDEN DE ENTREGA UNIDAD TICS', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128) # Gris
        self.cell(0, 10, 'Unidad Tics MAHO Salud', 0, 0, 'C')

def generar_acta_entrega(movimiento, equipo=None):
    pdf = ActaEntregaPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- DATOS VARIABLES ---
    fecha_str = movimiento.fecha.strftime("%d/%m/%Y")
    anio_actual = movimiento.fecha.year
    folio = f"{movimiento.id:04d}/{anio_actual}" # Ej: 0005/2025
    
    # Parseo del destinatario desde el motivo
    nombre_receptor = ""
    unidad_receptor = ""
    
    # Intentamos extraer info si el motivo tiene formato "Entrega a: X | Motivo: Y"
    if "Entrega a:" in movimiento.motivo:
        try:
            partes = movimiento.motivo.split('|')
            info_receptor = partes[0].replace("Entrega a:", "").strip()
            # Si el usuario puso "Juan Perez - Finanzas", separamos
            if "-" in info_receptor:
                nombre_receptor, unidad_receptor = info_receptor.split('-', 1)
            else:
                nombre_receptor = info_receptor
        except:
            pass

    # --- 1. FOLIO Y FECHA ---
    pdf.set_font("Arial", "B", 10)
    pdf.set_y(35)
    
    # Folio (Izquierda)
    pdf.set_x(10)
    pdf.cell(18, 8, "Folio N°", 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(30, 8, folio, 1, 0, 'C') # Recuadro
    
    # Fecha (Derecha)
    pdf.set_x(150)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(15, 8, "Fecha", 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(35, 8, fecha_str, 1, 1, 'C') # Recuadro y Salto de línea

    pdf.ln(5)

    # --- 2. DATOS DEL RECEPTOR ---
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(255, 0, 0) # Rojo para el título
    pdf.cell(0, 6, "DATOS DEL RECEPTOR", 0, 1, 'C')
    pdf.set_text_color(0, 0, 0) # Volver a Negro

    # Fila 1: Nombre (Ancho completo)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Nombre", 0, 0) # Etiqueta
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 8, nombre_receptor, 1, 1) # Caja input (Ancho restante)

    # Fila 2: Rut y Teléfono
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Rut", 0, 0)
    pdf.cell(60, 8, "", 1, 0) # Caja vacía para Rut
    
    pdf.set_x(105) # Mover a la derecha
    pdf.cell(20, 8, "Teléfono", 0, 0)
    pdf.cell(0, 8, "", 1, 1) # Caja vacía para teléfono

    # Fila 3: Correo y Unidad
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Correo", 0, 0)
    pdf.cell(60, 8, "", 1, 0) # Caja vacía
    
    pdf.set_x(105)
    pdf.cell(20, 8, "Unidad", 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 8, unidad_receptor, 1, 1) # Caja con unidad si la tenemos

    pdf.ln(5)

    # --- 3. PRODUCTOS ENTREGADOS ---
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "PRODUCTOS ENTREGADOS DEL ÁREA TIC", 0, 1, 'C')

    # Caja de Contenido
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(10, pdf.get_y(), 190, 40) # Dibujar rectángulo grande manual
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 6, "Contenido:", 0, 1)
    
    # Detalle del producto
    pdf.set_font("Arial", "", 10)
    texto_producto = f"- {movimiento.cantidad}x {movimiento.producto.nombre}\n"
    if equipo:
        texto_producto += f"  Serie: {equipo.numero_serie}\n"
    # Limpiamos saltos de línea extra en la descripción para que no rompa el PDF
    desc = (movimiento.producto.descripcion or "").replace('\n', ' ').replace('\r', '')
    texto_producto += f"  ({desc[:80]}...)" if len(desc) > 80 else f"  ({desc})"
    
    pdf.set_xy(12, pdf.get_y()) # Margen interno
    pdf.multi_cell(186, 6, texto_producto)
    
    pdf.set_y(pdf.get_y() + 22) # Bajar cursor manualmente para salir del rect

    # --- 4. OBSERVACIONES ---
    y_observacion = pdf.get_y()
    pdf.rect(10, y_observacion, 190, 20) # Rectángulo Observaciones
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_xy(10, y_observacion)
    pdf.cell(30, 6, "Observaciones:", 0, 0)
    
    pdf.set_font("Arial", "", 9)
    motivo_limpio = movimiento.motivo.split('|')[-1].replace("Motivo:", "").strip()
    pdf.set_xy(40, y_observacion)
    pdf.multi_cell(158, 6, motivo_limpio)
    
    pdf.set_y(y_observacion + 20) # Bajar

    # Disclaimer
    pdf.set_font("Arial", "", 7)
    pdf.multi_cell(0, 4, "Quien acepta y recibe conforme, se compromete a cuidarlo y hacer buen uso del equipo haciéndose responsable de este.", 0, 'C')
    
    pdf.ln(15)

    # --- 5. FIRMA ---
    pdf.line(70, pdf.get_y(), 140, pdf.get_y()) # Línea central
    pdf.ln(2)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "FIRMA RECEPTOR DE LA ENTREGA", 0, 1, 'C')
    pdf.ln(10)

    # --- 6. IMAGEN ---
    pdf.set_font("Arial", "B", 9)
    # Dibujar caja para la imagen (El resto de la página hasta el footer)
    y_actual = pdf.get_y()
    espacio_disponible = 270 - y_actual
    
    # Dibujamos el cuadro usando el espacio disponible (o un mínimo de 50mm)
    altura_cuadro = max(espacio_disponible, 60)
    
    pdf.rect(10, y_actual, 190, altura_cuadro)
    pdf.set_xy(12, y_actual + 2)
    pdf.cell(0, 5, "Imagen:", 0, 1)
    
    # --- LÓGICA DE IMAGEN MEJORADA ---
    if movimiento.producto.imagen:
        ruta_img = os.path.join(os.getcwd(), 'static', 'uploads', 'productos', movimiento.producto.imagen)
        if os.path.exists(ruta_img):
            # Dejamos un margen de 10mm dentro del cuadro
            margen_interno = 10
            ancho_max = 170 # 190 del cuadro - 20 margen
            alto_max = altura_cuadro - 20 # altura cuadro - margen titulo y borde
            
            # FPDF image() con w=0, h=0 usa tamaño real.
            # Si ponemos w=ancho_max y h=0, mantiene ratio basado en ancho.
            # Pero necesitamos restringir AMBOS (que no se salga de ancho ni de alto).
            
            # Truco: Usar w=0 y h=alto_max fuerza el alto y calcula el ancho.
            # Luego centramos.
            
            # Coordenadas para centrar
            x_centro = 105 # Centro de la página (210/2)
            y_centro_cuadro = y_actual + (altura_cuadro / 2) + 2 # +2 por el título "Imagen:"
            
            # Insertar imagen restringida por altura (para que no se salga por abajo)
            # Pasamos h=alto_max. FPDF ajustará el ancho proporcionalmente.
            # Nota: Si la imagen es muy ancha y baja, podría salirse por los lados.
            # FPDF no tiene "contain" automático simple, pero esto suele bastar para fotos de productos.
            
            try:
                # Intentamos ajustar por altura primero (seguro para listas verticales)
                pdf.image(ruta_img, x=70, y=y_actual + 15, h=alto_max, w=0)
            except:
                # Si falla (ej: formato no soportado), ignoramos
                pass

    # Salida en bytes
    return bytes(pdf.output())