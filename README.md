# Waypoint

Waypoint es una plataforma web desarrollada en Django diseñada para facilitar la gestión de mesas de rol (TTRPG), personajes y bitácoras de aventuras. Ya seas el Amo del Calabozo o un jugador, Waypoint te ayuda a mantener el rastro de tus campañas.

## Características Principales

* **Gestión de Mesas:** Creación de mesas de juego públicas y privadas con control de acceso.
* **Bitácora de Aventuras:** Registro de eventos de la campaña con tipos de entradas personalizadas (Diario libre, Muerte de personaje, etc.).
* **Gestión de Personajes:** Control y seguimiento de los héroes de la campaña.
* **Seguridad:** Protección de rutas y mesas privadas para mantener los secretos del DM a salvo.

## Tecnologías Utilizadas

* **Backend:** Python 3, Django
* **Base de Datos:** SQLite 
* **Frontend:** HTML5, CSS3, JavaScript y Bootstrap

---

## 💻 Instalación Local

Si deseas clonar este proyecto para probarlo o modificarlo en tu propia computadora, sigue estos pasos:

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/](https://github.com/)[ManuelALH]/Waypoint.git
   cd Waypoint

2. **Crea y activa un entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En macOS/Linux:
    source venv/bin/activate

3. **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt

4. **Configura las variables de entorno:**
    Copia el archivo de ejemplo y renómbralo a .env. Luego, abre el archivo y completa los datos requeridos (claves, correos, etc.).
    ```bash
    cp .env.example .env

5. **Aplica las migraciones a la base de datos:**
    ```bash
    python manage.py migrate

6. **Crea un superusuario (Opcional pero recomendado para acceder al panel de admin):**
    ```bash
    python manage.py createsuperuser

7. **Ejecuta el servidor de desarrollo:**
    ```bash
    python manage.py runserver

Visita http://127.0.0.1:8000 en tu navegador para ver la aplicación corriendo.

# Waypoint - Guía de Despliegue

Esta guía detalla los pasos para desplegar el proyecto gratuitamente en **PythonAnywhere**.

## Prerrequisitos

1.  Una cuenta en [GitHub](https://github.com/) con este repositorio subido.
2.  Una cuenta gratuita ("Beginner") en [PythonAnywhere](https://www.pythonanywhere.com/).


## Paso 1: Configuración en PythonAnywhere

1. **Clonar el repositorio:**
    Abre una Bash Console en PythonAnywhere y ejecuta:
    ```bash
    git clone [https://github.com/](https://github.com/)[TU_USUARIO]/Waypoint.git

2. **Crear el Entorno Virtual:**
    Se recomienda usar la misma versión de Python con la que desarrollaste (ej. 3.13).
    ```bash
    mkvirtualenv --python=/usr/bin/python3.13 waypoint-env
    pip install -r Waypoint/requirements.txt

3. **Configurar el .env en producción:**
    Crea tu archivo .env dentro de PythonAnywhere con tus claves reales (recuerda poner DEBUG=False y ajustar tus ALLOWED_HOSTS).

4. **Migraciones y Estáticos:**
    ```bash
    cd Waypoint
    python manage.py migrate
    python manage.py collectstatic

## Paso 2: Configuración de la Pestaña "Web"

1. **Agregar una nueva Web App:**
    Selecciona "Manual Configuration" (NO selecciones Django automático) y elige la versión de Python que usaste.

2. **Virtualenv:**
    Ingresa la ruta a tu entorno: /home/[TU_USUARIO]/.virtualenvs/waypoint-env

3. **Code:**
    Source code: /home/[TU_USUARIO]/Waypoint
    Working directory: /home/[TU_USUARIO]/Waypoint

4. **WSGI Configuration File:**
    ```python
    import os
    import sys
    from dotenv import load_dotenv

    # Ruta al proyecto
    path = '/home/[TU_USUARIO]/Waypoint'
    if path not in sys.path:
        sys.path.append(path)

    # Cargar variables de entorno
    project_folder = os.path.expanduser('~/Waypoint')
    load_dotenv(os.path.join(project_folder, '.env'))

    # Establecer settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'Waypoint'

    # Iniciar la aplicación
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

5. **Static Files:**
    En la sección de archivos estáticos configura:
    URL: /static/
    Directory: /home/[TU_USUARIO]/Wayfinder_Public/staticfiles

## Paso Final
Ve al tope de la pestaña Web, haz clic en el botón verde Reload y visita tu enlace: https://[TU_USUARIO].pythonanywhere.com.

## Licencia
Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.
