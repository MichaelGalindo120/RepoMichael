"""
Pruebas unitarias — Módulo reportes (Versión Refactorizada)
Sistema de Notas Universitarias — Sprint 2
"""

import pytest
from src.estudiantes import Estudiante, RegistroEstudiantes
from src.materias import Materia, RegistroMaterias
from src.notas import Trabajo, GestorNotas
from src.reportes import (
    reporte_general,
    ranking_estudiantes,
    generar_reporte_csv,
    reporte_detallado_estudiante,
    _clasificar_trabajo,
    FORMATO_FECHA,
    VERSION_REPORTE,
)


# ─────────────────────────────────────────────
#  Fixtures (Mejoradas)
# ─────────────────────────────────────────────

@pytest.fixture
def est1():
    return Estudiante("E001", "Ana García", "ana@test.com")


@pytest.fixture
def est2():
    return Estudiante("E002", "Carlos Mejía", "carlos@test.com")


@pytest.fixture
def est3():
    return Estudiante("E003", "Luis Pérez", "luis@test.com")


@pytest.fixture
def mat1():
    return Materia("CS101", "Calidad del Software", 3)


@pytest.fixture
def mat2():
    return Materia("IS201", "Ingeniería de Requerimientos", 3)


@pytest.fixture
def gestor_con_clasificaciones(est1, est2, est3, mat1, mat2):
    """GestorNotas con trabajos que cubren todas las clasificaciones posibles"""
    g = GestorNotas()
    g.asignar(Trabajo(est1, mat1, "Parcial 1", 5.0))    # Excelente
    g.asignar(Trabajo(est1, mat2, "Quiz 1", 4.6))       # Sobresaliente
    g.asignar(Trabajo(est2, mat1, "Parcial 1", 3.5))    # Aprobado
    g.asignar(Trabajo(est2, mat2, "Quiz 1", 2.8))       # Reprobado
    g.asignar(Trabajo(est3, mat1, "Parcial 1", 1.0))    # Reprobado Grave
    return g


@pytest.fixture
def registro_est_basico(est1, est2):
    r = RegistroEstudiantes()
    r.registrar(est1)
    r.registrar(est2)
    return r


@pytest.fixture
def registro_est_completo(est1, est2, est3):
    r = RegistroEstudiantes()
    r.registrar(est1)
    r.registrar(est2)
    r.registrar(est3)
    return r


@pytest.fixture
def registro_mat_basico(mat1, mat2):
    r = RegistroMaterias()
    r.registrar(mat1)
    r.registrar(mat2)
    return r


@pytest.fixture
def gestor_con_datos(est1, est2, mat1, mat2):
    g = GestorNotas()
    g.asignar(Trabajo(est1, mat1, "Parcial 1", 4.0))
    g.asignar(Trabajo(est1, mat2, "Quiz 1", 3.5))
    g.asignar(Trabajo(est2, mat1, "Parcial 1", 2.8))
    return g


# ─────────────────────────────────────────────
#  Tests: reporte_general (sin divisiones por cero)
# ─────────────────────────────────────────────

