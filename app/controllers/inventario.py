from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Inventario, Producto, Finca
from app.utils.suscripcion import verificar_limite
from datetime import datetime

bp = Blueprint('inventario', __name__, url_prefix='/inventario')

@bp.route('/')
@login_required
def listar():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    inventarios = Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).all()
    return render_template('inventario/listar.html', inventarios=inventarios)

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    puede, mensaje = verificar_limite(current_user, 'inventario')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))
    
    productos = Producto.query.all()
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    
    if request.method == 'POST':
        id_producto = request.form.get('id_producto')
        id_finca = request.form.get('id_finca')
        cantidad = request.form.get('cantidad')
        unidad_medida = request.form.get('unidad_medida')
        fecha_ingreso = request.form.get('fecha_ingreso')
        proveedor = request.form.get('proveedor')
        costo_unitario = request.form.get('costo_unitario')
        stock_minimo = request.form.get('stock_minimo')
        
        inventario = Inventario(
            id_producto=int(id_producto),
            id_finca=int(id_finca),
            cantidad=float(cantidad) if cantidad else 0,
            unidad_medida=unidad_medida,
            fecha_ingreso=datetime.strptime(fecha_ingreso, '%Y-%m-%d') if fecha_ingreso else datetime.utcnow(),
            proveedor=proveedor,
            costo_unitario=float(costo_unitario) if costo_unitario else 0,
            stock_minimo=float(stock_minimo) if stock_minimo else 0
        )
        db.session.add(inventario)
        db.session.commit()
        
        flash('Producto agregado al inventario exitosamente.', 'success')
        return redirect(url_for('inventario.listar'))
    
    return render_template('inventario/crear.html', productos=productos, fincas=fincas)

@bp.route('/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    inventario = Inventario.query.get(int(id))
    productos = Producto.query.all()
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    
    if request.method == 'POST':
        id_producto = request.form.get('id_producto')
        id_finca = request.form.get('id_finca')
        inventario.id_producto = int(id_producto)
        inventario.id_finca = int(id_finca)
        inventario.cantidad = float(request.form.get('cantidad')) if request.form.get('cantidad') else 0
        inventario.unidad_medida = request.form.get('unidad_medida')
        inventario.proveedor = request.form.get('proveedor')
        inventario.costo_unitario = float(request.form.get('costo_unitario')) if request.form.get('costo_unitario') else 0
        inventario.stock_minimo = float(request.form.get('stock_minimo')) if request.form.get('stock_minimo') else 0
        db.session.commit()
        
        flash('Inventario actualizado exitosamente.', 'success')
        return redirect(url_for('inventario.listar'))
    
    return render_template('inventario/editar.html', inventario=inventario, productos=productos, fincas=fincas)

@bp.route('/eliminar/<id>', methods=['POST'])
@login_required
def eliminar(id):
    inventario = Inventario.query.get(int(id))
    if inventario:
        db.session.delete(inventario)
        db.session.commit()
        flash('Registro de inventario eliminado.', 'success')
    else:
        flash('Registro no encontrado.', 'danger')
    return redirect(url_for('inventario.listar'))

@bp.route('/alertas')
@login_required
def alertas():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    inventarios = Inventario.query.filter(Inventario.id_finca.in_(fincas_ids), Inventario.cantidad <= 0).all()
    return render_template('inventario/alertas.html', inventarios=inventarios)

@bp.route('/reportes')
@login_required
def reportes():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    inventarios = Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).all()
    
    valor_total = sum(inv.cantidad * inv.costo_unitario for inv in inventarios)
    productos_bajo_stock = sum(1 for inv in inventarios if inv.cantidad <= inv.stock_minimo)
    
    return render_template('inventario/reportes.html', 
                          inventarios=inventarios,
                          valor_total=valor_total,
                          productos_bajo_stock=productos_bajo_stock)
