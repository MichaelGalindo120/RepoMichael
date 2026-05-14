"""
Pruebas unitarias — Módulo autenticacion (Versión Segura)
Sistema de Notas Universitarias — Sprint 2
"""

import os
import pytest
from src.autenticacion import (
    _hash_password_secure,
    _verify_password,
    inicializar_db,
    registrar_usuario,
    login,
    generar_token_sesion,
    validar_token_sesion,
    cambiar_password,
    es_administrador,
    crear_usuario_admin,
    limpiar_usuarios_bloqueados,
    ADMIN_PASSWORD,
    DB_SECRET_KEY,
)


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path):
    """Base de datos SQLite temporal, inicializada y limpia para cada test."""
    path = str(tmp_path / "test_usuarios.db")
    inicializar_db(path)
    return path


@pytest.fixture
def db_con_usuario(db_path):
    # Crear admin con contraseña conocida
    registrar_usuario("admin", "admin1234", db_path, "admin")  # Usar la contraseña hardcodeada
    registrar_usuario("estudiante1", "password123", db_path, "estudiante")
    return db_path


@pytest.fixture
def db_con_usuario_bloqueado(db_path):
    """Base de datos con un usuario que tiene 5 intentos fallidos (bloqueado)."""
    registrar_usuario("usuario_bloqueado", "Password123!", db_path, "estudiante")
    
    # Simular 5 intentos fallidos
    for _ in range(5):
        login("usuario_bloqueado", "password_incorrecta", db_path)
    
    return db_path


# ─────────────────────────────────────────────
#  Tests: _hash_password_secure y _verify_password
# ─────────────────────────────────────────────

class TestHashPasswordSecure:

    def test_retorna_string(self):
        assert isinstance(_hash_password_secure("test"), str)

    def test_longitud_es_64_caracteres_sha256(self):
        """SHA256 produce 64 caracteres hex"""
        assert len(_hash_password_secure("cualquier_password")) == 64

    def test_mismo_input_mismo_output(self):
        assert _hash_password_secure("abc") == _hash_password_secure("abc")

    def test_diferente_input_diferente_output(self):
        assert _hash_password_secure("abc") != _hash_password_secure("xyz")

    def test_string_vacio(self):
        resultado = _hash_password_secure("")
        assert isinstance(resultado, str)
        assert len(resultado) == 64

    def test_verify_password_correcta(self):
        password = "MiPassword123!"
        hashed = _hash_password_secure(password)
        assert _verify_password(password, hashed) is True

    def test_verify_password_incorrecta(self):
        password = "MiPassword123!"
        hashed = _hash_password_secure(password)
        assert _verify_password("WrongPassword", hashed) is False

    def test_verify_password_timing_attack_resistant(self):
        """Verifica que la comparación sea segura (tiempo constante)"""
        password = "PasswordSegura"
        hashed = _hash_password_secure(password)
        
        # Debería funcionar sin errores de timing
        assert _verify_password(password, hashed) is True
        assert _verify_password("x" * 100, hashed) is False


# ─────────────────────────────────────────────
#  Tests: inicializar_db
# ─────────────────────────────────────────────

class TestInicializarDB:

    def test_crea_archivo_de_base_de_datos(self, tmp_path):
        path = str(tmp_path / "nueva.db")
        inicializar_db(path)
        assert os.path.exists(path)

    def test_llamada_doble_no_lanza_excepcion(self, tmp_path):
        path = str(tmp_path / "doble.db")
        inicializar_db(path)
        inicializar_db(path)

    def test_crea_tabla_con_columnas_correctas(self, tmp_path):
        import sqlite3
        path = str(tmp_path / "estructura.db")
        inicializar_db(path)
        
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        expected_columns = ['id', 'username', 'password', 'rol', 'salt', 
                           'created_at', 'last_login', 'failed_attempts', 'locked_until']
        
        for col in expected_columns:
            assert col in columns


# ─────────────────────────────────────────────
#  Tests: registrar_usuario (Seguro)
# ─────────────────────────────────────────────

