from app.config.database import db
from app.models import (
    Finca, Parcela, Inventario, Gasto, RegistroAgricola,
    Suscripcion, Plan, Usuario
)
from datetime import datetime, timedelta


# ============================================================
# RESOLUCIÓN DE USUARIO
# ============================================================

def _resolver_usuario(usuario_o_id):
    """Acepta un Usuario o un id_usuario y devuelve el Usuario."""
    if usuario_o_id is None:
        return None
    if hasattr(usuario_o_id, 'rol'):
        return usuario_o_id
    try:
        return db.session.get(Usuario, int(usuario_o_id))
    except (ValueError, TypeError):
        return None


def es_admin(usuario_o_id):
    """
    Verifica si el USUARIO (no el productor) es administrador.
    
    CORREGIDO: antes recibía id_productor y devolvía True si CUALQUIER
    usuario de ese productor era admin. Ahora verifica el usuario específico.
    """
    usuario = _resolver_usuario(usuario_o_id)
    if not usuario:
        return False
    return usuario.rol == 'administrador'


# ============================================================
# SUSCRIPCIONES
# ============================================================

def obtener_suscripcion_activa(id_productor):
    """Obtiene la suscripción activa del productor (solo lectura)."""
    return Suscripcion.query.filter_by(
        id_productor=id_productor,
        estado='activa'
    ).first()


def marcar_suscripciones_vencidas(id_productor):
    """
    Marca como 'vencida' cualquier suscripción activa cuya fecha_fin ya pasó.
    Se llama explícitamente (no como side effect de otra función).
    """
    hoy = datetime.now().date()
    actualizadas = Suscripcion.query.filter(
        Suscripcion.id_productor == id_productor,
        Suscripcion.estado == 'activa',
        Suscripcion.fecha_fin < hoy
    ).update({'estado': 'vencida'}, synchronize_session=False)
    
    if actualizadas:
        db.session.commit()
    return actualizadas


def esta_suscripcion_activa(id_productor):
    """Verifica si la suscripción está activa y no ha vencido."""
    marcar_suscripciones_vencidas(id_productor)
    return obtener_suscripcion_activa(id_productor) is not None


# ============================================================
# PLANES
# ============================================================

def obtener_plan(id_plan):
    """Obtiene un plan por su ID (API moderna)."""
    return db.session.get(Plan, id_plan)


def obtener_limites_plan(id_productor):
    """Retorna los límites del plan actual del productor."""
    suscripcion = obtener_suscripcion_activa(id_productor)
    if not suscripcion or not suscripcion.plan:
        return None
    
    plan = suscripcion.plan
    return {
        'limite_fincas': plan.limite_fincas,
        'limite_usuarios': plan.limite_usuarios,
        'limite_parcelas': plan.limite_parcelas,
        'limite_productos': plan.limite_productos,
        'limite_inventario': plan.limite_inventario,
        'limite_registros': plan.limite_registros,
        'limite_gastos': plan.limite_gastos,
        'reportes_avanzados': plan.reportes_avanzados,
        'exportar_datos': plan.exportar_datos,
        'nombre_plan': plan.nombre_plan,
        'precio': plan.precio_mensual,
    }


# ============================================================
# CONTEO DE RECURSOS
# ============================================================

def contar_recursos(id_productor):
    """Cuenta los recursos actuales del productor."""
    fincas = Finca.query.filter_by(id_productor=id_productor).all()
    fincas_ids = [f.id for f in fincas]
    
    parcelas = (
        Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
        if fincas_ids else []
    )
    parcelas_ids = [p.id for p in parcelas]
    
    return {
        'fincas': len(fincas),
        'parcelas': len(parcelas),
        'inventario': (
            Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).count()
            if fincas_ids else 0
        ),
        'gastos': (
            Gasto.query.filter(Gasto.id_finca.in_(fincas_ids)).count()
            if fincas_ids else 0
        ),
        'registros': (
            RegistroAgricola.query.filter(
                RegistroAgricola.id_parcela.in_(parcelas_ids)
            ).count()
            if parcelas_ids else 0
        ),
        'usuarios': Usuario.query.filter_by(id_productor=id_productor).count(),
    }


