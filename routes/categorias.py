from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection

categorias_bp = Blueprint("categorias", __name__)

@categorias_bp.route("/")
def listar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categorias ORDER BY id_categoria;")
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("categorias/list.html", categorias=datos)

@categorias_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
            return render_template("categorias/form.html", categoria=None)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO categorias (nombre) VALUES (%s);", (nombre,))
            conn.commit()
            flash("Categoría creada correctamente.", "success")
            return redirect(url_for("categorias.listar"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Error: Esa categoría ya existe.", "danger")
        finally:
            cur.close()
            conn.close()
    return render_template("categorias/form.html", categoria=None)

@categorias_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
        else:
            try:
                cur.execute("UPDATE categorias SET nombre = %s WHERE id_categoria = %s;", (nombre, id))
                conn.commit()
                flash("Categoría actualizada.", "success")
                return redirect(url_for("categorias.listar"))
            except psycopg2.IntegrityError:
                conn.rollback()
                flash("Error: Nombre duplicado.", "danger")
    cur.execute("SELECT * FROM categorias WHERE id_categoria = %s;", (id,))
    categoria = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("categorias/form.html", categoria=categoria)

@categorias_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM categorias WHERE id_categoria = %s;", (id,))
        conn.commit()
        flash("Registro eliminado.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar: tiene libros asociados.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("categorias.listar"))