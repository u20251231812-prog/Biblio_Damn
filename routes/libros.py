from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection

libros_bp = Blueprint("libros", __name__)

@libros_bp.route("/")
def listar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.*, a.nombre AS autor_nombre, c.nombre AS categoria_nombre
        FROM libros l
        JOIN autores a ON l.id_autor = a.id_autor
        JOIN categorias c ON l.id_categoria = c.id_categoria
        ORDER BY l.id_libro;
    """)
    libros = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("libros/list.html", libros=libros)

@libros_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        portada_url = request.form.get("portada_url", "").strip()
        stock = request.form.get("stock_disponible", "0")
        id_categoria = request.form.get("id_categoria")
        id_autor = request.form.get("id_autor")

        if not titulo or not portada_url or not id_categoria or not id_autor:
            flash("Todos los campos son obligatorios.", "danger")
        else:
            try:
                cur.execute("""
                    INSERT INTO libros (titulo, portada_url, stock_disponible, id_categoria, id_autor)
                    VALUES (%s, %s, %s, %s, %s);
                """, (titulo, portada_url, int(stock), id_categoria, id_autor))
                conn.commit()
                flash("Libro agregado al catálogo.", "success")
                return redirect(url_for("libros.listar"))
            except (psycopg2.Error, ValueError):
                conn.rollback()
                flash("Error al guardar el libro. Verifica el stock.", "danger")

    cur.execute("SELECT * FROM categorias ORDER BY nombre;")
    categorias = cur.fetchall()
    cur.execute("SELECT * FROM autores ORDER BY nombre;")
    autores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("libros/form.html", libro=None, categorias=categorias, autores=autores)

@libros_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        portada_url = request.form.get("portada_url", "").strip()
        stock = request.form.get("stock_disponible", "0")
        id_categoria = request.form.get("id_categoria")
        id_autor = request.form.get("id_autor")
        try:
            cur.execute("""
                UPDATE libros SET titulo=%s, portada_url=%s, stock_disponible=%s, id_categoria=%s, id_autor=%s
                WHERE id_libro=%s;
            """, (titulo, portada_url, int(stock), id_categoria, id_autor, id))
            conn.commit()
            flash("Libro actualizado.", "success")
            return redirect(url_for("libros.listar"))
        except (psycopg2.Error, ValueError):
            conn.rollback()
            flash("Error al actualizar el libro.", "danger")

    cur.execute("SELECT * FROM libros WHERE id_libro = %s;", (id,))
    libro = cur.fetchone()
    cur.execute("SELECT * FROM categorias ORDER BY nombre;")
    categorias = cur.fetchall()
    cur.execute("SELECT * FROM autores ORDER BY nombre;")
    autores = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("libros/form.html", libro=libro, categorias=categorias, autores=autores)

@libros_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM libros WHERE id_libro = %s;", (id,))
        conn.commit()
        flash("Libro eliminado.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar: tiene reservas asociadas.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("libros.listar"))