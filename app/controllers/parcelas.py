from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Parcela, Finca
from app.utils.suscripcion import verificar_limite

bp = Blueprint('parcelas', __name__, url_prefix='/parcelas')

@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
    return render_template('parcelas/listar.html', parcelas=parcelas)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    puede, mensaje = verificar_limite(current_user, 'parcela')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))
    
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    
    if request.method == 'POST':
        id_finca = request.form.get('id_finca')
        numero_parcela = request.form.get('numero_parcela')
        area = request.form.get('area')
        
        parcela = Parcela(
            id_finca=int(id_finca),
            numero_parcela=numero_parcela,
            area=float(area) if area else None
        )
        db.session.add(parcela)
        db.session.commit()
        
        flash('Parcela creada exitosamente.', 'success')
        return redirect(url_for('parcelas.listar'))
    
    return render_template('parcelas/crear.html', fincas=fincas)

@bp.route('/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    try:
        parcela = Parcela.query.get(int(id))
    except (ValueError, TypeError):
        flash('Parcela no encontrada.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    if not parcela:
        flash('Parcela no encontrada.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    # Verificar que la parcela pertenece al productor del usuario actual
    if parcela.finca.id_productor != current_user.id_productor:
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    
    if request.method == 'POST':
        id_finca = request.form.get('id_finca')
        parcela.id_finca = int(id_finca)
        parcela.numero_parcela = request.form.get('numero_parcela')
        area = request.form.get('area')
        parcela.area = float(area) if area else None
        db.session.commit()
        
        flash('Parcela actualizada exitosamente.', 'success')
        return redirect(url_for('parcelas.listar'))
    
    return render_template('parcelas/editar.html', parcela=parcela, fincas=fincas)

@bp.route('/eliminar/<id>', methods=['POST'])
@login_required
def eliminar(id):
    try:
        parcela = Parcela.query.get(int(id))
    except (ValueError, TypeError):
        flash('Parcela no encontrada.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    if not parcela:
        flash('Parcela no encontrada.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    if parcela.finca.id_productor != current_user.id_productor:
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('parcelas.listar'))
    
    db.session.delete(parcela)
    db.session.commit()
    flash('Parcela eliminada exitosamente.', 'success')
    return redirect(url_for('parcelas.listar'))