class TestReporteGeneral:

    def test_reporte_retorna_totales_correctos(self, gestor_con_datos, registro_est_basico, registro_mat_basico):
        reporte = reporte_general(gestor_con_datos, registro_est_basico, registro_mat_basico)
        
        assert reporte["total_estudiantes"] == 2
        assert reporte["total_materias"] == 2
        assert reporte["total_trabajos"] == 3

    def test_reporte_promedio_global_es_float(self, gestor_con_datos, registro_est_basico, registro_mat_basico):
        reporte = reporte_general(gestor_con_datos, registro_est_basico, registro_mat_basico)
        assert isinstance(reporte["promedio_global"], float)

    def test_reporte_promedio_por_materia_es_float(self, gestor_con_datos, registro_est_basico, registro_mat_basico):
        reporte = reporte_general(gestor_con_datos, registro_est_basico, registro_mat_basico)
        assert isinstance(reporte["promedio_por_materia"], float)

    def test_sin_estudiantes_no_lanza_error(self, mat1):
        """[FIX] Ya no lanza ZeroDivisionError, maneja el caso correctamente"""
        gestor = GestorNotas()
        reg_est_vacio = RegistroEstudiantes()
        reg_mat = RegistroMaterias()
        reg_mat.registrar(mat1)
        
        # Ya no debe lanzar excepción
        reporte = reporte_general(gestor, reg_est_vacio, reg_mat)
        
        assert reporte["total_estudiantes"] == 0
        assert reporte["promedio_global"] == 0.0
        assert reporte["total_materias"] == 1
        assert reporte["promedio_por_materia"] == 0.0  # Sin trabajos
        assert reporte["total_trabajos"] == 0

    def test_sin_materias_no_lanza_error(self, est1):
        """[FIX] Ya no lanza ZeroDivisionError, maneja el caso correctamente"""
        gestor = GestorNotas()
        reg_est = RegistroEstudiantes()
        reg_est.registrar(est1)
        reg_mat_vacio = RegistroMaterias()
        
        reporte = reporte_general(gestor, reg_est, reg_mat_vacio)
        
        assert reporte["total_estudiantes"] == 1
        assert reporte["total_materias"] == 0
        assert reporte["promedio_por_materia"] == 0.0

    def test_sistema_vacio_no_lanza_error(self):
        """Sistema completamente vacío debe funcionar sin errores"""
        gestor = GestorNotas()
        reg_est_vacio = RegistroEstudiantes()
        reg_mat_vacio = RegistroMaterias()
        
        reporte = reporte_general(gestor, reg_est_vacio, reg_mat_vacio)
        
        assert reporte["total_estudiantes"] == 0
        assert reporte["total_materias"] == 0
        assert reporte["promedio_global"] == 0.0
        assert reporte["promedio_por_materia"] == 0.0
        assert reporte["total_trabajos"] == 0

    def test_reporte_incluye_metadata(self, gestor_con_datos, registro_est_basico, registro_mat_basico):
        reporte = reporte_general(gestor_con_datos, registro_est_basico, registro_mat_basico)
        
        assert "version_reporte" in reporte
        assert "formato_fecha" in reporte
        assert reporte["version_reporte"] == VERSION_REPORTE
        assert reporte["formato_fecha"] == FORMATO_FECHA


# ─────────────────────────────────────────────
#  Tests: ranking_estudiantes (mejorados)
# ─────────────────────────────────────────────

class TestRankingEstudiantes:

    def test_ranking_ordenado_de_mayor_a_menor(self, gestor_con_datos, registro_est_basico):
        ranking = ranking_estudiantes(gestor_con_datos, registro_est_basico)
        promedios = [item["promedio"] for item in ranking]
        assert promedios == sorted(promedios, reverse=True)

    def test_ranking_incluye_todos_los_estudiantes(self, gestor_con_datos, registro_est_basico):
        ranking = ranking_estudiantes(gestor_con_datos, registro_est_basico)
        assert len(ranking) == 2

    def test_ranking_estructura_de_cada_item(self, gestor_con_datos, registro_est_basico):
        ranking = ranking_estudiantes(gestor_con_datos, registro_est_basico)
        for item in ranking:
            assert "codigo" in item
            assert "nombre" in item
            assert "promedio" in item

    def test_ranking_vacio_con_registro_sin_estudiantes(self):
        ranking = ranking_estudiantes(GestorNotas(), RegistroEstudiantes())
        assert ranking == []

    def test_primer_lugar_tiene_mayor_promedio(self, gestor_con_datos, registro_est_basico):
        """[FIX] No asume código específico, verifica la propiedad"""
        ranking = ranking_estudiantes(gestor_con_datos, registro_est_basico)
        
        # Verificar que el primero tiene el promedio más alto
        assert ranking[0]["promedio"] >= ranking[1]["promedio"] if len(ranking) > 1 else True
        
        # Verificar consistencia con cálculo directo
        mejor_promedio = max(gestor_con_datos.promedio_estudiante("E001"), 
                            gestor_con_datos.promedio_estudiante("E002"))
        assert ranking[0]["promedio"] == mejor_promedio


# ─────────────────────────────────────────────
#  Tests: generar_reporte_csv (antes GENERAR_REPORTE_CSV)
# ─────────────────────────────────────────────

