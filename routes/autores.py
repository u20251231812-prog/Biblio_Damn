from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection

autores_bp = Blueprint("autores", __name__)

@autores_bp.route("/")
def listar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM autores ORDER BY id_autor;")
    autores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("autores/list.html", autores=autores)

@autores_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        nacionalidad = request.form.get("nacionalidad", "").strip()
        if not nombre or not nacionalidad:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("autores/form.html", autor=None)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO autores (nombre, nacionalidad) VALUES (%s, %s);", (nombre, nacionalidad))
            conn.commit()
            flash("Autor creado correctamente.", "success")
            return redirect(url_for("autores.listar"))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"Error en base de datos: {e}", "danger")
        finally:
            cur.close()
            conn.close()
    return render_template("autores/form.html", autor=None)

@autores_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        nacionalidad = request.form.get("nacionalidad", "").strip()
        if not nombre or not nacionalidad:
            flash("Todos los campos son obligatorios.", "danger")
        else:
            try:
                cur.execute("UPDATE autores SET nombre=%s, nacionalidad=%s WHERE id_autor=%s;", (nombre, nacionalidad, id))
                conn.commit()
                flash("Autor actualizado.", "success")
                return redirect(url_for("autores.listar"))
            except psycopg2.Error:
                conn.rollback()
                flash("Error al actualizar.", "danger")
    cur.execute("SELECT * FROM autores WHERE id_autor = %s;", (id,))
    autor = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("autores/form.html", autor=autor)

@autores_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM autores WHERE id_autor = %s;", (id,))
        conn.commit()
        flash("Autor eliminado.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar: tiene libros registrados.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("autores.listar"))