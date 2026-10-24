from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.config.database import db
from app.models import Producto
from app.utils.permisos import exigir_admin
from app.utils.validaciones import ErrorValidacion, limpiar_texto, validar_largo

bp = Blueprint('productos', __name__, url_prefix='/productos')

TIPOS_PRODUCTO = ('herbicida', 'fungicida', 'insecticida', 'fertilizante', 'otro')


@bp.route('/')
@login_required
def listar():
    productos = Producto.query.order_by(Producto.nombre_producto).all()
    return render_template('productos/listar.html', productos=productos)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            nombre_producto = limpiar_texto(request.form.get('nombre_producto'))
            validar_largo(nombre_producto, 100, 'El nombre del producto', obligatorio=True)
            tipo_producto = limpiar_texto(request.form.get('tipo_producto'))
            validar_largo(tipo_producto, 50, 'El tipo de producto', obligatorio=True)
            if tipo_producto not in TIPOS_PRODUCTO:
                raise ErrorValidacion('El tipo de producto no es válido.')

            db.session.add(
                Producto(nombre_producto=nombre_producto, tipo_producto=tipo_producto)
            )
            db.session.commit()
            flash('Producto creado exitosamente.', 'success')
            return redirect(url_for('productos.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('productos/crear.html')


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    exigir_admin()
    producto = Producto.query.get_or_404(id)
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado exitosamente.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('No se puede eliminar porque está en uso.', 'warning')
    return redirect(url_for('productos.listar'))