class TestGenerarReporteCSV:

    def test_csv_incluye_encabezado(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        primera_linea = salida.strip().split("\n")[0]
        
        assert "Estudiante" in primera_linea
        assert "Materia" in primera_linea
        assert "Trabajo" in primera_linea
        assert "Nota" in primera_linea
        assert "Estado" in primera_linea
        assert "Categoria" in primera_linea

    def test_csv_sin_estudiantes_solo_tiene_encabezado(self):
        salida = generar_reporte_csv(GestorNotas(), RegistroEstudiantes())
        lineas = [l for l in salida.strip().split("\n") if l]
        
        # Solo el encabezado
        assert len(lineas) == 1

    def test_csv_incluye_version_reporte(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        assert VERSION_REPORTE in salida

    def test_csv_contiene_todos_los_estudiantes(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        
        assert "Ana García" in salida
        assert "Carlos Mejía" in salida
        assert "Luis Pérez" in salida

    def test_csv_clasifica_todas_las_categorias(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        
        assert "Excelente" in salida
        assert "Sobresaliente" in salida
        assert "Aprobado" in salida
        assert "Reprobado" in salida
        assert "Reprobado Grave" in salida

    def test_csv_retorna_string(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        assert isinstance(salida, str)

    def test_csv_formato_correcto(self, gestor_con_clasificaciones, registro_est_completo):
        salida = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        lineas = salida.strip().split("\n")
        
        # Verificar que todas las líneas tienen el mismo número de columnas
        num_columnas = len(lineas[0].split(','))
        for linea in lineas[1:]:
            assert len(linea.split(',')) == num_columnas


# ─────────────────────────────────────────────
#  Tests: reporte_detallado_estudiante (nueva funcionalidad)
# ─────────────────────────────────────────────

class TestReporteDetalladoEstudiante:

    def test_reporte_estudiante_existente(self, gestor_con_clasificaciones, registro_est_completo):
        resultado = reporte_detallado_estudiante(
            gestor_con_clasificaciones, 
            registro_est_completo, 
            "E001"
        )
        
        assert "estudiante" in resultado
        assert resultado["estudiante"]["codigo"] == "E001"
        assert "promedio_general" in resultado
        assert "total_trabajos" in resultado
        assert "trabajos_aprobados" in resultado
        assert "trabajos_reprobados" in resultado
        assert "detalle_por_materia" in resultado

    def test_reporte_estudiante_sin_trabajos(self, registro_est_completo):
        gestor_vacio = GestorNotas()
        resultado = reporte_detallado_estudiante(
            gestor_vacio, 
            registro_est_completo, 
            "E001"
        )
        
        assert resultado["total_trabajos"] == 0
        assert resultado["promedio_general"] == 0.0
        assert resultado["trabajos_aprobados"] == 0
        assert resultado["trabajos_reprobados"] == 0

    def test_reporte_estudiante_inexistente(self, gestor_con_clasificaciones, registro_est_completo):
        resultado = reporte_detallado_estudiante(
            gestor_con_clasificaciones, 
            registro_est_completo, 
            "INEXISTENTE"
        )
        
        assert "error" in resultado
        assert resultado["estudiante"] is None

    def test_reporte_estudiante_caso_insensible(self, gestor_con_clasificaciones, registro_est_completo):
        """Debe funcionar con códigos en minúsculas también"""
        resultado = reporte_detallado_estudiante(
            gestor_con_clasificaciones, 
            registro_est_completo, 
            "e001"
        )
        
        assert "estudiante" in resultado
        assert resultado["estudiante"]["codigo"].upper() == "E001"


# ─────────────────────────────────────────────
#  Tests: _clasificar_trabajo (nueva funcionalidad)
# ─────────────────────────────────────────────

class TestClasificarTrabajo:
    """Pruebas exhaustivas para la clasificación de trabajos"""

    @pytest.mark.parametrize("nota,esperado_categoria,esperado_estado", [
        (5.0, "Excelente", "Aprobado"),
        (4.8, "Sobresaliente", "Aprobado"),
        (4.5, "Sobresaliente", "Aprobado"),
        (4.0, "Aprobado", "Aprobado"),
        (3.5, "Aprobado", "Aprobado"),
        (3.0, "Aprobado", "Aprobado"),
        (2.9, "Reprobado", "Reprobado"),
        (2.0, "Reprobado", "Reprobado"),
        (1.5, "Reprobado", "Reprobado"),
        (1.4, "Reprobado Grave", "Reprobado"),
        (1.0, "Reprobado Grave", "Reprobado"),
        (0.0, "Reprobado Grave", "Reprobado"),
    ])
    def test_clasificacion_notas(self, nota, esperado_categoria, esperado_estado):
        categoria, estado = _clasificar_trabajo(nota)
        assert categoria == esperado_categoria
        assert estado == esperado_estado

    def test_clasificacion_valores_limite(self):
        """Probar bordes entre categorías"""
        # Límite entre aprobado y reprobado
        assert _clasificar_trabajo(3.0)[0] == "Aprobado"
        assert _clasificar_trabajo(2.999)[0] == "Reprobado"
        
        # Límite entre Sobresaliente y Aprobado
        assert _clasificar_trabajo(4.5)[0] == "Sobresaliente"
        assert _clasificar_trabajo(4.499)[0] == "Aprobado"
        
        # Límite entre Reprobado Grave y Reprobado
        assert _clasificar_trabajo(1.5)[0] == "Reprobado"
        assert _clasificar_trabajo(1.499)[0] == "Reprobado Grave"


# ─────────────────────────────────────────────
#  Tests: Pruebas de integración
# ─────────────────────────────────────────────

class TestIntegracionReportes:

    def test_flujo_completo_reportes(self, gestor_con_clasificaciones, registro_est_completo, registro_mat_basico):
        """Prueba que todas las funciones de reportes funcionen juntas"""
        
        # 1. Reporte general
        general = reporte_general(gestor_con_clasificaciones, registro_est_completo, registro_mat_basico)
        assert general["total_estudiantes"] == 3
        assert general["total_trabajos"] == 5
        
        # 2. Ranking
        ranking = ranking_estudiantes(gestor_con_clasificaciones, registro_est_completo)
        assert len(ranking) == 3
        assert ranking[0]["codigo"] == "E001"  # Ana tiene el mejor promedio
        
        # 3. Reporte detallado del mejor estudiante
        detalle = reporte_detallado_estudiante(
            gestor_con_clasificaciones, 
            registro_est_completo, 
            ranking[0]["codigo"]
        )
        assert detalle["promedio_general"] == ranking[0]["promedio"]
        
        # 4. CSV completo
        csv_content = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        assert len(csv_content) > 0
        assert "Excelente" in csv_content
        assert "Sobresaliente" in csv_content

    def test_consistencia_entre_reportes(self, gestor_con_datos, registro_est_basico, registro_mat_basico):
        """Verificar que diferentes funciones de reportes son consistentes"""
        
        # Obtener promedios de diferentes formas
        ranking_data = ranking_estudiantes(gestor_con_datos, registro_est_basico)
        general_data = reporte_general(gestor_con_datos, registro_est_basico, registro_mat_basico)
        
        # Calcular promedio manualmente desde ranking
        promedio_manual = sum(item["promedio"] for item in ranking_data) / len(ranking_data)
        
        # Debe coincidir con el promedio global
        assert abs(general_data["promedio_global"] - promedio_manual) < 0.01


# ─────────────────────────────────────────────
#  Tests: Compatibilidad hacia atrás
# ─────────────────────────────────────────────

class TestCompatibilidadLegacy:
    """Verifica que el código legacy (GENERAR_REPORTE_CSV) aún funcione"""
    
    def test_funcion_legacy_funciona(self, gestor_con_clasificaciones, registro_est_completo):
        """La función en mayúsculas debe seguir funcionando (deprecated)"""
        from src.reportes import GENERAR_REPORTE_CSV
        
        # Debe funcionar aunque esté deprecated
        resultado_legacy = GENERAR_REPORTE_CSV(gestor_con_clasificaciones, registro_est_completo)
        resultado_nuevo = generar_reporte_csv(gestor_con_clasificaciones, registro_est_completo)
        
        # Ambos deben dar el mismo resultado
        assert resultado_legacy == resultado_nuevo