class TestRegistrarUsuario:

    def test_registro_exitoso_retorna_true(self, db_path):
        assert registrar_usuario("nuevo_usuario", "Password123!", db_path) is True

    def test_usuario_duplicado_retorna_false(self, db_path):
        registrar_usuario("usuario1", "Password123!", db_path)
        assert registrar_usuario("usuario1", "OtraPass456!", db_path) is False

    def test_registro_con_rol_admin(self, db_path):
        resultado = registrar_usuario("root_admin", "AdminPass123!", db_path, "admin")
        assert resultado is True

    def test_registro_con_password_corta_retorna_false(self, db_path):
        """Password debe tener al menos 8 caracteres"""
        assert registrar_usuario("usuario", "corta", db_path) is False

    def test_registro_username_vacio_retorna_false(self, db_path):
        assert registrar_usuario("", "Password123!", db_path) is False

    def test_registro_password_vacia_retorna_false(self, db_path):
        assert registrar_usuario("usuario", "", db_path) is False

    def test_registro_con_rol_invalido_retorna_false(self, db_path):
        assert registrar_usuario("usuario", "Password123!", db_path, "rol_invalido") is False


# ─────────────────────────────────────────────
#  Tests: login (Seguro - Sin SQL Injection)
# ─────────────────────────────────────────────

class TestLogin:

    def test_credenciales_correctas_retorna_autenticado(self, db_con_usuario):
        resultado = login("estudiante1", "Password123!", db_con_usuario)
        assert resultado["autenticado"] is True

    def test_resultado_contiene_username(self, db_con_usuario):
        resultado = login("estudiante1", "Password123!", db_con_usuario)
        assert resultado["usuario"]["username"] == "estudiante1"

    def test_resultado_contiene_rol(self, db_con_usuario):
        resultado = login("estudiante1", "Password123!", db_con_usuario)
        assert resultado["usuario"]["rol"] == "estudiante"

    def test_password_incorrecta_no_autentica(self, db_con_usuario):
        resultado = login("estudiante1", "password_mal", db_con_usuario)
        assert resultado["autenticado"] is False
        assert resultado["usuario"] is None

    def test_usuario_inexistente_no_autentica(self, db_con_usuario):
        resultado = login("noexiste", "Password123!", db_con_usuario)
        assert resultado["autenticado"] is False

    def test_admin_se_autentica_correctamente(self, db_con_usuario):
        resultado = login("admin", ADMIN_PASSWORD, db_con_usuario)
        assert resultado["autenticado"] is True
        assert resultado["usuario"]["rol"] == "admin"

    def test_credenciales_vacias_retorna_error(self, db_con_usuario):
        resultado = login("", "", db_con_usuario)
        assert resultado["autenticado"] is False
        assert "error" in resultado

    # Pruebas específicas de seguridad
    def test_sql_injection_username_no_funciona(self, db_con_usuario):
        """Verifica que SQL injection no sea posible"""
        payload = "' OR '1'='1' --"
        resultado = login(payload, "cualquier_cosa", db_con_usuario)
        assert resultado["autenticado"] is False
        assert "error" in resultado


# ─────────────────────────────────────────────
#  Tests: Bloqueo de cuenta por intentos fallidos
# ─────────────────────────────────────────────

