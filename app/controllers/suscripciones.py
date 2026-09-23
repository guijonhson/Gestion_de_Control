from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Plan, Suscripcion, Pago, Notificacion
from app.utils.suscripcion import verificar_limite, obtener_suscripcion_activa, obtener_limites_plan, contar_recursos
from datetime import datetime, timedelta
import os

bp = Blueprint('suscripciones', __name__, url_prefix='/suscripciones')

YAPPY_NUMERO = "6944-2874"

@bp.route('/')
@login_required
def index():
    suscripcion = obtener_suscripcion_activa(current_user.id_productor)
    limites = obtener_limites_plan(current_user.id_productor)
    recursos = contar_recursos(current_user.id_productor)
    
    return render_template('suscripciones/index.html',
                         suscripcion=suscripcion,
                         limites=limites,
                         recursos=recursos)

@bp.route('/upgrade')
@login_required
def upgrade():
    planes = Plan.query.filter_by(activo=True).all()
    return render_template('suscripciones/upgrade.html', planes=planes)

@bp.route('/pagar/<int:id_plan>', methods=['GET', 'POST'])
@login_required
def pagar(id_plan):
    plan = Plan.query.get_or_404(id_plan)
    suscripcion = obtener_suscripcion_activa(current_user.id_productor)
    
    if not suscripcion:
        suscripcion = Suscripcion(
            id_productor=current_user.id_productor,
            id_plan=plan.id,
            fecha_inicio=datetime.now().date(),
            estado='pendiente'
        )
        db.session.add(suscripcion)
        db.session.commit()
    
    if request.method == 'POST':
        referencia = request.form.get('referencia')
        
        pago = Pago(
            id_suscripcion=suscripcion.id,
            id_productor=current_user.id_productor,
            monto=plan.precio_mensual,
            metodo_pago='Yappy',
            referencia=referencia,
            estado='pendiente'
        )
        db.session.add(pago)
        db.session.commit()
        
        noti = Notificacion(
            mensaje=f"Usuario {current_user.correo} solicitó upgrade al plan {plan.nombre_plan} - Pago pendiente de revisión",
            tipo='pago',
            leido=False
        )
        db.session.add(noti)
        db.session.commit()
        
        flash('Pago registrado. Te contactaremos para verificar tu comprobante.', 'success')
        return redirect(url_for('suscripciones.index'))
    
    return render_template('suscripciones/pagar.html', plan=plan, yappy_numero=YAPPY_NUMERO)

@bp.route('/verificar_limite/<tipo>')
@login_required
def api_verificar_limite(tipo):
    puede, mensaje = verificar_limite(current_user, tipo)
    return {'puede': puede, 'mensaje': mensaje}

@bp.route('/mi_plan')
@login_required
def mi_plan():
    suscripcion = obtener_suscripcion_activa(current_user.id_productor)
    if not suscripcion:
        flash('No tienes suscripción activa', 'warning')
        return redirect(url_for('suscripciones.upgrade'))
    
    return render_template('suscripciones/mi_plan.html', suscripcion=suscripcion)

@bp.route('/pagos_pendientes')
@login_required
def pagos_pendientes():
    if current_user.rol != 'administrador':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    pagos = Pago.query.filter_by(estado='pendiente').order_by(Pago.fecha_pago.desc()).all()
    return render_template('suscripciones/pagos_pendientes.html', pagos=pagos)

@bp.route('/aprobar_pago/<int:id>', methods=['POST'])
@login_required
def aprobar_pago(id):
    if current_user.rol != 'administrador':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    pago = Pago.query.get_or_404(id)
    
    pago.estado = 'aprobado'
    
    suscripcion = pago.suscripcion
    suscripcion.estado = 'activa'
    suscripcion.fecha_inicio = datetime.now().date()
    suscripcion.fecha_fin = (datetime.now() + timedelta(days=30)).date()
    
    noti = Notificacion(
        id_productor=pago.id_productor,
        mensaje=f"Tu pago ha sido aprobado. Tu plan {suscripcion.plan.nombre_plan} está activo.",
        tipo='pago_aprobado',
        leido=False
    )
    db.session.add(noti)
    db.session.commit()
    
    flash('Pago aprobado y suscripción activada.', 'success')
    return redirect(url_for('suscripciones.pagos_pendientes'))

@bp.route('/rechazar_pago/<int:id>', methods=['POST'])
@login_required
def rechazar_pago(id):
    if current_user.rol != 'administrador':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    pago = Pago.query.get_or_404(id)
    pago.estado = 'rechazado'
    
    noti = Notificacion(
        id_productor=pago.id_productor,
        mensaje=f"Tu pago ha sido rechazado. Por favor contacta soporte.",
        tipo='pago_rechazado',
        leido=False
    )
    db.session.add(noti)
    db.session.commit()
    
    flash('Pago rechazado.', 'success')
    return redirect(url_for('suscripciones.pagos_pendientes'))
