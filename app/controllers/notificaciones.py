from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Notificacion
from app.utils.permisos import es_admin, obtener_notificacion

bp = Blueprint('notificaciones', __name__, url_prefix='/notificaciones')


@bp.route('/')
@login_required
def listar():
    if es_admin():
        notificaciones = (
            Notificacion.query
            .filter(Notificacion.id_productor.is_(None))
            .order_by(Notificacion.fecha.desc())
            .all()
        )
    else:
        notificaciones = (
            Notificacion.query
            .filter_by(id_productor=current_user.id_productor)
            .order_by(Notificacion.fecha.desc())
            .all()
        )

    return render_template('notificaciones/index.html', notificaciones=notificaciones)


@bp.route('/marcar_leida/<int:id>', methods=['POST'])
@login_required
def marcar_leida(id):
    notificacion = obtener_notificacion(id)
    notificacion.leido = True
    db.session.commit()
    flash('Notificación marcada como leída.', 'success')
    return redirect(url_for('notificaciones.listar'))


@bp.route('/marcar_todas_leidas', methods=['POST'])
@login_required
def marcar_todas_leidas():
    if es_admin():
        Notificacion.query.filter(
            Notificacion.id_productor.is_(None),
            Notificacion.leido.is_(False),
        ).update({'leido': True})
    else:
        Notificacion.query.filter_by(
            id_productor=current_user.id_productor,
            leido=False,
        ).update({'leido': True})

    db.session.commit()
    flash('Todas las notificaciones marcadas como leídas.', 'success')
    return redirect(url_for('notificaciones.listar'))


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    if not es_admin():
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('notificaciones.listar'))

    notificacion = Notificacion.query.get_or_404(id)
    db.session.delete(notificacion)
    db.session.commit()
    flash('Notificación eliminada.', 'success')
    return redirect(url_for('notificaciones.listar'))


@bp.route('/contador')
@login_required
def contador():
    if es_admin():
        count = Notificacion.query.filter(
            Notificacion.id_productor.is_(None),
            Notificacion.leido.is_(False),
        ).count()
    else:
        count = Notificacion.query.filter_by(
            id_productor=current_user.id_productor,
            leido=False,
        ).count()

    return {'count': count}
