"""
Comprobaciones de pertenencia de datos.

Todas las funciones devuelven el objeto solo si pertenece al productor del
usuario actual. El administrador puede acceder a todo. Si el objeto no existe
o no pertenece al productor se responde 404 (no 403) para no revelar que existe.
"""
from flask import abort
from flask_login import current_user

from app.models import (
    Aplicador,
    Finca,
    Gasto,
    Inventario,
    Notificacion,
    Parcela,
    Produccion,
    Productor,
    RegistroAgricola,
)


def es_admin():
    return getattr(current_user, 'rol', None) == 'administrador'


def _mismo_productor(id_productor):
    return es_admin() or id_productor == current_user.id_productor


def obtener_finca(id_finca):
    finca = Finca.query.get_or_404(id_finca)
    if not _mismo_productor(finca.id_productor):
        abort(404)
    return finca


def obtener_parcela(id_parcela):
    parcela = Parcela.query.get_or_404(id_parcela)
    if not parcela.finca or not _mismo_productor(parcela.finca.id_productor):
        abort(404)
    return parcela


def obtener_registro(id_registro):
    registro = RegistroAgricola.query.get_or_404(id_registro)
    if not registro.parcela or not registro.parcela.finca:
        abort(404)
    if not _mismo_productor(registro.parcela.finca.id_productor):
        abort(404)
    return registro


def obtener_produccion(id_produccion):
    produccion = Produccion.query.get_or_404(id_produccion)
    if not produccion.parcela or not produccion.parcela.finca:
        abort(404)
    if not _mismo_productor(produccion.parcela.finca.id_productor):
        abort(404)
    return produccion


def obtener_inventario(id_inventario):
    inventario = Inventario.query.get_or_404(id_inventario)
    if not inventario.finca or not _mismo_productor(inventario.finca.id_productor):
        abort(404)
    return inventario


def obtener_gasto(id_gasto):
    gasto = Gasto.query.get_or_404(id_gasto)
    if not gasto.finca or not _mismo_productor(gasto.finca.id_productor):
        abort(404)
    return gasto


def obtener_aplicador(id_aplicador):
    aplicador = Aplicador.query.get_or_404(id_aplicador)
    if not _mismo_productor(aplicador.id_productor):
        abort(404)
    return aplicador


def obtener_productor(id_productor):
    productor = Productor.query.get_or_404(id_productor)
    if not _mismo_productor(productor.id):
        abort(404)
    return productor


def obtener_notificacion(id_notificacion):
    notificacion = Notificacion.query.get_or_404(id_notificacion)
    if es_admin():
        # El administrador solo gestiona las notificaciones generales.
        if notificacion.id_productor is not None:
            abort(404)
    elif notificacion.id_productor != current_user.id_productor:
        abort(404)
    return notificacion


def exigir_admin():
    """Aborta con 404 si el usuario actual no es administrador."""
    if not es_admin():
        abort(404)
