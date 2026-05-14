"""
Módulo 4: Autenticación de Usuarios - Versión Segura
Sistema de Notas Universitarias — Sprint 2
"""

import hashlib
import secrets
import sqlite3
import string
import os
import logging
from typing import Optional, Dict, Any

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN SEGURA DESDE VARIABLES DE ENTORNO
# ============================================

# [FIX] Credenciales desde variables de entorno, no hardcodeadas
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
DB_SECRET_KEY = os.environ.get('DB_SECRET_KEY', '')
PEPPER = os.environ.get('PEPPER', '')  # Sal adicional para hashes

if not ADMIN_PASSWORD or not DB_SECRET_KEY:
    logger.warning("Variables de entorno no configuradas correctamente")

# Caracteres permitidos para tokens (solo alfanumérico seguro)
SAFE_CHARS = string.ascii_letters + string.digits

# ============================================
# FUNCIONES DE HASH SEGURO
# ============================================

def _hash_password_secure(password: str) -> str:
    """
    Hash seguro de contraseña usando SHA-256 con salt y pepper.
    [FIX] Reemplaza MD5 débil con SHA-256 + salt + pepper
    
    NOTA: En producción, usar bcrypt o argon2 (requiere instalación adicional)
    """
    # Salt fijo para el usuario (idealmente único por usuario)
    salt = DB_SECRET_KEY
    
    # Aplicar pepper (secret key adicional)
    peppered = password + PEPPER
    
    # Combinar con salt y aplicar SHA-256
    salted = peppered + salt
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    
    # Aplicar múltiples iteraciones para fortalecer (key stretching)
    for _ in range(100000):  # 100k iteraciones como bcrypt
        hashed = hashlib.sha256(hashed.encode()).hexdigest()
    
    return hashed


