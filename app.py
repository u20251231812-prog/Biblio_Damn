from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config

# Importar Blueprints y funciones de consulta
from routes.categorias import categorias_bp
from routes.autores import autores_bp
from routes.estudiantes import estudiantes_bp
from routes.libros import libros_bp, buscar_libros, obtener_filtros
from routes.reservas import reservas_bp, obtener_reservas_activas
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

# Secciones exclusivas de administrador (permitiendo que estudiantes entren a reservas.crear)
BLUEPRINTS_ADMIN = {"categorias", "autores", "estudiantes", "libros"}
RUTAS_ADMIN_RESERVAS = {"reservas.listar", "reservas.editar", "reservas.escanear_qr","reservas.devolver"}

# Bloqueo de todas las páginas si no hay sesión
@app.before_request
def requerir_login():
    if request.endpoint in (None, "static", "auth.login", "auth.registro"):
        return
    if request.endpoint in (None, "static", "auth.login"):
        return
    if "id_estudiante" not in session:
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
    
    if (request.blueprint in BLUEPRINTS_ADMIN or request.endpoint in RUTAS_ADMIN_RESERVAS) and session.get("rol") != "admin":
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

    es_admin = session.get("rol") == "admin"
    reservas_activas = obtener_reservas_activas(session.get("id_estudiante"), es_admin)

    return render_template(
        "index.html",
        libros=libros,
        reservas_activas=reservas_activas,
        categorias=categorias,
        autores=autores,
        q=q,
        id_categoria=id_categoria,
        id_autor=id_autor,
        solo_disponibles=solo_disponibles,
        orden=orden,
    )

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)