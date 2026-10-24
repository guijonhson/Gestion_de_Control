from sqlalchemy import inspect, text
from sqlalchemy.types import String

from app.config.database import db

# (tabla, columna, tipo SQL)
COLUMNAS_NUEVAS = [
    ('parcela', 'tipo_uso', "VARCHAR(20) DEFAULT 'agricola' NOT NULL"),
    ('finca', 'rubro', 'VARCHAR(200)'),
    ('parcela', 'fecha_inicio_siembra', 'DATE'),
    ('parcela', 'duracion_cultivo', 'INTEGER'),
    ('usuario', 'fecha_aceptacion_terminos', 'TIMESTAMP'),
]

# Reglas del plan EMPRESARIAL (None = ilimitado)
PLAN_EMPRESARIAL = {
    'limite_usuarios': 10,
    'limite_fincas': None,
    'limite_parcelas': None,
    'limite_productos': None,
}

# Texto de herramientas que se pegó por error en campos de texto
TEXTO_BASURA = '%successfully downloaded text file%'
MARCADOR_REVISAR = 'PENDIENTE'

# (etiqueta, import_path, modelo, campo, es_obligatorio)
CAMPOS_A_REVISAR = [
    ('usuario.nombre_usuario', 'app.models.usuario', 'Usuario', 'nombre_usuario', True),
    ('productor.nombre', 'app.models.productor', 'Productor', 'nombre', True),
    ('finca.nombre_finca', 'app.models.finca', 'Finca', 'nombre_finca', True),
    ('parcela.numero_parcela', 'app.models.parcela', 'Parcela', 'numero_parcela', True),
    ('finca.rubro', 'app.models.finca', 'Finca', 'rubro', False),
    ('parcela.cultivo_actual', 'app.models.parcela', 'Parcela', 'cultivo_actual', False),
    ('parcela_ganadera.pasto', 'app.models.parcela_ganadera', 'ParcelaGanadera', 'pasto', False),
    ('parcela_ganadera.raza', 'app.models.parcela_ganadera', 'ParcelaGanadera', 'raza', False),
    ('registro_agricola.dosis', 'app.models.registro_agricola', 'RegistroAgricola', 'dosis', False),
    ('registro_agricola.observaciones', 'app.models.registro_agricola', 'RegistroAgricola', 'observaciones', False),
]


def _es_postgres():
    return db.engine.dialect.name == 'postgresql'


def _revisar(etiqueta, funcion):
    """Ejecuta una verificacion aislada: un fallo no oculta las demas."""
    try:
        return funcion()
    except Exception as e:
        print(f"[migraciones] No se pudo revisar {etiqueta}: {e}")
        db.session.rollback()
        return None


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


def _modelo(import_path, nombre):
    import importlib
    modulo = importlib.import_module(import_path)
    return getattr(modulo, nombre)


def _tablas_public():
    """Todas las tablas del esquema public (solo PostgreSQL)."""
    if not _es_postgres():
        return []
    filas = db.session.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
    )).fetchall()
    return [f[0] for f in filas]


def _tablas_sin_rls():
    """Tablas del esquema public sin RLS habilitado (solo PostgreSQL)."""
    if not _es_postgres():
        return []
    filas = db.session.execute(text(
        "SELECT c.relname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity = false"
    )).fetchall()
    return [f[0] for f in filas]


def habilitar_rls():
    """
    Habilita Row Level Security en todas las tablas del esquema public.

    Cierra el acceso por la API publica de Supabase (anon key). NO afecta a la
    aplicacion: Flask se conecta como usuario postgres (dueno de las tablas),
    que ignora RLS. Devuelve la lista de tablas procesadas.
    """
    tablas = _tablas_public()
    for tabla in tablas:
        db.session.execute(text('ALTER TABLE public."' + tabla + '" ENABLE ROW LEVEL SECURITY'))
    if tablas:
        db.session.commit()
    return tablas


def limpiar_texto_pegado():
    """
    Borra el texto de herramientas que se pegó por error en campos de texto.
    Devuelve un dict {campo: filas corregidas}. Los campos obligatorios quedan
    con el marcador PENDIENTE; los opcionales se vacían.
    """
    corregidos = {}
    for etiqueta, import_path, nombre, campo, obligatorio in CAMPOS_A_REVISAR:
        try:
            modelo = _modelo(import_path, nombre)
            columna = getattr(modelo, campo)
            consulta = modelo.query.filter(columna.ilike(TEXTO_BASURA))
            cantidad = consulta.count()
            if cantidad:
                valor = MARCADOR_REVISAR if obligatorio else None
                consulta.update({columna: valor}, synchronize_session=False)
                corregidos[etiqueta] = cantidad
        except Exception as e:
            print(f"[migraciones] No se pudo revisar {etiqueta}: {e}")
            db.session.rollback()
    if corregidos:
        db.session.commit()
    return corregidos


def _basura_pendiente():
    total = 0
    for etiqueta, import_path, nombre, campo, _ob in CAMPOS_A_REVISAR:
        try:
            modelo = _modelo(import_path, nombre)
            columna = getattr(modelo, campo)
            total += modelo.query.filter(columna.ilike(TEXTO_BASURA)).count()
        except Exception as e:
            print(f"[migraciones] No se pudo revisar {etiqueta}: {e}")
            db.session.rollback()
    return total


def obtener_pendientes():
    """
    Lista lo que falta por aplicar. Cada verificacion es independiente:
    si una falla, las demas siguen reportando (y el boton sigue apareciendo).
    """
    pendientes = []

    # Columnas nuevas
    def _columnas_faltantes():
        inspector = inspect(db.engine)
        return [
            f'Columna {tabla}.{columna}'
            for tabla, columna, _tipo in COLUMNAS_NUEVAS
            if columna not in _columnas(inspector, tabla)
        ]
    faltantes = _revisar('columnas', _columnas_faltantes)
    if faltantes:
        pendientes.extend(faltantes)

    # Tipo de dosis
    if _revisar('dosis', lambda: _dosis_pendiente(inspect(db.engine))):
        pendientes.append('Tipo de dato de registro_agricola.dosis')

    # Plan EMPRESARIAL
    if _revisar('plan EMPRESARIAL', lambda: _plan_pendiente()):
        pendientes.append('Límites del plan EMPRESARIAL')

    # Catálogo de cultivos
    faltan = _revisar('catálogo', lambda: _catalogo_pendiente())
    if faltan:
        pendientes.append('Catálogo de cultivos de Panamá')

    # Texto pegado por error
    basura = _revisar('texto pegado', _basura_pendiente)
    if basura:
        pendientes.append(f'Texto pegado por error en {basura} campo(s)')

    # Seguridad RLS
    sin_rls = _revisar('RLS', lambda: _tablas_sin_rls())
    if sin_rls:
        pendientes.append(f'Seguridad: RLS deshabilitado en {len(sin_rls)} tabla(s)')

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

    # Seguridad: habilitar RLS en las tablas del esquema public
    habilitar_rls()


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
    return limpiar_texto_pegado()
