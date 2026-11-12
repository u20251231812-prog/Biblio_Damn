import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
import psycopg2
from db import get_db_connection

reservas_bp = Blueprint("reservas", __name__)

@reservas_bp.route("/")
def listar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, e.nombre AS estudiante_nombre, l.titulo AS libro_titulo
        FROM reservas r
        JOIN estudiantes e ON r.id_estudiante = e.id_estudiante
        JOIN libros l ON r.id_libro = l.id_libro
        ORDER BY r.id_reserva DESC;
    """)
    reservas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("reservas/list.html", reservas=reservas)

@reservas_bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        id_estudiante = request.form.get("id_estudiante")
        id_libro = request.form.get("id_libro")
        # Genera código único para el QR del estudiante
        codigo_qr = f"QR-{uuid.uuid4().hex[:8].upper()}"

        if not id_estudiante or not id_libro:
            flash("Debe seleccionar estudiante y libro.", "danger")
        else:
            try:
                cur.execute("""
                    INSERT INTO reservas (id_estudiante, id_libro, codigo_qr, estado)
                    VALUES (%s, %s, %s, 'Pendiente');
                """, (id_estudiante, id_libro, codigo_qr))
                conn.commit()
                flash(f"Reserva creada. Código QR generado: {codigo_qr}", "success")
                return redirect(url_for("index"))
            except psycopg2.Error as e:
                conn.rollback()
                flash(f"Error en base de datos: {e}", "danger")

    cur.execute("SELECT * FROM estudiantes ORDER BY nombre;")
    estudiantes = cur.fetchall()
    cur.execute("SELECT * FROM libros WHERE stock_disponible > 0 ORDER BY titulo;")
    libros = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("reservas/form.html", reserva=None, estudiantes=estudiantes, libros=libros)

@reservas_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        id_estudiante = request.form.get("id_estudiante")
        id_libro = request.form.get("id_libro")
        estado = request.form.get("estado")
        try:
            cur.execute("""
                UPDATE reservas SET id_estudiante=%s, id_libro=%s, estado=%s
                WHERE id_reserva=%s;
            """, (id_estudiante, id_libro, estado, id))
            conn.commit()
            flash("Reserva actualizada.", "success")
            return redirect(url_for("reservas.listar"))
        except psycopg2.Error:
            conn.rollback()
            flash("Error al actualizar reserva.", "danger")

    cur.execute("SELECT * FROM reservas WHERE id_reserva = %s;", (id,))
    reserva = cur.fetchone()
    cur.execute("SELECT * FROM estudiantes ORDER BY nombre;")
    estudiantes = cur.fetchall()
    cur.execute("SELECT * FROM libros ORDER BY titulo;")
    libros = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("reservas/form.html", reserva=reserva, estudiantes=estudiantes, libros=libros)

@reservas_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reservas WHERE id_reserva = %s;", (id,))
        conn.commit()
        flash("Reserva eliminada.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar la reserva.", "danger")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("reservas.listar"))

# VISTA PARA LA BIBLIOTECARIA: Escanear/Validar QR cuando el estudiante reclama el libro
@reservas_bp.route("/escanear", methods=["GET", "POST"])
def escanear_qr():
    if request.method == "POST":
        codigo_qr = request.form.get("codigo_qr", "").strip().upper()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservas WHERE codigo_qr = %s;", (codigo_qr,))
        reserva = cur.fetchone()

        if not reserva:
            flash("Código QR no encontrado en el sistema.", "danger")
        elif reserva["estado"] != "Pendiente":
            flash(f"Este QR ya fue procesado (Estado actual: {reserva['estado']}).", "warning")
        else:
            # Cambia estado a Reclamado y descuenta 1 al stock del libro
            cur.execute("UPDATE reservas SET estado = 'Reclamado' WHERE id_reserva = %s;", (reserva["id_reserva"],))
            cur.execute("UPDATE libros SET stock_disponible = stock_disponible - 1 WHERE id_libro = %s;", (reserva["id_libro"],))
            conn.commit()
            flash("¡Libro entregado con éxito! Estado actualizado a Reclamado.", "success")
        cur.close()
        conn.close()
    return render_template("reservas/escaner_qr.html")