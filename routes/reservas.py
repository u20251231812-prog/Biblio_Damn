import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
from db import get_db_connection

reservas_bp = Blueprint("reservas", __name__)

def obtener_reservas_activas(id_estudiante=None, es_admin=False):
    conn = get_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT r.*, e.nombre AS estudiante_nombre, l.titulo AS libro_titulo
        FROM reservas r
        JOIN estudiantes e ON r.id_estudiante = e.id_estudiante
        JOIN libros l ON r.id_libro = l.id_libro
        WHERE r.estado = 'Pendiente'
    """
    params = []

    if not es_admin and id_estudiante:
        sql += " AND r.id_estudiante = %s"
        params.append(id_estudiante)

    sql += " ORDER BY r.id_reserva DESC;"

    cur.execute(sql, params)
    reservas = cur.fetchall()
    cur.close()
    conn.close()
    return reservas


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
    es_admin = session.get("rol") == "admin"
    libro_preseleccionado = request.args.get("libro", type=int)

    if request.method == "POST":
        id_estudiante = request.form.get("id_estudiante") if es_admin else session.get("id_estudiante")
        id_libro = request.form.get("id_libro")
        codigo_qr = f"QR-{uuid.uuid4().hex[:8].upper()}"

        if not id_estudiante or not id_libro:
            flash("Debe seleccionar estudiante y libro.", "danger")
        else:
            try:
                # Verificar cupo real: stock físico menos las reservas pendientes actuales
                cur.execute("""
                    SELECT l.stock_disponible - COUNT(r.id_reserva) AS cupo_real
                    FROM libros l
                    LEFT JOIN reservas r ON l.id_libro = r.id_libro AND r.estado = 'Pendiente'
                    WHERE l.id_libro = %s
                    GROUP BY l.id_libro, l.stock_disponible;
                """, (id_libro,))
                resultado = cur.fetchone()

                if not resultado or resultado["cupo_real"] <= 0:
                    flash("No hay ejemplares disponibles: los que quedan ya están reservados por otros estudiantes.", "warning")
                else:
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

    # Solo listar libros que tengan ejemplares libres descontando las reservas pendientes
    cur.execute("""
        SELECT l.id_libro, l.titulo,
               (l.stock_disponible - COUNT(r.id_reserva)) AS stock_disponible
        FROM libros l
        LEFT JOIN reservas r ON l.id_libro = r.id_libro AND r.estado = 'Pendiente'
        GROUP BY l.id_libro, l.titulo, l.stock_disponible
        HAVING (l.stock_disponible - COUNT(r.id_reserva)) > 0
        ORDER BY l.titulo;
    """)
    libros = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "reservas/form.html",
        reserva=None,
        estudiantes=estudiantes,
        libros=libros,
        libro_preseleccionado=libro_preseleccionado
    )


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
    return render_template("reservas/form.html", reserva=reserva, estudiantes=estudiantes, libros=libros, libro_preseleccionado=None)


@reservas_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if session.get("rol") != "admin":
            cur.execute(
                "DELETE FROM reservas WHERE id_reserva = %s AND id_estudiante = %s AND estado = 'Pendiente';",
                (id, session.get("id_estudiante"))
            )
        else:
            cur.execute("DELETE FROM reservas WHERE id_reserva = %s;", (id,))

        conn.commit()
        flash("Reserva cancelada correctamente.", "success")
    except psycopg2.IntegrityError:
        conn.rollback()
        flash("No se puede eliminar la reserva.", "danger")
    finally:
        cur.close()
        conn.close()

    if session.get("rol") != "admin":
        return redirect(url_for("index"))
    return redirect(url_for("reservas.listar"))

@reservas_bp.route("/devolver/<int:id>", methods=["POST"])
def devolver(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_libro, estado FROM reservas WHERE id_reserva = %s;", (id,))
        reserva = cur.fetchone()

        if not reserva:
            flash("Reserva no encontrada.", "danger")
        elif reserva["estado"] != "Reclamado":
            flash("Solo se pueden devolver libros que estén en estado 'Reclamado'.", "warning")
        else:
            cur.execute("UPDATE reservas SET estado = 'Devuelto' WHERE id_reserva = %s;", (id,))
            cur.execute("UPDATE libros SET stock_disponible = stock_disponible + 1 WHERE id_libro = %s;", (reserva["id_libro"],))
            conn.commit()
            flash("Libro marcado como Devuelto y sumado al inventario.", "success")
    except psycopg2.Error:
        conn.rollback()
        flash("Error al registrar la devolución.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("reservas.listar"))

@reservas_bp.route("/escanear", methods=["GET", "POST"])
def escanear_qr():
    if request.method == "POST":
        codigo_qr = request.form.get("codigo_qr", "").strip().upper()
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT r.*, l.stock_disponible
                FROM reservas r
                JOIN libros l ON r.id_libro = l.id_libro
                WHERE r.codigo_qr = %s;
            """, (codigo_qr,))
            reserva = cur.fetchone()

            if not reserva:
                flash("Código QR no encontrado en el sistema.", "danger")
            elif reserva["estado"] != "Pendiente":
                flash(f"Este QR ya fue procesado (Estado actual: {reserva['estado']}).", "warning")
            elif reserva["stock_disponible"] <= 0:
                flash("No se puede entregar: este libro ya no tiene unidades disponibles en inventario.", "danger")
            else:
                cur.execute("UPDATE reservas SET estado = 'Reclamado' WHERE id_reserva = %s;", (reserva["id_reserva"],))
                cur.execute("UPDATE libros SET stock_disponible = stock_disponible - 1 WHERE id_libro = %s;", (reserva["id_libro"],))
                conn.commit()
                flash("¡Libro entregado con éxito! Estado actualizado a Reclamado.", "success")
        except psycopg2.Error:
            conn.rollback()
            flash("No se pudo completar la entrega por falta de stock disponible.", "danger")
        finally:
            cur.close()
            conn.close()

    pendientes = obtener_reservas_activas(es_admin=True)
    return render_template("reservas/escaner_qr.html", pendientes=pendientes)
