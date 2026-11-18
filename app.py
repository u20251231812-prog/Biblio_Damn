##Agregar 
from flask import Flask, render_template, request
from config import Config
from db import get_db_connection
from flask import Flask, render_template, request, redirect, url_for, session
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Importar Blueprints
from routes.categorias import categorias_bp
from routes.autores import autores_bp
from routes.estudiantes import estudiantes_bp
from routes.libros import libros_bp, buscar_libros, obtener_filtros
from routes.reservas import reservas_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config.from_object(Config)

# Registrar Blueprints
app.register_blueprint(categorias_bp, url_prefix="/categorias")
app.register_blueprint(autores_bp, url_prefix="/autores")
app.register_blueprint(estudiantes_bp, url_prefix="/estudiantes")
app.register_blueprint(libros_bp, url_prefix="/libros")
app.register_blueprint(reservas_bp, url_prefix="/reservas")
app.register_blueprint(auth_bp)

# Secciones que solo puede abrir un administrador
BLUEPRINTS_ADMIN = {"categorias", "autores", "estudiantes", "libros", "reservas"}

##Bloqueo de todas las páginas si no hay sesión
@app.before_request
def requerir_login():
    if request.endpoint in (None, "static", "auth.login"):
        return
    if "id_estudiante" not in session:
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
    if request.blueprint in BLUEPRINTS_ADMIN and session.get("rol") != "admin":
        flash("No tienes permiso para entrar a esa sección.", "danger")
        return redirect(url_for("index"))


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    id_categoria = request.args.get("categoria", type=int)
    id_autor = request.args.get("autor", type=int)
    solo_disponibles = request.args.get("disponibles") == "1"
    orden = request.args.get("orden", "recientes")

    libros = buscar_libros(q, id_categoria, id_autor, solo_disponibles, orden)
    categorias, autores = obtener_filtros()

    conn = get_db_connection()
    cur = conn.cursor()
    sql = """
        SELECT r.*, l.titulo AS libro_titulo, l.portada_url, e.nombre AS estudiante_nombre
        FROM reservas r
        JOIN libros l ON r.id_libro = l.id_libro
        JOIN estudiantes e ON r.id_estudiante = e.id_estudiante
        WHERE r.estado = 'Pendiente'
    """
    params = []
    if session.get("rol") != "admin":
        sql += " AND r.id_estudiante = %s"
        params.append(session["id_estudiante"])
    sql += " ORDER BY r.id_reserva DESC LIMIT 3;"
    cur.execute(sql, params)
    reservas_activas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "index.html",
        libros=libros, reservas_activas=reservas_activas,
        categorias=categorias, autores=autores,
        q=q, id_categoria=id_categoria, id_autor=id_autor,
        solo_disponibles=solo_disponibles, orden=orden,
    )

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)