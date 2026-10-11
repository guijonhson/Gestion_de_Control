from sqlalchemy import inspect, text
from sqlalchemy.types import String

from app.config.database import db

# (tabla, columna, tipo SQL)
COLUMNAS_NUEVAS = [
    ('parcela', 'tipo_uso', "VARCHAR(20) DEFAULT 'agricola' NOT NULL"),
    ('finca', 'rubro', 'VARCHAR(200)'),
    ('parcela', 'fecha_inicio_siembra', 'DATE'),
    ('parcela', 'duracion_cultivo', 'INTEGER'),
]

# Reglas del plan EMPRESARIAL (None = ilimitado)
PLAN_EMPRESARIAL = {
    'limite_usuarios': 10,
    'limite_fincas': None,
    'limite_parcelas': None,
    'limite_productos': None,
}


def _es_postgres():
    return db.engine.dialect.name == 'postgresql'


def _columnas(inspector, tabla):
    return {c['name'] for c in inspector.get_columns(tabla)}


def _dosis_pendiente(inspector):
    if not _es_postgres():
        return False
    for col in inspector.get_columns('registro_agricola'):
        if col['name'] == 'dosis':
            return not isinstance(col['type'], String)
    return False


def _plan_pendiente():
    from app.models import Plan
    plan = Plan.query.filter_by(nombre_plan='EMPRESARIAL').first()
    if not plan:
        return False
    return any(getattr(plan, campo) != valor for campo, valor in PLAN_EMPRESARIAL.items())


def _catalogo_pendiente():
    from app.models import Cultivo
    from app.utils.catalogos_agro import CULTIVOS_PANAMA
    existentes = {c.nombre_cultivo for c in Cultivo.query.all()}
    return [n for n, _ in CULTIVOS_PANAMA if n not in existentes]


def obtener_pendientes():
    pendientes = []
    inspector = inspect(db.engine)

    for tabla, columna, _tipo in COLUMNAS_NUEVAS:
        existentes = _columnas(inspector, tabla)
        if columna not in existentes:
            pendientes.append(f'Columna {tabla}.{columna}')

    if _dosis_pendiente(inspector):
        pendientes.append('Tipo de dato de registro_agricola.dosis')

    if _plan_pendiente():
        pendientes.append('Límites del plan EMPRESARIAL')

    if _catalogo_pendiente():
        pendientes.append('Catálogo de cultivos de Panamá')

    return pendientes


def aplicar_cambios_estructurales():
    inspector = inspect(db.engine)

    for tabla, columna, tipo in COLUMNAS_NUEVAS:
        existentes = _columnas(inspector, tabla)
        if columna in existentes:
            continue
        sentencia = f'ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}'
        if _es_postgres():
            sentencia = f'ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {columna} {tipo}'
        db.session.execute(text(sentencia))
        db.session.commit()

    if _dosis_pendiente(inspect(db.engine)):
        db.session.execute(text(
            'ALTER TABLE registro_agricola '
            'ALTER COLUMN dosis TYPE VARCHAR(50) USING dosis::text'
        ))
        db.session.commit()

    # Catálogo de cultivos de Panamá (solo añade, nunca borra)
    faltantes = _catalogo_pendiente()
    if faltantes:
        from app.models import Cultivo
        from app.utils.catalogos_agro import CULTIVOS_PANAMA
        ciclos = dict(CULTIVOS_PANAMA)
        for nombre in faltantes:
            db.session.add(Cultivo(nombre_cultivo=nombre, ciclo_dias_aprox=ciclos.get(nombre)))
        db.session.commit()


def aplicar_plan_empresarial():
    from app.models import Plan
    plan = Plan.query.filter_by(nombre_plan='EMPRESARIAL').first()
    if not plan:
        return False
    for campo, valor in PLAN_EMPRESARIAL.items():
        setattr(plan, campo, valor)
    db.session.commit()
    return True


def aplicar_todo():
    aplicar_cambios_estructurales()
    aplicar_plan_empresarial()
