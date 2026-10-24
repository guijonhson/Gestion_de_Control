from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Aplicador
from app.utils.permisos import obtener_aplicador
from app.utils.validaciones import (
    ErrorValidacion,
    limpiar_texto,
    validar_largo,
    validar_telefono,
)

bp = Blueprint('aplicadores', __name__, url_prefix='/aplicadores')


@bp.route('/')
@login_required
def listar():
    aplicadores = Aplicador.query.filter_by(
        id_productor=current_user.id_productor
    ).all()
    return render_template('aplicadores/listar.html', aplicadores=aplicadores)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            nombre = validar_largo(
                request.form.get('nombre'), 100, 'El nombre', obligatorio=True
            )
            cargo = validar_largo(request.form.get('cargo'), 50, 'El cargo')
            telefono = validar_telefono(request.form.get('telefono'))

            db.session.add(
                Aplicador(
                    id_productor=current_user.id_productor,
                    nombre=nombre,
                    cargo=cargo,
                    telefono=telefono,
                )
            )
            db.session.commit()
            flash('Aplicador creado exitosamente.', 'success')
            return redirect(url_for('aplicadores.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('aplicadores/crear.html')


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    aplicador = obtener_aplicador(id)
    db.session.delete(aplicador)
    db.session.commit()
    flash('Aplicador eliminado exitosamente.', 'success')
    return redirect(url_for('aplicadores.listar'))
