Aplicación web para administrar el catálogo de una biblioteca universitaria y gestionar reservas de libros mediante códigos QR. 
Está desarrollada con Flask (Python) y PostgreSQL.
El estudiante reserva un libro desde el catálogo y recibe un comprobante con un código QR (por ejemplo, QR-RES-1009). 
Lo presenta en el mostrador, donde un administrador lo valida para entregarle el ejemplar.

--como instalarlo 
-Requisitos previos
Python 3.9 o superior
PostgreSQL (y opcionalmente pgAdmin)
Git

-Clonar el repositorio
git clone <URL-DEL-REPOSITORIO>
cd Biblio_Damn
-Crear el entorno virtual e instalar dependencias
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

-Crear la base de datos
Crea una base de datos vacía en PostgreSQL (por ejemplo, biblioteca_db).
Ejecuta en ella el script SQL del proyecto  
En pgAdmin: clic derecho sobre la base → Query Tool → pegar el script → Ejecutar.

-Configurar las variables de entorno

Crea un archivo .env en la raíz del proyecto 
FLASK_SECRET_KEY=pon_aqui_una_clave_larga_y_aleatoria
DB_HOST=localhost
DB_PORT=5432
DB_NAME=biblioteca_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña_de_postgres

-Asignar contraseñas iniciales

Si la tabla estudiantes tiene la columna password_hash, ejecuta una sola vez:
python crear_passwords.py
El script asigna la contraseña inicial 1234

-Iniciar la aplicación
python app.py
