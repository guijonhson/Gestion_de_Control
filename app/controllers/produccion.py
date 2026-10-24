from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Cultivo, Finca, Parcela, Produccion
from app.utils.permisos import obtener_parcela, obtener_produccion
from app.utils.validaciones import (
    ErrorValidacion,
    a_decimal,
    a_entero,
    a_fecha,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('produccion', __name__, url_prefix='/produccion')

UNIDADES = ('kg', 'ton', 'qq', 'unidades', 'lbs')


def _leer_datos():
    id_cultivo = a_entero(request.form.get('id_cultivo'), 'El cultivo', minimo=1)
    if not Cultivo.query.get(id_cultivo):
        raise ErrorValidacion('El cultivo seleccionado no existe.')

    id_parcela = a_entero(request.form.get('id_parcela'), 'La parcela', minimo=1)
    parcela = obtener_parcela(id_parcela)

    fecha = a_fecha(
        request.form.get('fecha_cosecha'), 'La fecha de cosecha', obligatoria=True
    )
    cantidad = a_decimal(
        request.form.get('cantidad'), 'La cantidad', minimo=0, obligatorio=True
    )
    if cantidad is not None and cantidad <= 0:
        raise ErrorValidacion('La cantidad debe ser mayor que 0.')
    unidad = limpiar_texto(request.form.get('unidad_medida')) or 'kg'
    if unidad not in UNIDADES:
        raise ErrorValidacion('La unidad de medida no es válida.')
    precio = a_decimal(
        request.form.get('precio_venta'), 'El precio de venta', minimo=0
    ) or 0
    observaciones = validar_largo(
        request.form.get('observaciones'), 500, 'Las observaciones'
    )
    return {
        'id_cultivo': id_cultivo,
        'id_parcela': parcela.id,
        'fecha_cosecha': fecha,
        'cantidad': cantidad,
        'unidad_medida': unidad,
        'precio_venta': precio,
        'observaciones': observaciones,
    }


@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    parcelas_ids = [p.id for p in parcelas]
    producciones = (
        Produccion.query
        .filter(Produccion.id_parcela.in_(parcelas_ids))
        .order_by(Produccion.fecha_cosecha.desc())
        .all()
    )
    return render_template('produccion/listar.html', producciones=producciones)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    cultivos = Cultivo.query.order_by(Cultivo.nombre_cultivo).all()

    if request.method == 'POST':
        try:
            db.session.add(Produccion(**_leer_datos()))
            db.session.commit()
            flash('Producción registrada exitosamente.', 'success')
            return redirect(url_for('produccion.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'produccion/crear.html', parcelas=parcelas, cultivos=cultivos
    )


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    produccion = obtener_produccion(id)
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    cultivos = Cultivo.query.order_by(Cultivo.nombre_cultivo).all()

    if request.method == 'POST':
        try:
            for campo, valor in _leer_datos().items():
                setattr(produccion, campo, valor)
            db.session.commit()
            flash('Producción actualizada exitosamente.', 'success')
            return redirect(url_for('produccion.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'produccion/editar.html',
        produccion=produccion,
        parcelas=parcelas,
        cultivos=cultivos,
    )


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    produccion = obtener_produccion(id)
    db.session.delete(produccion)
    db.session.commit()
    flash('Registro de producción eliminado.', 'success')
    return redirect(url_for('produccion.listar'))


@bp.route('/resumen')
@login_required
def resumen():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    parcelas_ids = [p.id for p in parcelas]
    producciones = Produccion.query.filter(
        Produccion.id_parcela.in_(parcelas_ids)
    ).all()

    total_cosechas = len(producciones)
    total_cantidad = sum(float(p.cantidad or 0) for p in producciones)
    total_ingreso = sum(p.ingreso_total for p in producciones)

    resumen_cultivos = {}
    for p in producciones:
        cultivo_nombre = p.cultivo.nombre_cultivo if p.cultivo else 'Sin cultivo'
        if cultivo_nombre not in resumen_cultivos:
            resumen_cultivos[cultivo_nombre] = {
                'cultivo': cultivo_nombre,
                'cosechas': 0,
                'cantidad': 0,
                'unidad': p.unidad_medida,
                'ingreso': 0,
                'precio_promedio': 0,
            }
        resumen_cultivos[cultivo_nombre]['cosechas'] += 1
        resumen_cultivos[cultivo_nombre]['cantidad'] += float(p.cantidad or 0)
        resumen_cultivos[cultivo_nombre]['ingreso'] += p.ingreso_total

    for item in resumen_cultivos.values():
        if item['cantidad'] > 0:
            item['precio_promedio'] = item['ingreso'] / item['cantidad']

    ultimas_cosechas = (
        Produccion.query
        .filter(Produccion.id_parcela.in_(parcelas_ids))
        .order_by(Produccion.fecha_cosecha.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'produccion/resumen.html',
        producciones=producciones,
        total_cosechas=total_cosechas,
        total_cantidad=total_cantidad,
        total_ingreso=total_ingreso,
        resumen_cultivos=list(resumen_cultivos.values()),
        ultimas_cosechas=ultimas_cosechas,
    )
