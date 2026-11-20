import psycopg2
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "id_estudiante" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id_estudiante, nombre, password_hash, rol FROM estudiantes WHERE LOWER(nombre) = LOWER(%s);",
            (nombre,),
        )
        est = cur.fetchone()
        cur.close()
        conn.close()

        if est and est["password_hash"] and check_password_hash(est["password_hash"], password):
            session.clear()
            session["id_estudiante"] = est["id_estudiante"]
            session["nombre"] = est["nombre"]
            session["rol"] = est["rol"]
            siguiente = request.args.get("next", "")
            if siguiente.startswith("/") and not siguiente.startswith("//"):
                return redirect(siguiente)
            return redirect(url_for("index"))

        flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("auth/login.html", modo="login")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if "id_estudiante" in session:
        return redirect(url_for("index"))

    datos = {"codigo_estudiantil": "", "nombre": "", "correo": ""}

    if request.method == "POST":
        datos["codigo_estudiantil"] = request.form.get("codigo_estudiantil", "").strip()
        datos["nombre"] = request.form.get("nombre", "").strip()
        datos["correo"] = request.form.get("correo", "").strip()
        password = request.form.get("password", "")
        confirmar = request.form.get("confirmar", "")

        if not all([datos["codigo_estudiantil"], datos["nombre"], datos["correo"], password, confirmar]):
            flash("Todos los campos son obligatorios.", "danger")
        elif len(password) < 4:
            flash("La contraseña debe tener al menos 4 caracteres.", "danger")
        elif password != confirmar:
            flash("Las contraseñas no coinciden.", "danger")
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                # El nombre es el usuario para iniciar sesión, así que no puede repetirse
                cur.execute(
                    "SELECT 1 FROM estudiantes WHERE LOWER(nombre) = LOWER(%s);",
                    (datos["nombre"],),
                )
                if cur.fetchone():
                    flash("Ya existe un usuario con ese nombre.", "danger")
                else:
                    # No se envía "rol": la base de datos le asigna 'estudiante' por defecto
                    cur.execute(
                        """
                        INSERT INTO estudiantes (codigo_estudiantil, nombre, correo, password_hash)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (datos["codigo_estudiantil"], datos["nombre"], datos["correo"],
                         generate_password_hash(password)),
                    )
                    conn.commit()
                    flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
                    return redirect(url_for("auth.login"))
            except psycopg2.IntegrityError:
                conn.rollback()
                flash("El código estudiantil o el correo ya está registrado.", "danger")
            finally:
                cur.close()
                conn.close()

    return render_template("auth/login.html", modo="registro", datos=datos)


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("auth.login"))