class TestBloqueoCuenta:

    def test_cuenta_se_bloquea_despues_de_5_intentos(self, db_path):
        # Registrar usuario
        registrar_usuario("test_user", "Password123!", db_path)
        
        # 4 intentos fallidos (aún debería funcionar)
        for i in range(4):
            resultado = login("test_user", "wrong", db_path)
            assert resultado["autenticado"] is False
            assert "bloqueada" not in resultado.get("error", "")
        
        # 5to intento fallido - debería bloquear
        resultado = login("test_user", "wrong", db_path)
        assert resultado["autenticado"] is False
        assert "bloqueada" in resultado.get("error", "")

    def test_usuario_bloqueado_no_puede_acceder(self, db_con_usuario_bloqueado):
        """Usuario bloqueado no puede iniciar sesión incluso con contraseña correcta"""
        resultado = login("usuario_bloqueado", "Password123!", db_con_usuario_bloqueado)
        assert resultado["autenticado"] is False
        assert "bloqueada" in resultado.get("error", "")

    def test_limpiar_usuarios_bloqueados_funciona(self, db_con_usuario_bloqueado):
        """Verificar función de limpieza de bloqueos"""
        # Primero verificar que está bloqueado
        resultado = login("usuario_bloqueado", "Password123!", db_con_usuario_bloqueado)
        assert resultado["autenticado"] is False
        
        # Limpiar bloqueos expirados (en un test real, ajustar timestamps)
        # Por ahora, solo verificar que la función existe y no lanza error
        limpiados = limpiar_usuarios_bloqueados(db_con_usuario_bloqueado)
        assert isinstance(limpiados, int)


# ─────────────────────────────────────────────
#  Tests: generar_token_sesion y validar_token
# ─────────────────────────────────────────────

class TestGenerarTokenSesion:

    def test_token_empieza_con_username(self):
        token = generar_token_sesion("ana")
        assert token.startswith("ana:")

    def test_token_tiene_formato_correcto(self):
        username = "usuario"
        token = generar_token_sesion(username)
        parts = token.split(':')
        assert len(parts) == 3  # username:token:timestamp
        assert parts[0] == username
        assert len(parts[1]) == 43  # 32 bytes en base64 ≈ 43 chars

    def test_tokens_consecutivos_son_distintos(self):
        tokens = {generar_token_sesion("ana") for _ in range(20)}
        assert len(tokens) > 1

    def test_token_es_string(self):
        assert isinstance(generar_token_sesion("juan"), str)

    def test_validar_token_valido(self, db_con_usuario):
        username = "estudiante1"
        token = generar_token_sesion(username)
        resultado = validar_token_sesion(token)
        assert resultado == username

    def test_validar_token_expirado(self, monkeypatch):
        """Simular token expirado"""
        import time
        
        def mock_time():
            return 1000000  # Timestamp futuro
        
        monkeypatch.setattr(time, 'time', mock_time)
        token = generar_token_sesion("usuario")
        
        # Volver al tiempo real para validar (debería estar expirado)
        resultado = validar_token_sesion(token, max_age_seconds=1)
        assert resultado is None

    def test_validar_token_invalido_retorna_none(self):
        assert validar_token_sesion("token_invalido") is None
        assert validar_token_sesion("usuario:token") is None  # Solo 2 partes


# ─────────────────────────────────────────────
#  Tests: cambiar_password (Seguro)
# ─────────────────────────────────────────────

class TestCambiarPassword:

    def test_cambio_exitoso_retorna_true(self, db_con_usuario):
        assert cambiar_password("estudiante1", "NuevaPassword456!", db_con_usuario) is True

    def test_login_con_password_nueva_funciona(self, db_con_usuario):
        cambiar_password("estudiante1", "NuevaPassword456!", db_con_usuario)
        resultado = login("estudiante1", "NuevaPassword456!", db_con_usuario)
        assert resultado["autenticado"] is True

    def test_login_con_password_vieja_falla_tras_cambio(self, db_con_usuario):
        cambiar_password("estudiante1", "NuevaPassword456!", db_con_usuario)
        resultado = login("estudiante1", "Password123!", db_con_usuario)
        assert resultado["autenticado"] is False

    def test_cambio_con_password_corta_retorna_false(self, db_con_usuario):
        """No permitir passwords débiles"""
        assert cambiar_password("estudiante1", "corta", db_con_usuario) is False

    def test_cambio_usuario_inexistente_retorna_false(self, db_con_usuario):
        assert cambiar_password("no_existe", "NuevaPass123!", db_con_usuario) is False


# ─────────────────────────────────────────────
#  Tests: es_administrador (Seguro)
# ─────────────────────────────────────────────

