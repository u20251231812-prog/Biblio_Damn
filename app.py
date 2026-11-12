from flask import Flask, render_template
from config import Config
from db import get_db_connection

# Importar Blueprints
from routes.categorias import categorias_bp
from routes.autores import autores_bp
from routes.estudiantes import estudiantes_bp
from routes.libros import libros_bp
from routes.reservas import reservas_bp

app = Flask(__name__)
app.config.from_object(Config)

# Registrar Blueprints
app.register_blueprint(categorias_bp, url_prefix="/categorias")
app.register_blueprint(autores_bp, url_prefix="/autores")
app.register_blueprint(estudiantes_bp, url_prefix="/estudiantes")
app.register_blueprint(libros_bp, url_prefix="/libros")
app.register_blueprint(reservas_bp, url_prefix="/reservas")

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    # Trae libros para el catálogo visual con portada
    cur.execute("""
        SELECT l.*, a.nombre AS autor_nombre, c.nombre AS categoria_nombre
        FROM libros l
        JOIN autores a ON l.id_autor = a.id_autor
        JOIN categorias c ON l.id_categoria = c.id_categoria
        ORDER BY l.id_libro DESC;
    """)
    libros = cur.fetchall()

    # Trae reservas activas (Pendientes) para mostrar el QR en pantalla
    cur.execute("""
        SELECT r.*, l.titulo AS libro_titulo, l.portada_url, e.nombre AS estudiante_nombre
        FROM reservas r
        JOIN libros l ON r.id_libro = l.id_libro
        JOIN estudiantes e ON r.id_estudiante = e.id_estudiante
        WHERE r.estado = 'Pendiente'
        ORDER BY r.id_reserva DESC LIMIT 3;
    """)
    reservas_activas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", libros=libros, reservas_activas=reservas_activas)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)