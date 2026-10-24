from flask import Blueprint, render_template, url_for
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Aplicador, Finca, Parcela, RegistroAgricola, Gasto, Produccion, Inventario, Usuario, Productor, Pago, Notificacion
from app.utils.suscripcion import obtener_limites_plan, contar_recursos
from datetime import datetime, timedelta

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    id_productor = current_user.id_productor
    
    fincas = Finca.query.filter_by(id_productor=id_productor).all()
    fincas_ids = [f.id for f in fincas]
    
    num_fincas = len(fincas_ids)
    num_parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).count() if fincas_ids else 0
    
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    parcelas_ids = [p.id for p in parcelas]
    num_registros = RegistroAgricola.query.filter(RegistroAgricola.id_parcela.in_(parcelas_ids)).count() if parcelas_ids else 0
    
    gastos = Gasto.query.filter(Gasto.id_finca.in_(fincas_ids)).all()
    total_gastos = sum(float(g.monto or 0) for g in gastos) if fincas_ids else 0
    
    producciones = Produccion.query.filter(Produccion.id_parcela.in_(parcelas_ids)).all()
    total_produccion = sum(p.ingreso_total for p in producciones) if parcelas_ids else 0
    
    num_productos_inventario = Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).count() if fincas_ids else 0
    num_aplicadores = Aplicador.query.filter_by(id_productor=id_productor).count()

    primeros_pasos = [
        {
            'titulo': 'Crear tu primera finca',
            'hecho': num_fincas > 0,
            'url': url_for('fincas.crear'),
            'boton': 'Crear finca',
        },
        {
            'titulo': 'Crear una parcela',
            'hecho': num_parcelas > 0,
            'url': url_for('parcelas.crear'),
            'boton': 'Crear parcela',
        },
        {
            'titulo': 'Registrar un aplicador',
            'hecho': num_aplicadores > 0,
            'url': url_for('aplicadores.crear'),
            'boton': 'Registrar aplicador',
        },
        {
            'titulo': 'Guardar tu primer registro agrícola',
            'hecho': num_registros > 0,
            'url': url_for('registros.crear'),
            'boton': 'Crear registro',
        },
    ]
    pasos_completos = all(paso['hecho'] for paso in primeros_pasos)

    limites = obtener_limites_plan(id_productor)
    recursos = contar_recursos(id_productor)
    
    metricas_admin = None
    if current_user.rol == 'administrador':
        hoy = datetime.now().date()
        semana = datetime.now() - timedelta(days=7)
        
        usuarios_totales = Usuario.query.count()
        usuarios_hoy = Usuario.query.filter(
            db.func.date(Usuario.ultimo_acceso) == hoy
        ).count() if hasattr(Usuario, 'ultimo_acceso') else 0
        usuarios_semana = Usuario.query.filter(
            Usuario.ultimo_acceso >= semana
        ).count() if hasattr(Usuario, 'ultimo_acceso') else 0
        
        pagos_pendientes = Pago.query.filter_by(estado='pendiente').count()
        notificaciones_nuevas = Notificacion.query.filter_by(leido=False).count()
        
        metricas_admin = {
            'usuarios_totales': usuarios_totales,
            'usuarios_hoy': usuarios_hoy,
            'usuarios_semana': usuarios_semana,
            'pagos_pendientes': pagos_pendientes,
            'notificaciones_nuevas': notificaciones_nuevas
        }
    
    return render_template('dashboard/index.html',
        num_fincas=num_fincas,
        num_parcelas=num_parcelas,
        num_registros=num_registros,
        total_gastos=total_gastos,
        total_produccion=total_produccion,
        num_productos_inventario=num_productos_inventario,
        limites=limites,
        recursos=recursos,
        primeros_pasos=primeros_pasos,
        pasos_completos=pasos_completos,
        metricas_admin=metricas_admin)
