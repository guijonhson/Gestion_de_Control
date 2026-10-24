import json
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.config.database import db
from app.models import Cultivo, Finca, Parcela, ParcelaAgricola, ParcelaGanadera
from app.utils.catalogos_agro import (
    ADVERTENCIAS_PASTO,
    DENSIDAD_REFERENCIAL,
    PASTOS,
    RAZAS_SUGERIDAS,
    TIPOS_ANIMAL,
)
from app.utils.permisos import obtener_parcela
from app.utils.suscripcion import verificar_limite
from app.utils.validaciones import (
    ErrorValidacion,
    a_decimal,
    a_entero,
    limpiar_texto,
    validar_largo,
)

bp = Blueprint('parcelas', __name__, url_prefix='/parcelas')


def _leer_siembra(form):
    fecha_txt = limpiar_texto(form.get('fecha_inicio_siembra'))
    duracion_txt = limpiar_texto(form.get('duracion_cultivo'))

    fecha = None
    if fecha_txt:
        try:
            fecha = datetime.strptime(fecha_txt, '%Y-%m-%d').date()
        except ValueError as exc:
            raise ErrorValidacion('La fecha de inicio de siembra no es válida.') from exc

    duracion = None
    if duracion_txt:
        try:
            duracion = int(duracion_txt)
        except ValueError as exc:
            raise ErrorValidacion(
                'La duración del cultivo debe ser un número entero de días.'
            ) from exc
        if duracion <= 0:
            raise ErrorValidacion('La duración del cultivo debe ser mayor que 0 días.')

    return fecha, duracion


def _contexto_formulario():
    return {
        'cultivos': Cultivo.query.order_by(Cultivo.nombre_cultivo).all(),
        'pastos': PASTOS,
        'tipos_animal': TIPOS_ANIMAL,
        'advertencias_pasto': ADVERTENCIAS_PASTO,
        'densidades': DENSIDAD_REFERENCIAL,
        'razas_json': json.dumps(RAZAS_SUGERIDAS, ensure_ascii=False),
    }


def _finca_del_usuario(id_finca):
    finca = Finca.query.filter_by(
        id=id_finca, id_productor=current_user.id_productor
    ).first()
    if not finca:
        abort(404)
    return finca


def _datos_agricola():
    id_cultivo = a_entero(
        request.form.get('id_cultivo'), 'El cultivo', minimo=1, obligatorio=False
    )
    if id_cultivo and not Cultivo.query.get(id_cultivo):
        raise ErrorValidacion('El cultivo seleccionado no existe.')
    densidad = a_decimal(
        request.form.get('densidad_plantas_ha'),
        'La densidad de plantas',
        minimo=0,
    )
    return {
        'id_cultivo': id_cultivo,
        'densidad_plantas_ha': densidad,
    }, id_cultivo


def _datos_ganaderos():
    pasto = limpiar_texto(request.form.get('pasto'))
    if pasto == 'Otro':
        pasto = limpiar_texto(request.form.get('pasto_otro'))
    validar_largo(pasto, 100, 'El pasto')

    tipo_animal = limpiar_texto(request.form.get('tipo_animal'))
    validar_largo(tipo_animal, 50, 'El tipo de animal')
    if tipo_animal and tipo_animal not in TIPOS_ANIMAL:
        raise ErrorValidacion('El tipo de animal seleccionado no es válido.')

    raza = limpiar_texto(request.form.get('raza'))
    validar_largo(raza, 100, 'La raza')
    cantidad = a_entero(
        request.form.get('cantidad_animales'),
        'La cantidad de animales',
        minimo=0,
        obligatorio=False,
    )
    return {
        'pasto': pasto or None,
        'tipo_animal': tipo_animal or None,
        'raza': raza or None,
        'cantidad_animales': cantidad,
    }


def _guardar_detalle(parcela):
    if parcela.tipo_uso == 'ganadera':
        datos = _datos_ganaderos()
        if parcela.ganadera is None:
            db.session.add(ParcelaGanadera(id_parcela=parcela.id, **datos))
        else:
            for campo, valor in datos.items():
                setattr(parcela.ganadera, campo, valor)
    else:
        datos, id_cultivo = _datos_agricola()
        if parcela.agricola is None:
            db.session.add(ParcelaAgricola(id_parcela=parcela.id, **datos))
        else:
            for campo, valor in datos.items():
                setattr(parcela.agricola, campo, valor)
        cultivo = Cultivo.query.get(id_cultivo) if id_cultivo else None
        parcela.cultivo_actual = cultivo.nombre_cultivo if cultivo else None


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
        try:
            id_finca = a_entero(request.form.get('id_finca'), 'La finca', minimo=1)
            finca = _finca_del_usuario(id_finca)

            numero_parcela = limpiar_texto(request.form.get('numero_parcela'))
            validar_largo(numero_parcela, 50, 'El número o nombre de la parcela', obligatorio=True)

            area = a_decimal(request.form.get('area'), 'El área', minimo=0)

            tipo_uso = request.form.get('tipo_uso', 'agricola')
            if tipo_uso not in ('agricola', 'ganadera'):
                tipo_uso = 'agricola'

            fecha_siembra, duracion = _leer_siembra(request.form)

            parcela = Parcela(
                id_finca=finca.id,
                numero_parcela=numero_parcela,
                area=area,
                fecha_inicio_siembra=fecha_siembra,
                duracion_cultivo=duracion,
                tipo_uso=tipo_uso,
            )
            db.session.add(parcela)
            db.session.flush()
            _guardar_detalle(parcela)
            db.session.commit()

            flash('Parcela creada exitosamente.', 'success')
            return redirect(url_for('parcelas.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('parcelas/crear.html', fincas=fincas, **_contexto_formulario())


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    parcela = obtener_parcela(id)
    fincas = Finca.query.filter_by(id_productor=current_user.id_productor).all()

    if request.method == 'POST':
        try:
            fecha_siembra, duracion = _leer_siembra(request.form)

            parcela.id_finca = _finca_del_usuario(
                a_entero(request.form.get('id_finca'), 'La finca', minimo=1)
            ).id
            parcela.numero_parcela = limpiar_texto(request.form.get('numero_parcela'))
            validar_largo(
                parcela.numero_parcela,
                50,
                'El número o nombre de la parcela',
                obligatorio=True,
            )
            parcela.area = a_decimal(request.form.get('area'), 'El área', minimo=0)
            parcela.fecha_inicio_siembra = fecha_siembra
            parcela.duracion_cultivo = duracion

            nuevo_tipo = request.form.get('tipo_uso', parcela.tipo_uso)
            if nuevo_tipo not in ('agricola', 'ganadera'):
                nuevo_tipo = parcela.tipo_uso

            if nuevo_tipo != parcela.tipo_uso:
                if parcela.agricola:
                    db.session.delete(parcela.agricola)
                if parcela.ganadera:
                    db.session.delete(parcela.ganadera)
                parcela.tipo_uso = nuevo_tipo
                if parcela.tipo_uso == 'ganadera':
                    parcela.cultivo_actual = None
                db.session.flush()

            _guardar_detalle(parcela)
            db.session.commit()

            flash('Parcela actualizada exitosamente.', 'success')
            return redirect(url_for('parcelas.listar'))
        except ErrorValidacion as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template(
        'parcelas/editar.html',
        parcela=parcela,
        fincas=fincas,
        **_contexto_formulario(),
    )


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    parcela = obtener_parcela(id)
    db.session.delete(parcela)
    db.session.commit()
    flash('Parcela eliminada exitosamente.', 'success')
    return redirect(url_for('parcelas.listar'))
