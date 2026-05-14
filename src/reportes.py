"""
Pruebas unitarias para módulo de reportes (versión refactorizada)
"""

import pytest
from src.reportes import (
    reporte_general,
    ranking_estudiantes,
    generar_reporte_csv,
    reporte_detallado_estudiante,
    _clasificar_trabajo,
)


class TestClasificarTrabajo:
    """Pruebas para la función auxiliar de clasificación"""
    
    def test_excelente_nota_5(self):
        categoria, estado = _clasificar_trabajo(5.0)
        assert categoria == "Excelente"
        assert estado == "Aprobado"
    
    def test_sobresaliente_nota_4_7(self):
        categoria, estado = _clasificar_trabajo(4.7)
        assert categoria == "Sobresaliente"
        assert estado == "Aprobado"
    
    def test_aprobado_nota_3_5(self):
        categoria, estado = _clasificar_trabajo(3.5)
        assert categoria == "Aprobado"
        assert estado == "Aprobado"
    
    def test_reprobado_nota_2_0(self):
        categoria, estado = _clasificar_trabajo(2.0)
        assert categoria == "Reprobado"
        assert estado == "Reprobado"
    
    def test_reprobado_grave_nota_1_0(self):
        categoria, estado = _clasificar_trabajo(1.0)
        assert categoria == "Reprobado Grave"
        assert estado == "Reprobado"
    
    def test_limite_aprobacion_nota_3_0(self):
        categoria, estado = _clasificar_trabajo(3.0)
        assert categoria == "Aprobado"
        assert estado == "Aprobado"
    
    def test_limite_reprobado_nota_2_9(self):
        categoria, estado = _clasificar_trabajo(2.9)
        assert categoria == "Reprobado"
        assert estado == "Reprobado"


class TestReporteGeneral:
    """Pruebas para reporte general con manejo de casos borde"""
    
    def test_reporte_sin_estudiantes(self, gestor_vacio, registro_estudiantes_vacio, registro_materias_vacio):
        """No debe lanzar ZeroDivisionError cuando no hay estudiantes"""
        resultado = reporte_general(gestor_vacio, registro_estudiantes_vacio, registro_materias_vacio)
        
        assert resultado["total_estudiantes"] == 0
        assert resultado["promedio_global"] == 0.0
        assert resultado["total_materias"] == 0
        assert resultado["promedio_por_materia"] == 0.0
    
    def test_reporte_con_estudiantes(self, gestor_con_datos, registro_con_estudiantes, registro_con_materias):
        resultado = reporte_general(gestor_con_datos, registro_con_estudiantes, registro_con_materias)
        
        assert resultado["total_estudiantes"] > 0
        assert resultado["promedio_global"] >= 0
        assert "version_reporte" in resultado
        assert "formato_fecha" in resultado


class TestRankingEstudiantes:
    """Pruebas para ranking de estudiantes"""
    
    def test_ranking_orden_descendente(self, gestor_con_estudiantes, registro_con_estudiantes):
        ranking = ranking_estudiantes(gestor_con_estudiantes, registro_con_estudiantes)
        
        # Verificar orden descendente
        promedios = [e["promedio"] for e in ranking]
        assert promedios == sorted(promedios, reverse=True)
    
    def test_ranking_vacio(self, gestor_vacio, registro_estudiantes_vacio):
        ranking = ranking_estudiantes(gestor_vacio, registro_estudiantes_vacio)
        assert ranking == []


class TestGenerarReporteCSV:
    """Pruebas para generación de CSV"""
    
    def test_csv_tiene_encabezado(self, gestor_con_datos, registro_con_estudiantes):
        csv_content = generar_reporte_csv(gestor_con_datos, registro_con_estudiantes)
        
        assert "Estudiante" in csv_content
        assert "Materia" in csv_content
        assert "Nota" in csv_content
    
    def test_csv_no_esta_vacio(self, gestor_con_datos, registro_con_estudiantes):
        csv_content = generar_reporte_csv(gestor_con_datos, registro_con_estudiantes)
        assert len(csv_content.strip()) > 0


class TestReporteDetalladoEstudiante:
    """Pruebas para nueva funcionalidad"""
    
    def test_reporte_estudiante_existente(self, gestor_con_datos, registro_con_estudiantes):
        codigo = "20240001"  # Asumiendo que existe
        resultado = reporte_detallado_estudiante(gestor_con_datos, registro_con_estudiantes, codigo)
        
        assert "estudiante" in resultado
        assert "promedio_general" in resultado
        assert "total_trabajos" in resultado
    
    def test_reporte_estudiante_inexistente(self, gestor_con_datos, registro_con_estudiantes):
        resultado = reporte_detallado_estudiante(gestor_con_datos, registro_con_estudiantes, "INEXISTENTE")
        
        assert "error" in resultado
        assert resultado["estudiante"] is None