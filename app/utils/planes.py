"""Nombres visibles de los planes.

Los valores guardados en la base de datos no se modifican: FREE, BÁSICO,
PRO y EMPRESARIAL. Aquí solo se define cómo se muestran al usuario.
"""
NOMBRES_PLAN_VISIBLES = {
    'FREE': 'Gratis',
    'BÁSICO': 'Básico',
    'BASICO': 'Básico',
    # Variante dañada por codificación en versiones anteriores.
    'B\ufffdSICO': 'Básico',
    'PRO': 'Profesional',
    'EMPRESARIAL': 'Empresarial',
}


def nombre_plan_visible(nombre):
    if not nombre:
        return ''
    return NOMBRES_PLAN_VISIBLES.get(nombre, nombre)
