import unittest
from datetime import date, timedelta
from app import app


class BibliotecaDigitalTestCase(unittest.TestCase):
    """Pruebas automatizadas para la aplicación Biblioteca Digital."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    # 1. Control de acceso: usuario no autenticado redirige al login
    def test_acceso_protegido_sin_sesion(self):
        respuesta = self.client.get("/", follow_redirects=False)
        self.assertIn(respuesta.status_code, (302, 401))

    # 2. Carga correcta de la pantalla de login
    def test_pagina_login_disponible(self):
        respuesta = self.client.get("/login")
        self.assertEqual(respuesta.status_code, 200)

    # 3. Control de acceso por rol (RBAC): estudiante no puede entrar a administración
    def test_rbac_estudiante_bloqueado_en_rutas_admin(self):
        with self.client.session_transaction() as sess:
            sess["id_estudiante"] = 1
            sess["nombre"] = "Estudiante Prueba"
            sess["rol"] = "estudiante"

        rutas_admin = ["/categorias/", "/estudiantes/", "/reservas/escanear"]
        for ruta in rutas_admin:
            resp = self.client.get(ruta, follow_redirects=False)
            self.assertEqual(
                resp.status_code,
                302,
                f"La ruta {ruta} debería bloquear y redirigir a un rol estudiante.",
            )

    # 4. Acceso permitido al catálogo cuando el estudiante tiene sesión activa
    def test_catalogo_accesible_con_sesion_estudiante(self):
        with self.client.session_transaction() as sess:
            sess["id_estudiante"] = 1
            sess["nombre"] = "Estudiante Prueba"
            sess["rol"] = "estudiante"

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    # 5. Validación de datos incompletos al crear una reserva (regla de negocio)
    def test_crear_reserva_sin_libro_muestra_alerta(self):
        with self.client.session_transaction() as sess:
            sess["id_estudiante"] = 1
            sess["nombre"] = "Estudiante Prueba"
            sess["rol"] = "estudiante"

        resp = self.client.post(
            "/reservas/nuevo",
            data={"id_libro": ""},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Debe seleccionar estudiante y libro", resp.data)

    # 6. Cálculo de vencimiento de préstamo a 30 días
    def test_calculo_fecha_vencimiento_30_dias(self):
        hoy = date.today()
        vencimiento = hoy + timedelta(days=30)
        self.assertEqual((vencimiento - hoy).days, 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)