from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models.usuario import Usuario
from app.models.productor import Productor
from app.models.finca import Finca
from app.models.parcela import Parcela
from app.models.aplicador import Aplicador
from app.models.registro_agricola import RegistroAgricola
from app.models.produccion import Produccion
from app.models.gastos import Gasto
from app.models.inventario import Inventario
from app.config.database import db
from app.utils.suscripcion import verificar_limite, obtener_suscripcion_activa
from app.utils.migraciones import obtener_pendientes, aplicar_todo
from app.utils.planes import nombre_plan_visible
from app.utils.validaciones import (
    ErrorValidacion,
    a_entero,
    limpiar_texto,
    validar_correo,
    validar_largo,
    validar_password,
)
from app.models import Plan, Suscripcion
from datetime import datetime

bp = Blueprint('gestion_usuarios', __name__, url_prefix='/gestion/usuarios')

def verificar_admin():
    if current_user.rol != 'administrador':
        flash('No tiene permisos para acceder.', 'danger')
        return False
    return True

def verificar_acceso_usuario(usuario_id):
    if current_user.rol == 'administrador':
        return True
    usuario = Usuario.query.get(usuario_id)
    if usuario and usuario.id_productor == current_user.id_productor:
        return True
    return False

@bp.route('/')
@login_required
def listar():
    if current_user.rol == 'administrador':
        usuarios = Usuario.query.all()
    else:
        usuarios = Usuario.query.filter_by(id_productor=current_user.id_productor).all()

    planes = Plan.query.filter_by(activo=True).all()
    suscripcion_por_usuario = {}
    for u in usuarios:
        suscripcion_por_usuario[u.id] = obtener_suscripcion_activa(u.id_productor)

    pendientes = []
    if current_user.rol == 'administrador':
        try:
            pendientes = obtener_pendientes()
        except Exception as e:
            db.session.rollback()
            print(f"[migraciones] No se pudo revisar pendientes: {e}")

    return render_template(
        'gestion_usuarios/listar.html',
        usuarios=usuarios,
        planes=planes,
        suscripcion_por_usuario=suscripcion_por_usuario,
        pendientes=pendientes,
    )


@bp.route('/actualizar_base_datos', methods=['POST'])
@login_required
def actualizar_base_datos():
    if not verificar_admin():
        return redirect(url_for('gestion_usuarios.listar'))

    try:
        antes = obtener_pendientes()
        aplicar_todo()
        despues = obtener_pendientes()
    except Exception as e:
        db.session.rollback()
        print(f"[migraciones] Error al actualizar: {e}")
        flash('No se pudo completar la actualización. Revisa los registros del servidor.', 'danger')
        return redirect(url_for('gestion_usuarios.listar'))

    if despues:
        flash('Actualización parcial. Aún falta: ' + ', '.join(despues), 'warning')
    elif antes:
        flash('Base de datos actualizada correctamente: ' + ', '.join(antes), 'success')
    else:
        flash('La base de datos ya estaba actualizada.', 'info')
    return redirect(url_for('gestion_usuarios.listar'))


@bp.route('/cambiar_plan/<int:id>', methods=['POST'])
@login_required
def cambiar_plan(id):
    if not verificar_admin():
        return redirect(url_for('gestion_usuarios.listar'))

    usuario = Usuario.query.get_or_404(id)
    id_plan = request.form.get('id_plan')
    plan = Plan.query.get_or_404(id_plan)

    suscripcion = obtener_suscripcion_activa(usuario.id_productor)

    if suscripcion:
        suscripcion.id_plan = plan.id
        suscripcion.estado = 'activa'
    else:
        suscripcion = Suscripcion(
            id_productor=usuario.id_productor,
            id_plan=plan.id,
            fecha_inicio=datetime.now().date(),
            fecha_fin=None,
            estado='activa'
        )
        db.session.add(suscripcion)

    db.session.commit()

    flash(
        f'Plan de {usuario.nombre_usuario} actualizado a '
        f'{nombre_plan_visible(plan.nombre_plan)}.',
        'success',
    )
    return redirect(url_for('gestion_usuarios.listar'))

