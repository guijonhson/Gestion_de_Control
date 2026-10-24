from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Productor
from app.utils.permisos import es_admin, obtener_productor
from app.utils.validaciones import (
    ErrorValidacion,
    validar_correo,
    validar_largo,
    validar_telefono,
)

bp = Blueprint('productores', __name__, url_prefix='/productores')


@bp.route('/')
@login_required
def listar():
    if not es_admin():
        flash('No tienes permisos para acceder.', 'danger')
        return redirect(url_for('dashboard.index'))

    productores = Productor.query.order_by(Productor.nombre).all()
    return render_template('productores/listar.html', productores=productores)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if not es_admin():
        flash('No tienes permisos para acceder.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            nombre = validar_largo(
                request.form.get('nombre'), 100, 'El nombre', obligatorio=True
            )
            telefono = validar_telefono(request.form.get('telefono'))
            correo = validar_correo(request.form.get('correo'))
            if Productor.query.filter_by(correo=correo).first():
                raise ErrorValidacion('El correo ya está registrado.')

            db.session.add(Productor(nombre=nombre, telefono=telefono, correo=correo))
            db.session.commit()
            flash('Productor creado exitosamente.', 'success')
            return redirect(url_for('productores.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('productores/crear.html')


@bp.route('/ver/<int:id>')
@login_required
def ver(id):
    productor = obtener_productor(id)
    return render_template('productores/ver.html', productor=productor)
