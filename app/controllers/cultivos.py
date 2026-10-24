from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.config.database import db
from app.models import Cultivo
from app.utils.permisos import exigir_admin
from app.utils.validaciones import ErrorValidacion, a_entero, limpiar_texto, validar_largo

bp = Blueprint('cultivos', __name__, url_prefix='/cultivos')


@bp.route('/')
@login_required
def listar():
    cultivos = Cultivo.query.order_by(Cultivo.nombre_cultivo).all()
    return render_template('cultivos/listar.html', cultivos=cultivos)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            nombre_cultivo = limpiar_texto(request.form.get('nombre_cultivo'))
            validar_largo(nombre_cultivo, 100, 'El nombre del cultivo', obligatorio=True)
            ciclo_dias = a_entero(
                request.form.get('ciclo_dias_aprox'),
                'El ciclo en días',
                minimo=1,
                obligatorio=False,
            )
            db.session.add(
                Cultivo(nombre_cultivo=nombre_cultivo, ciclo_dias_aprox=ciclo_dias)
            )
            db.session.commit()
            flash('Cultivo creado exitosamente.', 'success')
            return redirect(url_for('cultivos.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('cultivos/crear.html')


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    exigir_admin()
    cultivo = Cultivo.query.get_or_404(id)
    try:
        db.session.delete(cultivo)
        db.session.commit()
        flash('Cultivo eliminado exitosamente.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('No se puede eliminar porque está en uso.', 'warning')
    return redirect(url_for('cultivos.listar'))