@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if not verificar_admin():
        return redirect(url_for('dashboard.index'))
    
    puede, mensaje = verificar_limite(current_user, 'usuario')
    if not puede:
        flash(mensaje, 'warning')
        return redirect(url_for('suscripciones.upgrade'))
    
    productores = Productor.query.all()
    
    if request.method == 'POST':
        try:
            id_productor = a_entero(
                request.form.get('id_productor'), 'El productor', minimo=1
            )
            if not Productor.query.get(id_productor):
                raise ErrorValidacion('El productor seleccionado no existe.')
            nombre_usuario = validar_largo(
                request.form.get('nombre_usuario'),
                50,
                'El nombre de usuario',
                obligatorio=True,
            )
            correo = validar_correo(request.form.get('correo'))
            password = validar_password(request.form.get('password'))
            rol = request.form.get('rol')
            if rol not in ('cliente', 'administrador'):
                raise ErrorValidacion('El rol seleccionado no es válido.')

            if Usuario.query.filter(func.lower(Usuario.correo) == correo).first():
                raise ErrorValidacion('El correo ya está registrado.')

            usuario = Usuario(
                id_productor=id_productor,
                nombre_usuario=nombre_usuario,
                correo=correo,
                rol=rol,
                activo=True,
            )
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('gestion_usuarios.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('El correo ya está registrado.', 'danger')

    return render_template('gestion_usuarios/crear.html', productores=productores)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not verificar_acceso_usuario(id):
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            nombre_productor = validar_largo(
                request.form.get('nombre_productor'),
                100,
                'El nombre del productor',
                obligatorio=True,
            )
            nombre_usuario = validar_largo(
                request.form.get('nombre_usuario'),
                50,
                'El nombre de usuario',
                obligatorio=True,
            )
            correo = validar_correo(request.form.get('correo'))

            existente = (
                Usuario.query
                .filter(func.lower(Usuario.correo) == correo, Usuario.id != usuario.id)
                .first()
            )
            if existente:
                raise ErrorValidacion('El correo ya está registrado.')

            usuario.nombre_usuario = nombre_usuario
            usuario.correo = correo

            if usuario.productor:
                usuario.productor.nombre = nombre_productor

            if current_user.rol == 'administrador':
                rol = request.form.get('rol')
                if rol not in ('cliente', 'administrador'):
                    raise ErrorValidacion('El rol seleccionado no es válido.')
                usuario.rol = rol

            nuevo_password = request.form.get('password')
            if nuevo_password:
                validar_password(nuevo_password)
                usuario.set_password(nuevo_password)

            if current_user.rol == 'administrador':
                estado = request.form.get('activo')
                usuario.activo = True if estado == '1' else False

            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('gestion_usuarios.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('El correo ya está registrado.', 'danger')

    return render_template('gestion_usuarios/editar.html', usuario=usuario)

@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    if not verificar_admin():
        return redirect(url_for('dashboard.index'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('No puede eliminarse a sí mismo.', 'danger')
        return redirect(url_for('gestion_usuarios.listar'))
    
    admins_count = Usuario.query.filter_by(rol='administrador').count()
    if usuario.rol == 'administrador' and admins_count <= 1:
        flash('No puede eliminar al único administrador.', 'danger')
        return redirect(url_for('gestion_usuarios.listar'))
    
    eliminar_historial = request.form.get('eliminar_historial', '0') == '1'
    
    try:
        if eliminar_historial and usuario.id_productor:
            id_productor = usuario.id_productor
            
            fincas = Finca.query.filter_by(id_productor=id_productor).all()
            fincas_ids = [f.id for f in fincas]
            
            parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
            parcelas_ids = [p.id for p in parcelas]
            
            RegistroAgricola.query.filter(RegistroAgricola.id_parcela.in_(parcelas_ids)).delete()
            Produccion.query.filter(Produccion.id_parcela.in_(parcelas_ids)).delete()
            Gasto.query.filter(Gasto.id_finca.in_(fincas_ids)).delete()
            Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).delete()
            Aplicador.query.filter_by(id_productor=id_productor).delete()
            Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).delete()
            Finca.query.filter_by(id_productor=id_productor).delete()
            Productor.query.filter_by(id=id_productor).delete()
        
        nombre_eliminado = usuario.nombre_usuario
        db.session.delete(usuario)
        db.session.commit()
        
        flash(f'Usuario "{nombre_eliminado}" eliminado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
    
    return redirect(url_for('gestion_usuarios.listar'))

@bp.route('/borrar_historial/<int:id>', methods=['GET', 'POST'])
@login_required
def borrar_historial(id):
    if not verificar_admin():
        return redirect(url_for('dashboard.index'))
    
    usuario = Usuario.query.get_or_404(id)
    productor = usuario.id_productor
    
    if request.method == 'POST':
        confirmar_nombre = request.form.get('confirmar_nombre')
        
        if confirmar_nombre != usuario.nombre_usuario:
            flash('El nombre de usuario no coincide. Intente nuevamente.', 'danger')
            return redirect(url_for('gestion_usuarios.borrar_historial', id=id))
        
        fincas = Finca.query.filter_by(id_productor=productor).all()
        fincas_ids = [f.id for f in fincas]
        
        parcelas = Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).all()
        parcelas_ids = [p.id for p in parcelas]
        
        RegistroAgricola.query.filter(RegistroAgricola.id_parcela.in_(parcelas_ids)).delete()
        Produccion.query.filter(Produccion.id_parcela.in_(parcelas_ids)).delete()
        Gasto.query.filter(Gasto.id_finca.in_(fincas_ids)).delete()
        Inventario.query.filter(Inventario.id_finca.in_(fincas_ids)).delete()
        Aplicador.query.filter_by(id_productor=productor).delete()
        Parcela.query.filter(Parcela.id_finca.in_(fincas_ids)).delete()
        Finca.query.filter_by(id_productor=productor).delete()
        
        db.session.commit()
        
        flash(f'Historial del usuario {usuario.nombre_usuario} ha sido borrado exitosamente.', 'success')
        return redirect(url_for('gestion_usuarios.listar'))
    
    return render_template('gestion_usuarios/confirmar_borrar.html', usuario=usuario)
