from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Gasto, Finca, Cultivo
from app.utils.suscripcion import verificar_limite
from datetime import datetime

bp = Blueprint('gastos', __name__, url_prefix='/gastos')

CATEGORIAS = ['semilla', 'fertilizante', 'mano_obra', 'combustible', 'mantenimiento', 'otro']
CATEGORIAS_LABELS = {
    'semilla': 'Semilla',
    'fertilizante': 'Fertilizante',
    'mano_obra': 'Mano de Obra',
    'combustible': 'Combustible',
    'mantenimiento': 'Mantenimiento',
    'otro': 'Otro'
}

@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    gastos = Gasto.query.filter(Gasto.id_finca.in_(fincas_ids)).order_by(Gasto.fecha.desc()).all()
    return render_template('gastos/listar.html', gastos=gastos, categorias=CATEGORIAS_LABELS)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    puede, mensaje = verificar_limite(current_user, 'gasto')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))
    
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    cultivos = Cultivo.query.all()
    
    if request.method == 'POST':
        tipo_gasto = request.form.get('tipo_gasto')
        descripcion = request.form.get('descripcion')
        monto = request.form.get('monto')
        fecha = request.form.get('fecha')
        responsable = request.form.get('responsable')
        id_finca = request.form.get('id_finca')
        id_cultivo = request.form.get('id_cultivo')
        
        gasto = Gasto(
            tipo_gasto=tipo_gasto,
            descripcion=descripcion,
            monto=float(monto) if monto else 0,
            fecha=datetime.strptime(fecha, '%Y-%m-%d').date() if fecha else datetime.utcnow().date(),
            responsable=responsable,
            id_finca=int(id_finca),
            id_cultivo=int(id_cultivo) if id_cultivo else None
        )
        db.session.add(gasto)
        db.session.commit()
        
        flash('Gasto registrado exitosamente.', 'success')
        return redirect(url_for('gastos.listar'))
    
    return render_template('gastos/crear.html', fincas=fincas, cultivos=cultivos, categorias=CATEGORIAS_LABELS)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    gasto = Gasto.query.get_or_404(id)
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    cultivos = Cultivo.query.all()
    
    if request.method == 'POST':
        gasto.tipo_gasto = request.form.get('tipo_gasto')
        gasto.descripcion = request.form.get('descripcion')
        gasto.monto = float(request.form.get('monto')) if request.form.get('monto') else 0
        gasto.fecha = datetime.strptime(request.form.get('fecha'), '%Y-%m-%d').date() if request.form.get('fecha') else datetime.utcnow().date()
        gasto.responsable = request.form.get('responsable')
        gasto.id_finca = int(request.form.get('id_finca'))
        gasto.id_cultivo = int(request.form.get('id_cultivo')) if request.form.get('id_cultivo') else None
        db.session.commit()
        
        flash('Gasto actualizado exitosamente.', 'success')
        return redirect(url_for('gastos.listar'))
    
    return render_template('gastos/editar.html', gasto=gasto, fincas=fincas, cultivos=cultivos, categorias=CATEGORIAS_LABELS)

@bp.route('/buscar', methods=['POST'])
@login_required
def buscar():
    fecha_inicio = request.form.get('fecha_inicio')
    fecha_fin = request.form.get('fecha_fin')
    tipo_gasto = request.form.get('tipo_gasto')
    id_finca = request.form.get('id_finca')
    
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    
    query = Gasto.query.filter(Gasto.id_finca.in_(fincas_ids))
    
    if tipo_gasto:
        query = query.filter(Gasto.tipo_gasto == tipo_gasto)
    if id_finca:
        query = query.filter(Gasto.id_finca == int(id_finca))
    
    gastos = query.order_by(Gasto.fecha.desc()).all()
    return render_template('gastos/listar.html', gastos=gastos, categorias=CATEGORIAS_LABELS)
