from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection

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
        if not codigo or not nombre or not correo:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("estudiantes/form.html", estudiante=None)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO estudiantes (codigo_estudiantil, nombre, correo) VALUES (%s, %s, %s);", (codigo, nombre, correo))
            conn.commit()
            flash("Estudiante registrado.", "success")
            return redirect(url_for("estudiantes.listar"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Error: El código estudiantil o el correo ya están registrados.", "danger")
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
        if not codigo or not nombre or not correo:
            flash("Todos los campos son obligatorios.", "danger")
        else:
            try:
                cur.execute("UPDATE estudiantes SET codigo_estudiantil=%s, nombre=%s, correo=%s WHERE id_estudiante=%s;", (codigo, nombre, correo, id))
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