def _verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash almacenado.
    [FIX] Verificación segura sin vulnerabilidades de timing
    """
    # Calcular hash de la contraseña ingresada
    test_hash = _hash_password_secure(password)
    
    # Comparación segura (tiempo constante)
    return secrets.compare_digest(test_hash, hashed_password)


# ============================================
# INICIALIZACIÓN DE BASE DE DATOS
# ============================================

def inicializar_db(db_path: str) -> None:
    """
    Crea la tabla de usuarios si no existe.
    [FIX] Schema mejorado con índices y campos para auditoría
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla principal con campos mejorados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'estudiante',
            salt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            CONSTRAINT valid_rol CHECK (rol IN ('estudiante', 'admin', 'profesor'))
        )
    """)
    
    # Índice para búsquedas rápidas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON usuarios(username)")
    
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada correctamente")


# ============================================
# REGISTRO DE USUARIOS (SEGURO)
# ============================================

def registrar_usuario(username: str, password: str, db_path: str, rol: str = "estudiante") -> bool:
    """
    Registra un nuevo usuario en la base de datos.
    [FIX] Query parametrizada + validación de inputs + manejo específico de errores
    """
    # Validaciones de entrada
    if not username or not password:
        logger.error("Username o password vacíos")
        return False
    
    if len(password) < 8:
        logger.error("Password muy débil: mínimo 8 caracteres")
        return False
    
    if rol not in ['estudiante', 'admin', 'profesor']:
        logger.error(f"Rol inválido: {rol}")
        return False
    
    try:
        hashed = _hash_password_secure(password)
        
        # [FIX] Query parametrizada - SEGURA contra SQL Injection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            (username, hashed, rol)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Usuario '{username}' registrado exitosamente con rol '{rol}'")
        return True
        
    except sqlite3.IntegrityError:
        logger.warning(f"Intento de registro duplicado: '{username}'")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al registrar '{username}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al registrar '{username}': {e}")
        return False


# ============================================
# LOGIN SEGURO (SIN SQL INJECTION)
# ============================================

def login(username: str, password: str, db_path: str) -> Dict[str, Any]:
    """
    Autentica al usuario contra la base de datos.
    [FIX] SQL Injection eliminado + manejo de intentos fallidos + bloqueo de cuenta
    """
    if not username or not password:
        logger.warning("Intento de login con credenciales vacías")
        return {"autenticado": False, "usuario": None, "error": "Credenciales requeridas"}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # [FIX] Query parametrizada - COMPLETAMENTE SEGURA
        cursor.execute(
            "SELECT id, username, password, rol, failed_attempts, locked_until FROM usuarios WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            logger.warning(f"Intento de login con usuario inexistente: '{username}'")
            return {"autenticado": False, "usuario": None, "error": "Usuario o contraseña incorrectos"}
        
        user_id, db_username, db_password, rol, failed_attempts, locked_until = row
        
        # Verificar si la cuenta está bloqueada
        import datetime
        if locked_until:
            if datetime.datetime.now() < datetime.datetime.fromisoformat(locked_until):
                conn.close()
                logger.warning(f"Cuenta bloqueada para '{username}' hasta {locked_until}")
                return {"autenticado": False, "usuario": None, "error": "Cuenta bloqueada. Intente más tarde"}
        
        # Verificar contraseña
        if _verify_password(password, db_password):
            # Login exitoso - resetear intentos fallidos
            cursor.execute(
                "UPDATE usuarios SET failed_attempts = 0, last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Login exitoso para '{username}' con rol '{rol}'")
            return {
                "autenticado": True,
                "usuario": {"id": user_id, "username": db_username, "rol": rol},
                "error": None
            }
        else:
            # Login fallido - incrementar contador
            new_attempts = (failed_attempts or 0) + 1
            lock_until = None
            
            # Bloquear después de 5 intentos fallidos
            if new_attempts >= 5:
                from datetime import datetime, timedelta
                lock_until = (datetime.now() + timedelta(minutes=15)).isoformat()
                logger.warning(f"Cuenta '{username}' bloqueada por 15 minutos (5 intentos fallidos)")
            
            cursor.execute(
                "UPDATE usuarios SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                (new_attempts, lock_until, user_id)
            )
            conn.commit()
            conn.close()
            
            logger.warning(f"Login fallido para '{username}' - Intento #{new_attempts}")
            return {"autenticado": False, "usuario": None, "error": "Usuario o contraseña incorrectos"}
            
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos en login para '{username}': {e}")
        return {"autenticado": False, "usuario": None, "error": "Error interno del sistema"}
    except Exception as e:
        logger.error(f"Error inesperado en login para '{username}': {e}")
        return {"autenticado": False, "usuario": None, "error": "Error interno del sistema"}


# ============================================
# TOKEN DE SESIÓN CRIPTOGRÁFICAMENTE SEGURO
# ============================================

def generar_token_sesion(username: str) -> str:
    """
    Genera un token de sesión para el usuario.
    [FIX] Reemplaza random.choice() con secrets.token_urlsafe() criptográficamente seguro
    """
    # [FIX] Token criptográficamente seguro (128 bits de entropía)
    token = secrets.token_urlsafe(32)
    
    # Incluir timestamp para expiración
    import time
    timestamp = int(time.time())
    
    return f"{username}:{token}:{timestamp}"


def validar_token_sesion(token: str, max_age_seconds: int = 3600) -> Optional[str]:
    """
    Valida un token de sesión y retorna el username si es válido.
    [NEW] Función de validación con expiración
    """
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return None
        
        username, token_value, timestamp = parts
        
        # Verificar expiración
        import time
        if int(time.time()) - int(timestamp) > max_age_seconds:
            logger.warning(f"Token expirado para '{username}'")
            return None
        
        # En producción, aquí se validaría contra una tabla de tokens activos
        logger.info(f"Token válido para '{username}'")
        return username
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error al validar token: {e}")
        return None


# ============================================
# CAMBIO DE CONTRASEÑA SEGURO
# ============================================

def cambiar_password(username: str, nueva_password: str, db_path: str) -> bool:
    """
    Cambia la contraseña de un usuario.
    [FIX] SQL Injection eliminado + validación de fortaleza
    """
    if not username or not nueva_password:
        logger.error("Username o nueva password vacíos")
        return False
    
    if len(nueva_password) < 8:
        logger.error("Nueva password demasiado débil")
        return False
    
    try:
        hashed = _hash_password_secure(nueva_password)
        
        # [FIX] Query parametrizada - SEGURA
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET password = ? WHERE username = ?",
            (hashed, username)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            logger.warning(f"Intento de cambio de password para usuario inexistente: '{username}'")
            return False
        
        conn.commit()
        conn.close()
        
        logger.info(f"Password actualizado exitosamente para '{username}'")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al cambiar password para '{username}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al cambiar password para '{username}': {e}")
        return False


# ============================================
# VERIFICACIÓN DE ADMINISTRADOR SEGURA
# ============================================

def es_administrador(username: str, db_path: str) -> bool:
    """
    Verifica si el usuario tiene rol de administrador.
    [FIX] SQL Injection eliminado + manejo de errores específico
    """
    if not username:
        logger.warning("Username vacío al verificar admin")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # [FIX] Query parametrizada - SEGURA
        cursor.execute(
            "SELECT rol FROM usuarios WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] == "admin":
            logger.info(f"Verificación de admin exitosa para '{username}'")
            return True
        
        logger.debug(f"Usuario '{username}' no es administrador (rol: {row[0] if row else 'inexistente'})")
        return False
        
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos al verificar admin para '{username}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al verificar admin para '{username}': {e}")
        return False


# ============================================
# FUNCIONES ADICIONALES DE SEGURIDAD
# ============================================

def crear_usuario_admin(db_path: str) -> bool:
    """
    Crea el usuario administrador inicial usando variables de entorno.
    [FIX] Usa variables de entorno en lugar de valores hardcodeados
    """
    if not ADMIN_PASSWORD:
        logger.error("ADMIN_PASSWORD no configurado en variables de entorno")
        return False
    
    return registrar_usuario("admin", ADMIN_PASSWORD, db_path, "admin")


def limpiar_usuarios_bloqueados(db_path: str) -> int:
    """
    Limpia las cuentas bloqueadas después de su tiempo de expiración.
    [NEW] Mantenimiento de seguridad
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE usuarios SET locked_until = NULL WHERE locked_until <= CURRENT_TIMESTAMP"
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Se desbloquearon {affected} cuentas expiradas")
        return affected
        
    except sqlite3.Error as e:
        logger.error(f"Error al limpiar usuarios bloqueados: {e}")
        return 0


# ============================================
# EJEMPLO DE USO SEGURO
# ============================================

if __name__ == "__main__":
    # Configuración inicial
    DATABASE_PATH = "universidad_segura.db"
    
    # Inicializar
    inicializar_db(DATABASE_PATH)
    crear_usuario_admin(DATABASE_PATH)
    
    # Registrar usuario normal
    registrar_usuario("juan_perez", "Password123!", DATABASE_PATH, "estudiante")
    
    # Login seguro
    resultado = login("juan_perez", "Password123!", DATABASE_PATH)
    print(f"Login exitoso: {resultado['autenticado']}")
    
    if resultado['autenticado']:
        # Generar token de sesión
        token = generar_token_sesion(resultado['usuario']['username'])
        print(f"Token generado: {token}")
        
        # Validar token
        username = validar_token_sesion(token)
        print(f"Token válido para: {username}")
    
    # Verificar admin
    print(f"¿juan_perez es admin? {es_administrador('juan_perez', DATABASE_PATH)}")
    print(f"¿admin es admin? {es_administrador('admin', DATABASE_PATH)}")