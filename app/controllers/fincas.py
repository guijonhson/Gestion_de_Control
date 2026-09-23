from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Finca
from app.utils.suscripcion import verificar_limite

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
    
    if request.method == 'POST':
        nombre_finca = request.form.get('nombre_finca')
        ubicacion = request.form.get('ubicacion')
        area_total = request.form.get('area_total')
        
        # current_user.id_productor es un integer
        finca = Finca(
            id_productor=current_user.id_productor,
            nombre_finca=nombre_finca,
            ubicacion=ubicacion,
            area_total=float(area_total) if area_total else None
        )
        db.session.add(finca)
        db.session.commit()
        
        flash('Finca creada exitosamente.', 'success')
        return redirect(url_for('fincas.listar'))
    
    return render_template('fincas/crear.html')

@bp.route('/ver/<id>')
@login_required
def ver(id):
    try:
        id_finca = int(id)
        finca = Finca.query.get(id_finca)
    except (ValueError, TypeError):
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if not finca:
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if finca.id_productor != current_user.id_productor:
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('fincas.listar'))
    return render_template('fincas/ver.html', finca=finca)

@bp.route('/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    try:
        id_finca = int(id)
        finca = Finca.query.get(id_finca)
    except (ValueError, TypeError):
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if not finca:
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if finca.id_productor != current_user.id_productor:
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if request.method == 'POST':
        finca.nombre_finca = request.form.get('nombre_finca')
        finca.ubicacion = request.form.get('ubicacion')
        area_total = request.form.get('area_total')
        finca.area_total = float(area_total) if area_total else None
        db.session.commit()
        
        flash('Finca actualizada exitosamente.', 'success')
        return redirect(url_for('fincas.listar'))
    
    return render_template('fincas/editar.html', finca=finca)

@bp.route('/eliminar/<id>', methods=['POST'])
@login_required
def eliminar(id):
    try:
        id_finca = int(id)
        finca = Finca.query.get(id_finca)
    except (ValueError, TypeError):
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if not finca:
        flash('Finca no encontrada.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    if finca.id_productor != current_user.id_productor:
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('fincas.listar'))
    
    db.session.delete(finca)
    db.session.commit()
    flash('Finca eliminada exitosamente.', 'success')
    return redirect(url_for('fincas.listar'))