# ============================================================
# VERIFICACIÓN DE LÍMITES
# ============================================================

def verificar_limite(usuario_o_id, tipo_recurso):
    """
    Verifica si el usuario puede crear más recursos según su plan.
    Retorna (puede_crear: bool, mensaje: str|None).
    
    IMPORTANTE: Solo el USUARIO admin tiene acceso ilimitado,
    no todos los usuarios del productor.
    """
    usuario = _resolver_usuario(usuario_o_id)
    if not usuario:
        return False, "Usuario no encontrado."
    
    # Solo el admin específico tiene ilimitado
    if usuario.rol == 'administrador':
        return True, None
    
    id_productor = usuario.id_productor
    
    # Verificar suscripción activa
    marcar_suscripciones_vencidas(id_productor)
    suscripcion = obtener_suscripcion_activa(id_productor)
    
    if not suscripcion:
        return False, "Tu suscripción no está activa. Renueva tu plan para continuar."
    
    plan = suscripcion.plan
    if not plan:
        return False, "Error: Plan no encontrado. Contacta al administrador."
    
    # Mapeo de tipo de recurso a atributo del plan
    limite_attr_map = {
        'finca': 'limite_fincas',
        'parcela': 'limite_parcelas',
        'inventario': 'limite_inventario',
        'usuario': 'limite_usuarios',
        'gasto': 'limite_gastos',
        'registro': 'limite_registros',
    }
    
    if tipo_recurso not in limite_attr_map:
        return True, None
    
    limite = getattr(plan, limite_attr_map[tipo_recurso], None)
    
    # None = ilimitado
    if limite is None:
        return True, None
    
    # Contar recursos actuales
    recursos = contar_recursos(id_productor)
    conteo_map = {
        'finca': recursos['fincas'],
        'parcela': recursos['parcelas'],
        'inventario': recursos['inventario'],
        'usuario': recursos['usuarios'],
        'gasto': recursos['gastos'],
        'registro': recursos['registros'],
    }
    count = conteo_map.get(tipo_recurso, 0)
    
    if count >= limite:
        plural = {
            'finca': 'fincas', 'parcela': 'parcelas', 'inventario': 'productos en inventario',
            'usuario': 'usuarios', 'gasto': 'gastos', 'registro': 'registros'
        }.get(tipo_recurso, 'recursos')
        
        return False, (
            f"Tu plan {plan.nombre_plan} permite solo {limite} {plural}. "
            f"Actualiza tu plan para seguir creciendo."
        )
    
    return True, None


# ============================================================
# FUNCIONALIDADES DEL PLAN
# ============================================================

def puede_usar_funcionalidad(usuario_o_id, funcionalidad):
    """Verifica si el usuario puede usar una funcionalidad según su plan."""
    usuario = _resolver_usuario(usuario_o_id)
    if not usuario:
        return False
    
    if usuario.rol == 'administrador':
        return True
    
    suscripcion = obtener_suscripcion_activa(usuario.id_productor)
    if not suscripcion or not suscripcion.plan:
        return False
    
    func_map = {
        'reportes_avanzados': 'reportes_avanzados',
        'exportar_datos': 'exportar_datos',
    }
    
    if funcionalidad in func_map:
        return bool(getattr(suscripcion.plan, func_map[funcionalidad], False))
    
    return True


# ============================================================
# ASIGNACIÓN DE PLANES
# ============================================================

def asignar_plan(id_productor, nombre_plan):
    """Asigna un plan al productor (marca el anterior como cancelado)."""
    plan = Plan.query.filter_by(nombre_plan=nombre_plan).first()
    if not plan:
        return None, f"Plan {nombre_plan} no encontrado"
    
    # Marcar suscripciones anteriores como canceladas (preserva historial)
    Suscripcion.query.filter_by(
        id_productor=id_productor, estado='activa'
    ).update({'estado': 'cancelada'}, synchronize_session=False)
    
    suscripcion = Suscripcion(
        id_productor=id_productor,
        id_plan=plan.id,
        fecha_inicio=datetime.now().date(),
        fecha_fin=datetime.now().date() + timedelta(days=30),
        estado='activa'
    )
    db.session.add(suscripcion)
    db.session.commit()
    return suscripcion, None