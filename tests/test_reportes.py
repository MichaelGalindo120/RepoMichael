"""
Pruebas unitarias — Módulo reportes (Versión Corregida)
Sistema de Notas Universitarias — Sprint 2
"""

import pytest
from src.estudiantes import Estudiante, RegistroEstudiantes
from src.materias import Materia, RegistroMaterias
from src.notas import Trabajo, GestorNotas

# Importar SOLO las funciones que existen en src/reportes.py
from src.reportes import (
    reporte_general,
    ranking_estudiantes,
    generar_reporte_csv,
    FORMATO_FECHA,
    VERSION_REPORTE,
)


# ─────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def est1():
    return Estudiante("E001", "Ana García", "ana@test.com")


@pytest.fixture
def est2():
    return Estudiante("E002", "Carlos Mejía", "carlos@test.com")


@pytest.fixture
def mat1():
    return Materia("CS101", "Calidad del Software", 3)


@pytest.fixture
def mat2():
    return Materia("IS201", "Ingeniería de Requerimientos", 3)


@pytest.fixture
def gestor_con_datos(est1, est2, mat1, mat2):
    g = GestorNotas()
    g.asignar(Trabajo(est1, mat1, "Parcial 1", 4.0))
    g.asignar(Trabajo(est1, mat2, "Quiz 1", 3.5))
    g.asignar(Trabajo(est2, mat1, "Parcial 1", 2.8))
    return g


@pytest.fixture
def registro_est_basico(est1, est2):
    r = RegistroEstudiantes()
    r.registrar(est1)
    r.registrar(est2)
    return r


@pytest.fixture
def registro_mat_basico(mat1, mat2):
    r = RegistroMaterias()
    r.registrar(mat1)
    r.registrar(mat2)
    return r


# ─────────────────────────────────────────────
#  Tests: reporte_general
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

    def test_sin_estudiantes_no_lanza_error(self, mat1):
        gestor = GestorNotas()
        reg_est_vacio = RegistroEstudiantes()
        reg_mat = RegistroMaterias()
        reg_mat.registrar(mat1)
        
        reporte = reporte_general(gestor, reg_est_vacio, reg_mat)
        
        assert reporte["total_estudiantes"] == 0
        assert reporte["promedio_global"] == 0.0
        assert reporte["total_trabajos"] == 0

    def test_sin_materias_no_lanza_error(self, est1):
        gestor = GestorNotas()
        reg_est = RegistroEstudiantes()
        reg_est.registrar(est1)
        reg_mat_vacio = RegistroMaterias()
        
        reporte = reporte_general(gestor, reg_est, reg_mat_vacio)
        
        assert reporte["total_estudiantes"] == 1
        assert reporte["total_materias"] == 0
        assert reporte["promedio_por_materia"] == 0.0


# ─────────────────────────────────────────────
#  Tests: ranking_estudiantes
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


# ─────────────────────────────────────────────
#  Tests: generar_reporte_csv
# ─────────────────────────────────────────────

class TestGenerarReporteCSV:

    def test_csv_incluye_encabezado(self, gestor_con_datos, registro_est_basico):
        salida = generar_reporte_csv(gestor_con_datos, registro_est_basico)
        primera_linea = salida.strip().split("\n")[0]
        
        assert "Estudiante" in primera_linea
        assert "Materia" in primera_linea
        assert "Nota" in primera_linea

    def test_csv_sin_estudiantes_solo_tiene_encabezado(self):
        salida = generar_reporte_csv(GestorNotas(), RegistroEstudiantes())
        lineas = [l for l in salida.strip().split("\n") if l]
        assert len(lineas) == 1

    def test_csv_retorna_string(self, gestor_con_datos, registro_est_basico):
        salida = generar_reporte_csv(gestor_con_datos, registro_est_basico)
        assert isinstance(salida, str)


# ─────────────────────────────────────────────
#  Tests: constantes
# ─────────────────────────────────────────────

class TestConstantes:

    def test_formato_fecha_esta_definido(self):
        assert FORMATO_FECHA is not None

    def test_version_reporte_esta_definida(self):
        assert VERSION_REPORTE is not None