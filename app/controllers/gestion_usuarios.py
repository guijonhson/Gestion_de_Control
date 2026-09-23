from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
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
from app.utils.suscripcion import verificar_limite

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
    return render_template('gestion_usuarios/listar.html', usuarios=usuarios)

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
        id_productor = request.form.get('id_productor')
        nombre_usuario = request.form.get('nombre_usuario')
        correo = request.form.get('correo')
        password = request.form.get('password')
        rol = request.form.get('rol')
        
        if Usuario.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('gestion_usuarios.crear'))
        
        usuario = Usuario(
            id_productor=int(id_productor),
            nombre_usuario=nombre_usuario,
            correo=correo,
            rol=rol,
            activo=True
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('gestion_usuarios.listar'))
    
    return render_template('gestion_usuarios/crear.html', productores=productores)

@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not verificar_acceso_usuario(id):
        flash('No tiene permisos para acceder.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    usuario = Usuario.query.get_or_404(id)
    productores = Productor.query.all()
    
    if request.method == 'POST':
        usuario.nombre_usuario = request.form.get('nombre_usuario')
        usuario.correo = request.form.get('correo')
        
        if current_user.rol == 'administrador':
            usuario.rol = request.form.get('rol')
        
        nuevo_password = request.form.get('password')
        if nuevo_password:
            usuario.set_password(nuevo_password)
        
        if current_user.rol == 'administrador':
            estado = request.form.get('activo')
            usuario.activo = True if estado == '1' else False
        
        db.session.commit()
        
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('gestion_usuarios.listar'))
    
    return render_template('gestion_usuarios/editar.html', usuario=usuario, productores=productores)

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
            parcelas_ids = [p.id_parcela for p in parcelas]
            
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
