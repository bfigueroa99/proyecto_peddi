# Bienes Raíz-ES

Esta aplicación de prueba permite a los usuarios simular procedimientos de seguimiento de Inscripciones y Enajenación de bienes raíces, con el objeto de poder determinar quienes son los propietarios de un bien raíz y en qué proporción, en un determinado momento. Esto pertenece al Proyecto 1 del curso Diseño de Software Verificable.

## 📦 Instalación de Dependencias 

De modo a sugerencia, se debe estar en un entorno virtual para mayor seguridad entre todos.Para aquello, debes ejecutar los siguientes comandos en el path principal:

- 🔨 Creación de entorno virtual:
```bash
python -m venv venv
```

- ✅ Activacion de entorno virtual:
```bash
.venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux
```

- ❌ Desactivar el entorno virtual

```bash
.venv\Scripts\deactivate  # Windows
source venv/bin/deactivate  # Linux
```

Las dependencias necesarias para el funcionamiento se encuentran en el documento de `requirements.txt` y para poder de forma sencilla instalar todo se tiene que ejecutar lo siguiente.

```bash
pip install -r requirements.txt
```

## ▶️ Iniciar Servidor ▶️

Para iniciar el servidor, ejecuta el siguiente comando según tu sistema operativo:

```bash
$env:TESTING="False"; python app.py  # Windows
export TESTING=False && python app.py  # Linux
```

## ⚙️ Iniciar Tests ⚙️

Para iniciar las pruebas, ejecuta el siguiente comando según tu sistema operativo:

```bash
$env:TESTING="True"; pytest --cov=app tests.py  # Windows
export TESTING=True && pytest --cov=app tests.py  # Linux
```

## ♒ Excepciones Corrección ♒

### 1. Reportes método "docstring"

- **Función crear_multipropietario** (línea 28): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: crea un objeto Multipropietario.

- **Función crear_formulario** (línea 50): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: crea un objeto Formulario.

- **Función existe_persona_formulario** (línea 66): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: verifica si existe una Persona dentro de un Formulario.

- **Función crear_tablas** (línea 696): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: crea las tablas de la base de datos.

- **Función home** (línea 707): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: muestra la página de inicio de la aplicación.

- **Función obtener_comunas** (línea 736): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: obtiene todas las comunas de una región.

- **Función mostrar_formularios** (línea 748): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: obtiene y muestra todos los formularios de la base de datos.

- **Función mostrar_carga_archivo** (línea 813): No es necesario agregar un comentario al inicio de esta función, ya que el nombre explica claramente su propósito: muestra la página de carga de archivos al renderizar la plantilla correspondiente.

### 2. Deshabilitación del reporte "Too many arguments"

Se deshabilitó el reporte en cuestión, ya que el algoritmo necesita modificar muchas variables para funcionar correctamente.

### 3. Deshabilitación del reporte "Too many local variables"

Se deshabilitó el reporte en cuestión, ya que la función necesita gestionar muchas variables para que el algoritmo funcione adecuadamente.

### 4. Deshabilitación del reporte "Singleton-comparison"

Se deshabilitó el reporte en cuestión, ya que el query presenta conflictos y no funciona con otras soluciones alternativas.
