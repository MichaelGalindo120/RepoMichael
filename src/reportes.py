"""
Módulo 5: Reportes del Sistema - Versión Corregida
Sistema de Notas Universitarias — Sprint 2
"""

import csv
import io
from typing import List, Dict, Any

from src.notas import GestorNotas
from src.estudiantes import RegistroEstudiantes
from src.materias import RegistroMaterias


# ============================================
# CONSTANTES
# ============================================

FORMATO_FECHA = "%d/%m/%Y"
VERSION_REPORTE = "1.0.0"


# ============================================
# FUNCIÓN AUXILIAR DE CLASIFICACIÓN
# ============================================

def _clasificar_trabajo(nota: float) -> tuple:
    """Clasifica un trabajo según su nota."""
    if nota >= 3.0:
        if nota >= 4.5:
            if nota == 5.0:
                return ("Excelente", "Aprobado")
            return ("Sobresaliente", "Aprobado")
        return ("Aprobado", "Aprobado")
    else:
        if nota < 1.5:
            return ("Reprobado Grave", "Reprobado")
        return ("Reprobado", "Reprobado")


# ============================================
# REPORTE GENERAL (sin división por cero)
# ============================================

def reporte_general(
    gestor: GestorNotas,
    registro_est: RegistroEstudiantes,
    registro_mat: RegistroMaterias,
) -> Dict[str, Any]:
    """Genera un reporte general del sistema."""
    estudiantes = registro_est.listar()
    materias = registro_mat.listar()
    
    total_estudiantes = len(estudiantes)
    total_materias = len(materias)
    
    # Manejo seguro de división por cero
    promedio_global = 0.0
    if total_estudiantes > 0:
        suma_promedios = sum(
            gestor.promedio_estudiante(e.codigo) for e in estudiantes
        )
        promedio_global = suma_promedios / total_estudiantes
    
    promedio_por_materia = 0.0
    if total_materias > 0:
        suma_materias = sum(
            gestor.promedio_materia(m.codigo) for m in materias
        )
        promedio_por_materia = suma_materias / total_materias
    
    return {
        "total_estudiantes": total_estudiantes,
        "total_materias": total_materias,
        "promedio_global": round(promedio_global, 2),
        "promedio_por_materia": round(promedio_por_materia, 2),
        "total_trabajos": gestor.total_trabajos(),
        "version_reporte": VERSION_REPORTE,
        "formato_fecha": FORMATO_FECHA,
    }


# ============================================
# RANKING DE ESTUDIANTES
# ============================================

def ranking_estudiantes(
    gestor: GestorNotas, 
    registro_est: RegistroEstudiantes
) -> List[Dict[str, Any]]:
    """Genera un ranking de estudiantes ordenado por promedio descendente."""
    estudiantes = registro_est.listar()
    
    ranking = []
    for estudiante in estudiantes:
        promedio = gestor.promedio_estudiante(estudiante.codigo)
        ranking.append({
            "codigo": estudiante.codigo,
            "nombre": estudiante.nombre,
            "promedio": promedio,
        })
    
    ranking.sort(key=lambda x: x["promedio"], reverse=True)
    return ranking


# ============================================
# REPORTE CSV (REFACTORIZADO)
# ============================================

def generar_reporte_csv(
    gestor: GestorNotas, 
    registro_est: RegistroEstudiantes
) -> str:
    """Genera un CSV con los trabajos de todos los estudiantes."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezado
    writer.writerow([
        "Estudiante", "Materia", "Trabajo", "Nota", 
        "Estado", "Categoria", "Version_Reporte"
    ])
    
    # Datos
    for estudiante in registro_est.listar():
        trabajos = gestor.trabajos_de_estudiante(estudiante.codigo)
        
        for trabajo in trabajos:
            categoria, estado = _clasificar_trabajo(trabajo.nota)
            
            writer.writerow([
                estudiante.nombre,
                trabajo.materia.nombre,
                trabajo.nombre_trabajo,
                trabajo.nota,
                estado,
                categoria,
                VERSION_REPORTE,
            ])
    
    return output.getvalue()


# ============================================
# FUNCIÓN LEGACY (para compatibilidad)
# ============================================

def GENERAR_REPORTE_CSV(gestor: GestorNotas, registro_est: RegistroEstudiantes) -> str:
    """[DEPRECATED] Usar generar_reporte_csv() en su lugar."""
    import warnings
    warnings.warn(
        "GENERAR_REPORTE_CSV está obsoleta, usar generar_reporte_csv()",
        DeprecationWarning,
        stacklevel=2
    )
    return generar_reporte_csv(gestor, registro_est)


# ============================================
# NOTA: La función calcular_promedio_estudiante
# ha sido eliminada para evitar duplicación.
# Usar gestor.promedio_estudiante() directamente.
# ============================================