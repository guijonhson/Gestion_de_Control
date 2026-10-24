from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Finca, Inventario, Producto
from app.utils.permisos import obtener_finca, obtener_inventario
from app.utils.suscripcion import verificar_limite
from app.utils.validaciones import (
    ErrorValidacion,
    a_decimal,
    a_entero,
    a_fecha,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('inventario', __name__, url_prefix='/inventario')

UNIDADES = ('kg', 'litros', 'unidades', 'sacos', 'galones')


def _finca_del_usuario(id_finca):
    return obtener_finca(id_finca)


def _validar_producto(id_producto):
    producto = Producto.query.get(id_producto)
    if not producto:
        raise ErrorValidacion('El producto seleccionado no existe.')
    return producto


def _leer_datos():
    id_producto = a_entero(request.form.get('id_producto'), 'El producto', minimo=1)
    id_finca = a_entero(request.form.get('id_finca'), 'La finca', minimo=1)
    _validar_producto(id_producto)
    finca = _finca_del_usuario(id_finca)

    cantidad = a_decimal(
        request.form.get('cantidad'), 'La cantidad', minimo=0, obligatorio=True
    )
    unidad_medida = limpiar_texto(request.form.get('unidad_medida')) or 'kg'
    if unidad_medida not in UNIDADES:
        raise ErrorValidacion('La unidad de medida no es válida.')
    stock_minimo = a_decimal(
        request.form.get('stock_minimo'), 'El stock mínimo', minimo=0
    ) or 0
    costo_unitario = a_decimal(
        request.form.get('costo_unitario'), 'El costo unitario', minimo=0
    ) or 0
    proveedor = validar_largo(request.form.get('proveedor'), 100, 'El proveedor')
    fecha = a_fecha(request.form.get('fecha_ingreso'), 'La fecha de ingreso')
    return {
        'id_producto': id_producto,
        'id_finca': finca.id,
        'cantidad': cantidad,
        'unidad_medida': unidad_medida,
        'stock_minimo': stock_minimo,
        'costo_unitario': costo_unitario,
        'proveedor': proveedor,
        'fecha_ingreso': (
            datetime.combine(fecha, datetime.min.time()) if fecha else datetime.utcnow()
        ),
    }


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

    productos = Producto.query.order_by(Producto.nombre_producto).all()
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()

    if request.method == 'POST':
        try:
            datos = _leer_datos()
            db.session.add(Inventario(**datos))
            db.session.commit()
            flash('Producto agregado al inventario exitosamente.', 'success')
            return redirect(url_for('inventario.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'inventario/crear.html', productos=productos, fincas=fincas
    )


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    inventario = obtener_inventario(id)
    productos = Producto.query.order_by(Producto.nombre_producto).all()
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()

    if request.method == 'POST':
        try:
            datos = _leer_datos()
            for campo, valor in datos.items():
                setattr(inventario, campo, valor)
            db.session.commit()
            flash('Inventario actualizado exitosamente.', 'success')
            return redirect(url_for('inventario.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'inventario/editar.html',
        inventario=inventario,
        productos=productos,
        fincas=fincas,
    )


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    inventario = obtener_inventario(id)
    db.session.delete(inventario)
    db.session.commit()
    flash('Registro de inventario eliminado.', 'success')
    return redirect(url_for('inventario.listar'))


@bp.route('/alertas')
@login_required
def alertas():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    inventarios = Inventario.query.filter(
        Inventario.id_finca.in_(fincas_ids), Inventario.cantidad <= 0
    ).all()
    return render_template('inventario/alertas.html', inventarios=inventarios)


@bp.route('/reportes')
@login_required
def reportes():
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()
    fincas_ids = [f.id for f in fincas]
    inventarios = Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).all()

    valor_total = sum(
        (inv.cantidad or 0) * (inv.costo_unitario or 0) for inv in inventarios
    )
    productos_bajo_stock = sum(
        1 for inv in inventarios if (inv.cantidad or 0) <= (inv.stock_minimo or 0)
    )

    return render_template(
        'inventario/reportes.html',
        inventarios=inventarios,
        valor_total=valor_total,
        productos_bajo_stock=productos_bajo_stock,
    )
