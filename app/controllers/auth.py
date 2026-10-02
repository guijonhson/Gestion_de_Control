from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.config.database import db
from app.models import Productor, Usuario, Suscripcion, Plan, Notificacion
from app.utils.email import enviar_alerta_email
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        if usuario and usuario.check_password(password):
            if usuario.activo:
                usuario.ultimo_acceso = datetime.now()
                db.session.commit()
                login_user(usuario)
                return redirect(url_for('dashboard.index'))
            else:
                flash('Usuario inactivo. Contacte al administrador.', 'danger')
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        nombre_productor = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        nombre_usuario = request.form.get('nombre_usuario')
        password = request.form.get('password')
        
        if Productor.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado.', 'danger')
            return redirect(url_for('auth.register'))
        
        es_primer_usuario = Usuario.query.count() == 0
        
        productor = Productor(
            nombre=nombre_productor,
            telefono=telefono,
            correo=correo
        )
        db.session.add(productor)
        db.session.commit()
        
        usuario = Usuario(
            id_productor=productor.id,
            nombre_usuario=nombre_usuario,
            correo=correo,
            rol='administrador' if es_primer_usuario else 'cliente',
            activo=True,
            fecha_registro=datetime.now()
        )
        usuario.set_password(password)
        db.session.add(usuario)
        
        plan_free = Plan.query.filter_by(nombre_plan='FREE').first()
        if not plan_free:
            from app.models.plan import init_planes
            init_planes()
            plan_free = Plan.query.filter_by(nombre_plan='FREE').first()
        
        suscripcion = Suscripcion(
            id_productor=productor.id,
            id_plan=plan_free.id,
            fecha_inicio=datetime.now().date(),
            fecha_fin=None,
            estado='activa'
        )
        db.session.add(suscripcion)
        db.session.commit()
        
        noti = Notificacion(
            mensaje=f"Nuevo usuario registrado: {correo} ({nombre_usuario}) - Plan FREE",
            tipo='registro',
            leido=False
        )
        db.session.add(noti)
        db.session.commit()
        
        enviar_alerta_email(
            asunto="Nuevo usuario registrado en Gestión de Control",
            mensaje=(
                f"Se registró un nuevo usuario.\n\n"
                f"Nombre: {nombre_usuario}\n"
                f"Correo: {correo}\n"
                f"Productor/Empresa: {nombre_productor}\n"
                f"Teléfono: {telefono}\n"
                f"Rol asignado: {'Administrador' if es_primer_usuario else 'Cliente'}\n"
                f"Plan inicial: FREE"
            ),
        )
        
        flash(f'Registro exitoso. Rol asignado: {"Administrador" if es_primer_usuario else "Cliente"}. Por favor inicie sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
