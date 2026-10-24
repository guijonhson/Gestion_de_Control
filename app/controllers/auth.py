from collections import defaultdict
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.config.database import db
from app.models import Notificacion, Plan, Productor, Suscripcion, Usuario
from app.utils.email import enviar_alerta_email
from app.utils.validaciones import (
    ErrorValidacion,
    limpiar_texto,
    validar_correo,
    validar_largo,
    validar_password,
    validar_telefono,
)

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Límites simples en memoria (suficientes para una sola instancia en Render).
_INTENTOS_LOGIN = defaultdict(list)
_SOLICITUDES_RECUPERACION = defaultdict(list)
MAX_INTENTOS_LOGIN = 10
VENTANA_LOGIN = timedelta(minutes=15)
MAX_RECUPERACIONES = 3
VENTANA_RECUPERACION = timedelta(hours=1)


def _limpiar_historial(historial, ventana):
    limite = datetime.now() - ventana
    return [marca for marca in historial if marca > limite]


def _supera_limite(historial, clave, maximo, ventana):
    historial[clave] = _limpiar_historial(historial[clave], ventana)
    return len(historial[clave]) >= maximo


def _registrar_intento(historial, clave):
    historial[clave].append(datetime.now())


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    datos = {}
    if request.method == 'POST':
        datos = request.form
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
        ip = ip.split(',')[0].strip()
        if _supera_limite(_INTENTOS_LOGIN, ip, MAX_INTENTOS_LOGIN, VENTANA_LOGIN):
            flash(
                'Demasiados intentos fallidos. Espera unos minutos e intenta de nuevo.',
                'danger',
            )
            return render_template('auth/login.html', datos=datos), 429

        correo = limpiar_texto(request.form.get('correo')).lower()
        password = request.form.get('password') or ''
        recordar = request.form.get('remember') == '1'

        usuario = (
            Usuario.query.filter(func.lower(Usuario.correo) == correo).first()
            if correo
            else None
        )

        if usuario and usuario.check_password(password):
            if not usuario.is_active:
                flash('Usuario inactivo. Contacta al administrador.', 'danger')
                return render_template('auth/login.html', datos=datos)

            _INTENTOS_LOGIN.pop(ip, None)
            usuario.ultimo_acceso = datetime.now()
            db.session.commit()
            login_user(usuario, remember=recordar)
            flash('Bienvenido de nuevo.', 'success')
            return redirect(url_for('dashboard.index'))

        _registrar_intento(_INTENTOS_LOGIN, ip)
        flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html', datos=datos)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    plan_free = Plan.query.filter_by(nombre_plan='FREE').first()
    if not plan_free:
        from app.models.plan import init_planes

        init_planes()
        plan_free = Plan.query.filter_by(nombre_plan='FREE').first()

    datos = {}
    if request.method == 'POST':
        datos = request.form
        try:
            nombre_productor = validar_largo(
                request.form.get('nombre'), 100, 'El nombre del productor', obligatorio=True
            )
            telefono = validar_telefono(request.form.get('telefono'))
            correo = validar_correo(request.form.get('correo'))
            nombre_usuario = validar_largo(
                request.form.get('nombre_usuario'),
                50,
                'El nombre de usuario',
                obligatorio=True,
            )
            password = validar_password(request.form.get('password'))
            confirmacion = request.form.get('password_confirmacion') or ''
            if password != confirmacion:
                raise ErrorValidacion('Las contraseñas no coinciden.')
            if request.form.get('acepto_terminos') != '1':
                raise ErrorValidacion(
                    'Debes aceptar los Términos y la Política de Privacidad.'
                )

            if Usuario.query.filter(func.lower(Usuario.correo) == correo).first():
                raise ErrorValidacion('El correo ya está registrado.')
            if (
                Productor.query
                .filter(func.lower(Productor.correo) == correo)
                .first()
            ):
                raise ErrorValidacion('El correo ya está registrado.')

            es_primer_usuario = Usuario.query.count() == 0
            if not plan_free:
                raise ErrorValidacion(
                    'No pudimos crear la cuenta. Intenta de nuevo.'
                )

            productor = Productor(
                nombre=nombre_productor,
                telefono=telefono,
                correo=correo,
            )
            db.session.add(productor)
            db.session.flush()

            usuario = Usuario(
                id_productor=productor.id,
                nombre_usuario=nombre_usuario,
                correo=correo,
                rol='administrador' if es_primer_usuario else 'cliente',
                activo=True,
                fecha_registro=datetime.now(),
                fecha_aceptacion_terminos=datetime.now(),
            )
            usuario.set_password(password)
            db.session.add(usuario)

            db.session.add(
                Suscripcion(
                    id_productor=productor.id,
                    id_plan=plan_free.id,
                    fecha_inicio=datetime.now().date(),
                    fecha_fin=None,
                    estado='activa',
                )
            )
            db.session.add(
                Notificacion(
                    mensaje=(
                        f'Nuevo usuario registrado: {correo} '
                        f'({nombre_usuario}) - Plan Gratis'
                    ),
                    tipo='registro',
                    leido=False,
                )
            )
            db.session.commit()

            enviar_alerta_email(
                asunto='Nuevo usuario registrado en Gestión de Control',
                mensaje=(
                    'Se registró un nuevo usuario.\n\n'
                    f'Nombre: {nombre_usuario}\n'
                    f'Correo: {correo}\n'
                    f'Productor/Empresa: {nombre_productor}\n'
                    f'Teléfono: {telefono or "No indicado"}\n'
                    'Plan inicial: FREE'
                ),
            )

            login_user(usuario)
            flash('¡Cuenta creada! Bienvenido a Gestión de Control.', 'success')
            return redirect(url_for('dashboard.index'))

        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except IntegrityError:
            db.session.rollback()
            flash('El correo ya está registrado.', 'danger')
        except Exception:
            db.session.rollback()
            flash('No pudimos crear la cuenta. Intenta de nuevo.', 'danger')

    return render_template(
        'auth/register.html', datos=datos, plan_free=plan_free
    )


@bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        try:
            correo = validar_correo(request.form.get('correo'))
        except ErrorValidacion as e:
            flash(str(e), 'danger')
            return render_template('auth/recuperar.html'), 400

        if not _supera_limite(
            _SOLICITUDES_RECUPERACION, correo, MAX_RECUPERACIONES, VENTANA_RECUPERACION
        ):
            _registrar_intento(_SOLICITUDES_RECUPERACION, correo)
            db.session.add(
                Notificacion(
                    mensaje=f'Solicitud de recuperación de contraseña para {correo}',
                    tipo='recuperacion',
                    leido=False,
                )
            )
            db.session.commit()
            enviar_alerta_email(
                asunto='Solicitud de recuperación de contraseña',
                mensaje=(
                    'Un usuario solicitó restablecer su contraseña.\n\n'
                    f'Correo indicado: {correo}\n\n'
                    'El administrador debe contactarlo para restablecerla desde '
                    'Usuarios > Editar.'
                ),
            )

        # FUTURO: restablecimiento por token con proveedor de correo transaccional.
        flash(
            'Si el correo está registrado, el administrador te contactará para '
            'restablecer tu contraseña.',
            'info',
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/recuperar.html')


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
