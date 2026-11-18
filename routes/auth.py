from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
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

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("auth.login"))