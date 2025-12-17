# 📦 Sistema de Inventario TIC - Salud MAHO

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)
![Database](https://img.shields.io/badge/Database-MySQL-blue.svg)
![ORM](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)

Sistema web desarrollado para la **Unidad de TICs del Departamento de Salud de la Municipalidad de Alto Hospicio**. Permite el control total del ciclo de vida de los activos tecnológicos, gestión de stock, movimientos (Kardex) y la generación digital de actas de entrega.

## 🚀 Características Principales

* **Gestión de Activos:** Gestión completa de productos, categorías y subcategorías, con control de stock en tiempo real.
* **Control de Movimientos (Kardex):**
    * Registro de **Entradas** (Compras, ingresos).
    * Registro de **Salidas** (Asignación a funcionarios o unidades).
    * Registro de **Devoluciones** (Reingreso a bodega).
* **Documentación Digital (Actas PDF):**
    * Generación automática de **Actas de Entrega y Devolución** en formato PDF institucional listas para firmar (Librería `FPDF2`).
* **Alertas Inteligentes:**
    * Indicadores visuales de **Stock Crítico** y **Stock Bajo** en el panel principal.
* **Seguridad y Auditoría:**
    * Protección CSRF en todos los formularios.
    * Registro detallado de Logs (Quién asignó qué equipo y cuándo).
    * Validación de contraseñas seguras y gestión de sesiones.
    * Forzado de cambio de contraseña en primer inicio de sesión.
* **Experiencia de Usuario (UX):**
    * Buscador dinámico de productos.
    * Interfaz limpia y responsiva con **TailwindCSS**.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Flask.
* **Base de Datos:** MySQL (SQLAlchemy ORM).
* **Frontend:** HTML5, Jinja2, TailwindCSS (CDN), JavaScript.
* **Librerías Clave:**
    * `FPDF2`: Motor de generación de reportes y actas PDF.
    * `Flask-Login`: Gestión de sesiones y autenticación.
    * `Flask-WTF`: Manejo seguro de formularios.
    * `Werkzeug`: Hashing seguro de contraseñas.

## 📂 Estructura del Proyecto

El proyecto sigue una arquitectura modular basada en **Blueprints** y **Application Factory**:

```text
sistema_inventario/
├── blueprints/          # Lógica modular (Admin, Auth, Inventario)
├── static/              # Assets (CSS Tailwind, JS, Logos, Iconos)
├── templates/           # Vistas HTML (Jinja2) con herencia de base.html
│   ├── admin/           # Gestión de usuarios
│   ├── auth/            # Login y recuperación de clave
│   └── inventario/      # Dashboard, Productos, Movimientos, PDF
├── utils/               # Módulo de utilidades refactorizado
│   ├── __init__.py      # Exportación de funciones
│   ├── decorators.py    # Decoradores de roles (admin_required, gestor_required)
│   ├── helpers.py       # Lógica auxiliar (Logs, Fechas)
│   ├── email.py         # Envío de correos
│   └── pdf_generator.py # Generador de Actas PDF con FPDF2
├── app.py               # Inicialización de la aplicación
├── models.py            # Modelos de BD (Producto, Movimiento, Usuario, etc.)
├── extensions.py        # Instancias de extensiones (login_manager, csrf)
└── requirements.txt     # Dependencias del proyecto
```
## 🌿 Gestión de Ramas y Despliegue
Este repositorio maneja dos flujos de trabajo distintos para separar el desarrollo local de la producción con identidad centralizada:

1. **Rama `main`** (Desarrollo Local / Standalone)
* **Autenticación:** Local (Tabla usuarios interna).

* **Uso:** Para desarrollo, pruebas de nuevas funcionalidades y uso offline.

* **Base de Datos:** Esquema local `inventario_tic_db`.

2. **Rama `produccion-global`** (Despliegue)
* **Autenticación:** Centralizada (Identidad Global).

* **Arquitectura**
    * El modelo `Usuario` local ya no guarda credenciales.
    * Se conecta a una Base de Datos externa mediante proxies en SQL.
    * Valida credenciales contra la tabla maestra y autoriza permisos según la tabla local.

* **Uso:** Versión productiva desplegada en el Hosting/CPanel.

## ⚙️ Instalación Local

1. Clonar el repositorio:

```bash
git clone https://github.com/Yosh457/sistema_inventario.git
cd sistema_inventario
```
2. Crear entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```
3. Instalar dependencias:

```bash
pip install -r requirements.txt
```
4. Configurar variables de entorno (.env):

```env
SECRET_KEY=tu_clave_secreta
MYSQL_PASSWORD=tu_password_mysql
EMAIL_USUARIO=tu_correo@gmail.com
EMAIL_CONTRASENA=tu_contraseña_aplicacion
```
5. Ejecutar:

```bash
python app.py
```
---
Desarrollado por **Josting Silva**  
Analista Programador – Unidad de TICs  
Departamento de Salud, Municipalidad de Alto Hospicio
