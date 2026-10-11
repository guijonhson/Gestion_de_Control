from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.config.database import db
from app.models import Parcela, Finca, ParcelaAgricola, ParcelaGanadera, Cultivo
from app.utils.suscripcion import verificar_limite
from app.utils.catalogos_agro import (
    PASTOS,
    TIPOS_ANIMAL,
    RAZAS_SUGERIDAS,
    ADVERTENCIAS_PASTO,
    DENSIDAD_REFERENCIAL,
)
from datetime import datetime
import json

bp = Blueprint('parcelas', __name__, url_prefix='/parcelas')


def _leer_siembra(form):
    fecha_txt = (form.get('fecha_inicio_siembra') or '').strip()
    duracion_txt = (form.get('duracion_cultivo') or '').strip()

    fecha = None
    if fecha_txt:
        try:
            fecha = datetime.strptime(fecha_txt, '%Y-%m-%d').date()
        except ValueError:
            return None, None, 'La fecha de inicio de siembra no es válida.'

    duracion = None
    if duracion_txt:
        try:
            duracion = int(duracion_txt)
        except ValueError:
            return None, None, 'La duración del cultivo debe ser un número entero de días.'
        if duracion <= 0:
            return None, None, 'La duración del cultivo debe ser mayor que 0 días.'

    return fecha, duracion, None


def _contexto_formulario():
    """Datos de catálogo compartidos por crear y editar."""
    return {
        'cultivos': Cultivo.query.order_by(Cultivo.nombre_cultivo).all(),
        'pastos': PASTOS,
        'tipos_animal': TIPOS_ANIMAL,
        'advertencias_pasto': ADVERTENCIAS_PASTO,
        'densidades': DENSIDAD_REFERENCIAL,
        'razas_json': json.dumps(RAZAS_SUGERIDAS, ensure_ascii=False),
    }


def _datos_agricola():
    id_cultivo = request.form.get('id_cultivo')
    densidad = request.form.get('densidad_plantas_ha')
    return {
        'id_cultivo': int(id_cultivo) if id_cultivo else None,
        'densidad_plantas_ha': float(densidad) if densidad else None,
    }


def _datos_ganaderos():
    pasto = request.form.get('pasto')
    if pasto == 'Otro':
        pasto = request.form.get('pasto_otro') or None
    cantidad = request.form.get('cantidad_animales')
    return {
        'pasto': pasto or None,
        'tipo_animal': request.form.get('tipo_animal') or None,
        'raza': request.form.get('raza') or None,
        'cantidad_animales': int(cantidad) if cantidad else None,
    }


def _guardar_detalle(parcela):
    """Crea o actualiza el sub-registro segun el tipo de uso."""
    if parcela.tipo_uso == 'ganadera':
        datos = _datos_ganaderos()
        if parcela.ganadera is None:
            db.session.add(ParcelaGanadera(id_parcela=parcela.id, **datos))
        else:
            for campo, valor in datos.items():
                setattr(parcela.ganadera, campo, valor)
    else:
        datos = _datos_agricola()
        if parcela.agricola is None:
            db.session.add(ParcelaAgricola(id_parcela=parcela.id, **datos))
        else:
            for campo, valor in datos.items():
                setattr(parcela.agricola, campo, valor)
        cultivo = Cultivo.query.get(datos['id_cultivo']) if datos['id_cultivo'] else None
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
        id_finca = request.form.get('id_finca')
        numero_parcela = request.form.get('numero_parcela')
        area = request.form.get('area')
        tipo_uso = request.form.get('tipo_uso', 'agricola')
        if tipo_uso not in ('agricola', 'ganadera'):
            tipo_uso = 'agricola'
        
        fecha_siembra, duracion, error = _leer_siembra(request.form)
        if error:
            flash(error, 'danger')
            return render_template('parcelas/crear.html', fincas=fincas, **_contexto_formulario())
        
        parcela = Parcela(
            id_finca=int(id_finca),
            numero_parcela=numero_parcela,
            area=float(area) if area else None,
            fecha_inicio_siembra=fecha_siembra,
            duracion_cultivo=duracion,
            tipo_uso=tipo_uso
        )
        db.session.add(parcela)
        db.session.flush()
        _guardar_detalle(parcela)
        db.session.commit()
        
        flash('Parcela creada exitosamente.', 'success')
        return redirect(url_for('parcelas.listar'))
    
    return render_template('parcelas/crear.html', fincas=fincas, **_contexto_formulario())


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
        fecha_siembra, duracion, error = _leer_siembra(request.form)
        if error:
            flash(error, 'danger')
            return render_template('parcelas/editar.html', parcela=parcela, fincas=fincas, **_contexto_formulario())
        
        parcela.id_finca = int(request.form.get('id_finca'))
        parcela.numero_parcela = request.form.get('numero_parcela')
        area = request.form.get('area')
        parcela.area = float(area) if area else None
        parcela.fecha_inicio_siembra = fecha_siembra
        parcela.duracion_cultivo = duracion
        
        nuevo_tipo = request.form.get('tipo_uso', parcela.tipo_uso)
        if nuevo_tipo not in ('agricola', 'ganadera'):
            nuevo_tipo = parcela.tipo_uso
        
        # Si cambia el tipo de uso, se descarta el detalle anterior
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
    
    return render_template('parcelas/editar.html', parcela=parcela, fincas=fincas, **_contexto_formulario())


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
