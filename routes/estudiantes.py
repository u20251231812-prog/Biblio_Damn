from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection
from werkzeug.security import generate_password_hash
estudiantes_bp = Blueprint("estudiantes", __name__)

@estudiantes_bp.route("/")
def listar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM estudiantes ORDER BY id_estudiante;")
    estudiantes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("estudiantes/list.html", estudiantes=estudiantes)

@estudiantes_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        codigo = request.form.get("codigo_estudiantil", "").strip()
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "")

        if not codigo or not nombre or not correo or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("estudiantes/form.html", estudiante=None)

        if len(password) < 4:
            flash("La contraseña debe tener al menos 4 caracteres.", "danger")
            return render_template("estudiantes/form.html", estudiante=None)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # El nombre es el usuario para iniciar sesión, así que no puede repetirse
            cur.execute(
                "SELECT 1 FROM estudiantes WHERE LOWER(nombre) = LOWER(%s);",
                (nombre,)
            )
            if cur.fetchone():
                flash("Ya existe un estudiante con ese nombre.", "danger")
            else:
                cur.execute("""
                    INSERT INTO estudiantes (codigo_estudiantil, nombre, correo, password_hash)
                    VALUES (%s, %s, %s, %s);
                """, (codigo, nombre, correo, generate_password_hash(password)))
                conn.commit()
                flash("Estudiante agregado.", "success")
                return redirect(url_for("estudiantes.listar"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("El código estudiantil o el correo ya existe.", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("estudiantes/form.html", estudiante=None)

@estudiantes_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        codigo = request.form.get("codigo_estudiantil", "").strip()
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        password = request.form.get("password", "")

        if not codigo or not nombre or not correo:
            flash("Todos los campos son obligatorios.", "danger")
        elif password and len(password) < 4:
            flash("La contraseña debe tener al menos 4 caracteres.", "danger")
        else:
            try:
                if password:
                    cur.execute("""
                        UPDATE estudiantes
                        SET codigo_estudiantil=%s, nombre=%s, correo=%s, password_hash=%s
                        WHERE id_estudiante=%s;
                    """, (codigo, nombre, correo, generate_password_hash(password), id))
                else:
                    cur.execute("""
                        UPDATE estudiantes
                        SET codigo_estudiantil=%s, nombre=%s, correo=%s
                        WHERE id_estudiante=%s;
                    """, (codigo, nombre, correo, id))
                conn.commit()
                flash("Estudiante actualizado.", "success")
                return redirect(url_for("estudiantes.listar"))
            except psycopg2.IntegrityError:
                conn.rollback()
                flash("Error: Código o correo duplicado.", "danger")

    cur.execute("SELECT * FROM estudiantes WHERE id_estudiante = %s;", (id,))
    estudiante = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("estudiantes/form.html", estudiante=estudiante)

@estudiantes_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM estudiantes WHERE id_estudiante = %s;", (id,))
        conn.commit()
        flash("Estudiante eliminado.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar: tiene reservas asociadas.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("estudiantes.listar"))