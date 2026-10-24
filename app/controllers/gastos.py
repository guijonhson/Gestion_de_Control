from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Cultivo, Finca, Gasto
from app.utils.permisos import obtener_finca, obtener_gasto
from app.utils.suscripcion import verificar_limite
from app.utils.validaciones import (
    ErrorValidacion,
    a_decimal,
    a_entero,
    a_fecha,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('gastos', __name__, url_prefix='/gastos')

CATEGORIAS = [
    'semilla',
    'fertilizante',
    'mano_obra',
    'combustible',
    'mantenimiento',
    'otro',
]
CATEGORIAS_LABELS = {
    'semilla': 'Semilla',
    'fertilizante': 'Fertilizante',
    'mano_obra': 'Mano de Obra',
    'combustible': 'Combustible',
    'mantenimiento': 'Mantenimiento',
    'otro': 'Otro',
}


def _leer_datos():
    tipo_gasto = limpiar_texto(request.form.get('tipo_gasto'))
    if tipo_gasto not in CATEGORIAS:
        raise ErrorValidacion('El tipo de gasto no es válido.')
    id_finca = a_entero(request.form.get('id_finca'), 'La finca', minimo=1)
    finca = obtener_finca(id_finca)
    id_cultivo = a_entero(
        request.form.get('id_cultivo'), 'El cultivo', minimo=1, obligatorio=False
    )
    if id_cultivo and not Cultivo.query.get(id_cultivo):
        raise ErrorValidacion('El cultivo seleccionado no existe.')

    monto = a_decimal(
        request.form.get('monto'), 'El monto', minimo=0, obligatorio=True
    )
    fecha = a_fecha(request.form.get('fecha'), 'La fecha', obligatoria=True)
    descripcion = validar_largo(
        request.form.get('descripcion'), 500, 'La descripción'
    )
    responsable = validar_largo(
        request.form.get('responsable'), 100, 'El responsable'
    )
    return {
        'tipo_gasto': tipo_gasto,
        'descripcion': descripcion,
        'monto': monto,
        'fecha': fecha,
        'responsable': responsable,
        'id_finca': finca.id,
        'id_cultivo': id_cultivo,
    }


@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    gastos = (
        Gasto.query
        .filter(Gasto.id_finca.in_(fincas_ids))
        .order_by(Gasto.fecha.desc())
        .all()
    )
    return render_template(
        'gastos/listar.html', gastos=gastos, categorias=CATEGORIAS_LABELS
    )


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    puede, mensaje = verificar_limite(current_user, 'gasto')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))

    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    cultivos = Cultivo.query.order_by(Cultivo.nombre_cultivo).all()

    if request.method == 'POST':
        try:
            db.session.add(Gasto(**_leer_datos()))
            db.session.commit()
            flash('Gasto registrado exitosamente.', 'success')
            return redirect(url_for('gastos.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'gastos/crear.html',
        fincas=fincas,
        cultivos=cultivos,
        categorias=CATEGORIAS_LABELS,
    )


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    gasto = obtener_gasto(id)
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    cultivos = Cultivo.query.order_by(Cultivo.nombre_cultivo).all()

    if request.method == 'POST':
        try:
            for campo, valor in _leer_datos().items():
                setattr(gasto, campo, valor)
            db.session.commit()
            flash('Gasto actualizado exitosamente.', 'success')
            return redirect(url_for('gastos.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'gastos/editar.html',
        gasto=gasto,
        fincas=fincas,
        cultivos=cultivos,
        categorias=CATEGORIAS_LABELS,
    )


@bp.route('/buscar', methods=['POST'])
@login_required
def buscar():
    tipo_gasto = request.form.get('tipo_gasto')
    id_finca = request.form.get('id_finca')

    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    query = Gasto.query.filter(Gasto.id_finca.in_(fincas_ids))

    if tipo_gasto:
        query = query.filter(Gasto.tipo_gasto == tipo_gasto)
    if id_finca:
        try:
            id_finca_int = int(id_finca)
        except (TypeError, ValueError):
            flash('La finca seleccionada no es válida.', 'danger')
            return redirect(url_for('gastos.listar'))
        if id_finca_int not in fincas_ids:
            flash('La finca seleccionada no es válida.', 'danger')
            return redirect(url_for('gastos.listar'))
        query = query.filter(Gasto.id_finca == id_finca_int)

    gastos = query.order_by(Gasto.fecha.desc()).all()
    return render_template(
        'gastos/listar.html', gastos=gastos, categorias=CATEGORIAS_LABELS
    )
