from werkzeug.security import generate_password_hash
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT id_estudiante FROM estudiantes WHERE password_hash IS NULL;")
for fila in cur.fetchall():
    cur.execute(
        "UPDATE estudiantes SET password_hash = %s WHERE id_estudiante = %s;",
        (generate_password_hash("1234"), fila["id_estudiante"]),
    )
conn.commit()
cur.close()
conn.close()
print("Contraseñas actualizadas")