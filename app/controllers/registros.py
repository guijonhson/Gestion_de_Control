from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import (
    Aplicador,
    Cultivo,
    Finca,
    Parcela,
    Producto,
    RegistroAgricola,
)
from app.utils.permisos import obtener_parcela, obtener_registro
from app.utils.validaciones import (
    ErrorValidacion,
    a_entero,
    a_fecha,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('registros', __name__, url_prefix='/registros')


@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    parcelas_ids = [p.id for p in parcelas]
    registros = (
        RegistroAgricola.query
        .filter(RegistroAgricola.id_parcela.in_(parcelas_ids))
        .order_by(RegistroAgricola.fecha.desc())
        .all()
    )
    return render_template('registros/listar.html', registros=registros)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    cultivos = Cultivo.query.all()
    productos = Producto.query.all()
    aplicadores = Aplicador.query.filter_by(id_productor=current_user.id_productor).all()

    datos = {}
    if request.method == 'POST':
        datos = request.form
        try:
            fecha = a_fecha(request.form.get('fecha'), 'La fecha', obligatoria=True)
            id_cultivo = a_entero(request.form.get('id_cultivo'), 'El cultivo', minimo=1)
            id_producto = a_entero(request.form.get('id_producto'), 'El producto', minimo=1)
            id_parcela = a_entero(request.form.get('id_parcela'), 'La parcela', minimo=1)
            id_aplicador = a_entero(request.form.get('id_aplicador'), 'El aplicador', minimo=1)
            tipo_control = limpiar_texto(request.form.get('tipo_control'))
            validar_largo(tipo_control, 50, 'El tipo de control', obligatorio=True)
            dosis = limpiar_texto(request.form.get('dosis'))
            validar_largo(dosis, 50, 'La dosis')
            observaciones = limpiar_texto(request.form.get('observaciones'))

            parcela = obtener_parcela(id_parcela)
            if parcela.id_finca not in fincas_ids:
                raise ErrorValidacion('La parcela seleccionada no pertenece a tus fincas.')
            if not Cultivo.query.get(id_cultivo):
                raise ErrorValidacion('El cultivo seleccionado no existe.')
            if not Producto.query.get(id_producto):
                raise ErrorValidacion('El producto seleccionado no existe.')
            if not Aplicador.query.filter_by(
                id=id_aplicador, id_productor=current_user.id_productor
            ).first():
                raise ErrorValidacion('El aplicador seleccionado no existe.')

            registro = RegistroAgricola(
                fecha=fecha,
                id_cultivo=id_cultivo,
                id_producto=id_producto,
                tipo_control=tipo_control,
                dosis=dosis or None,
                id_parcela=id_parcela,
                id_aplicador=id_aplicador,
                observaciones=observaciones or None,
            )
            db.session.add(registro)
            db.session.commit()
            flash('Registro agrícola creado exitosamente.', 'success')
            return redirect(url_for('registros.listar'))
        except (ErrorValidacion, ValueError) as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'registros/crear.html',
        fincas=fincas,
        parcelas=parcelas,
        cultivos=cultivos,
        productos=productos,
        aplicadores=aplicadores,
        datos=datos,
    )


@bp.route('/ver/<int:id>')
@login_required
def ver(id):
    registro = obtener_registro(id)
    return render_template('registros/ver.html', registro=registro)


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    registro = obtener_registro(id)
    db.session.delete(registro)
    db.session.commit()
    flash('Registro eliminado exitosamente.', 'success')
    return redirect(url_for('registros.listar'))
