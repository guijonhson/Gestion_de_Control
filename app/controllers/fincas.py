from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Finca
from app.utils.permisos import obtener_finca
from app.utils.suscripcion import verificar_limite
from app.utils.validaciones import (
    ErrorValidacion,
    a_decimal,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('fincas', __name__, url_prefix='/fincas')


@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    return render_template('fincas/listar.html', fincas=fincas)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    puede, mensaje = verificar_limite(current_user, 'finca')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))

    datos = {}
    if request.method == 'POST':
        datos = request.form
        try:
            nombre_finca = limpiar_texto(request.form.get('nombre_finca'))
            validar_largo(nombre_finca, 100, 'El nombre de la finca', obligatorio=True)
            ubicacion = limpiar_texto(request.form.get('ubicacion'))
            validar_largo(ubicacion, 200, 'La ubicación')
            rubro = limpiar_texto(request.form.get('rubro'))
            validar_largo(rubro, 200, 'El rubro')
            area_total = a_decimal(
                request.form.get('area_total'), 'El área total', minimo=0
            )

            finca = Finca(
                id_productor=current_user.id_productor,
                nombre_finca=nombre_finca,
                ubicacion=ubicacion or None,
                area_total=area_total,
                rubro=rubro or None,
            )
            db.session.add(finca)
            db.session.commit()
            flash('Finca creada exitosamente.', 'success')
            return redirect(url_for('fincas.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('fincas/crear.html', datos=datos)


@bp.route('/ver/<int:id>')
@login_required
def ver(id):
    finca = obtener_finca(id)
    return render_template('fincas/ver.html', finca=finca)


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    finca = obtener_finca(id)

    if request.method == 'POST':
        try:
            nombre_finca = limpiar_texto(request.form.get('nombre_finca'))
            validar_largo(nombre_finca, 100, 'El nombre de la finca', obligatorio=True)
            ubicacion = limpiar_texto(request.form.get('ubicacion'))
            validar_largo(ubicacion, 200, 'La ubicación')
            rubro = limpiar_texto(request.form.get('rubro'))
            validar_largo(rubro, 200, 'El rubro')
            area_total = a_decimal(
                request.form.get('area_total'), 'El área total', minimo=0
            )

            finca.nombre_finca = nombre_finca
            finca.ubicacion = ubicacion or None
            finca.area_total = area_total
            finca.rubro = rubro or None
            db.session.commit()
            flash('Finca actualizada exitosamente.', 'success')
            return redirect(url_for('fincas.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('fincas/editar.html', finca=finca)


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    finca = obtener_finca(id)
    db.session.delete(finca)
    db.session.commit()
    flash('Finca eliminada exitosamente.', 'success')
    return redirect(url_for('fincas.listar'))