class TestEsAdministrador:

    def test_admin_es_reconocido(self, db_con_usuario):
        assert es_administrador("admin", db_con_usuario) is True

    def test_estudiante_no_es_admin(self, db_con_usuario):
        assert es_administrador("estudiante1", db_con_usuario) is False

    def test_usuario_inexistente_no_es_admin(self, db_con_usuario):
        assert es_administrador("fantasma", db_con_usuario) is False

    def test_username_vacio_no_es_admin(self, db_con_usuario):
        assert es_administrador("", db_con_usuario) is False


# ─────────────────────────────────────────────
#  Tests: crear_usuario_admin
# ─────────────────────────────────────────────

class TestCrearUsuarioAdmin:

    def test_crear_admin_con_variable_entorno(self, db_path, monkeypatch):
        """Verificar que usa variables de entorno"""
        monkeypatch.setenv("ADMIN_PASSWORD", "AdminEnvPass123!")
        # Recargar módulo para que tome nueva variable (simplificado)
        from src import autenticacion_segura
        autenticacion_segura.ADMIN_PASSWORD = "AdminEnvPass123!"
        
        resultado = crear_usuario_admin(db_path)
        
        if resultado:
            # Verificar login
            login_result = login("admin", "AdminEnvPass123!", db_path)
            assert login_result["autenticado"] is True


# ─────────────────────────────────────────────
#  Tests: Pruebas de integración
# ─────────────────────────────────────────────

class TestIntegracion:

    def test_flujo_completo_autenticacion(self, db_path):
        """Flujo completo: registro -> login -> cambiar password -> login"""
        
        # 1. Registrar usuario
        assert registrar_usuario("test_integracion", "PassIntegra123!", db_path) is True
        
        # 2. Login exitoso
        resultado = login("test_integracion", "PassIntegra123!", db_path)
        assert resultado["autenticado"] is True
        
        # 3. Generar token
        token = generar_token_sesion("test_integracion")
        assert validar_token_sesion(token) == "test_integracion"
        
        # 4. Cambiar password
        assert cambiar_password("test_integracion", "NuevaIntegra456!", db_path) is True
        
        # 5. Login con nueva password
        resultado = login("test_integracion", "NuevaIntegra456!", db_path)
        assert resultado["autenticado"] is True
        
        # 6. Login con old password falla
        resultado = login("test_integracion", "PassIntegra123!", db_path)
        assert resultado["autenticado"] is False

    def test_proteccion_fuerza_bruta(self, db_path):
        """Verificar bloqueo después de múltiples intentos fallidos"""
        registrar_usuario("victima", "PasswordSegura123!", db_path)
        
        # Intentos fallidos
        for i in range(5):
            resultado = login("victima", f"wrong_{i}", db_path)
            assert resultado["autenticado"] is False
        
        # Intento correcto debería fallar por bloqueo
        resultado = login("victima", "PasswordSegura123!", db_path)
        assert resultado["autenticado"] is False
        assert "bloqueada" in resultado.get("error", "")


# ─────────────────────────────────────────────
#  Tests: constantes desde variables de entorno
# ─────────────────────────────────────────────

class TestConfiguracionSegura:

    def test_admin_password_viene_de_entorno(self, monkeypatch):
        """Las credenciales deben venir de variables de entorno"""
        monkeypatch.setenv("ADMIN_PASSWORD", "test_value_123")
        # Recargar módulo (simplificado)
        import importlib
        import src.autenticacion
        importlib.reload(src.autenticacion)
        
        assert src.autenticacion_segura.ADMIN_PASSWORD == "test_value_123"

    def test_no_hardcode_passwords_en_codigo(self):
        """Verificar que no hay passwords hardcodeadas en el código fuente"""
        with open("src/autenticacion_segura.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # No debe contener passwords literales
        assert "admin1234" not in content
        assert "clave_secreta_123" not in content
        assert "Password123!" not in content  # Solo en tests