"""Validaciones reutilizables de formularios (sin acceso a base de datos)."""
import re
from datetime import datetime

from email_validator import EmailNotValidError, validate_email


class ErrorValidacion(ValueError):
    """Error de validación con un mensaje ya listo para mostrar al usuario."""


def limpiar_texto(valor):
    """Quita espacios al inicio/final y colapsa espacios repetidos."""
    if valor is None:
        return ''
    return ' '.join(str(valor).split())


def validar_correo(correo):
    """Normaliza y valida un correo. Devuelve el correo en minúsculas."""
    correo = limpiar_texto(correo).lower()
    if not correo:
        raise ErrorValidacion('El correo es obligatorio.')
    if len(correo) > 100:
        raise ErrorValidacion('El correo no puede superar 100 caracteres.')
    try:
        resultado = validate_email(correo, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ErrorValidacion('Escribe un correo válido.') from exc
    return resultado.normalized.lower()


def validar_telefono(telefono):
    """Valida un teléfono opcional (dígitos, espacios, +, -, paréntesis)."""
    telefono = limpiar_texto(telefono)
    if not telefono:
        return None
    if len(telefono) < 7 or len(telefono) > 20:
        raise ErrorValidacion('El teléfono debe tener entre 7 y 20 caracteres.')
    if not re.fullmatch(r'[0-9+\-()\s]+', telefono):
        raise ErrorValidacion(
            'El teléfono solo puede tener números, espacios, +, - y paréntesis.'
        )
    return telefono


def validar_password(password):
    """Mínimo 8 caracteres, al menos una letra y un número."""
    if not password:
        raise ErrorValidacion('La contraseña es obligatoria.')
    if len(password) < 8:
        raise ErrorValidacion('La contraseña debe tener al menos 8 caracteres.')
    if not re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', password):
        raise ErrorValidacion('La contraseña debe incluir al menos una letra.')
    if not re.search(r'\d', password):
        raise ErrorValidacion('La contraseña debe incluir al menos un número.')
    if len(password) > 128:
        raise ErrorValidacion('La contraseña no puede superar 128 caracteres.')
    return password


def validar_largo(valor, maximo, etiqueta, obligatorio=False):
    """Valida longitud y obligatoriedad. Devuelve el texto limpio o None."""
    valor = limpiar_texto(valor)
    if obligatorio and not valor:
        raise ErrorValidacion(f'{etiqueta} es obligatorio.')
    if len(valor) > maximo:
        raise ErrorValidacion(f'{etiqueta} no puede superar {maximo} caracteres.')
    return valor or None


def a_entero(valor, etiqueta, minimo=None, maximo=None, obligatorio=True):
    """Convierte a entero con mensajes claros. Vacío -> None si es opcional."""
    texto = limpiar_texto(valor)
    if not texto:
        if obligatorio:
            raise ErrorValidacion(f'{etiqueta} es obligatorio.')
        return None
    try:
        numero = int(texto)
    except (TypeError, ValueError) as exc:
        raise ErrorValidacion(f'{etiqueta} debe ser un número entero.') from exc
    if minimo is not None and numero < minimo:
        raise ErrorValidacion(f'{etiqueta} debe ser mayor o igual que {minimo}.')
    if maximo is not None and numero > maximo:
        raise ErrorValidacion(f'{etiqueta} debe ser menor o igual que {maximo}.')
    return numero


def a_decimal(valor, etiqueta, minimo=None, maximo=None, obligatorio=False):
    """Convierte a decimal con mensajes claros. Vacío -> None si es opcional."""
    texto = limpiar_texto(valor)
    if not texto:
        if obligatorio:
            raise ErrorValidacion(f'{etiqueta} es obligatorio.')
        return None
    try:
        numero = float(texto)
    except (TypeError, ValueError) as exc:
        raise ErrorValidacion(f'{etiqueta} debe ser un número.') from exc
    if numero != numero or numero in (float('inf'), float('-inf')):
        raise ErrorValidacion(f'{etiqueta} debe ser un número válido.')
    if minimo is not None and numero < minimo:
        raise ErrorValidacion(f'{etiqueta} no puede ser negativo.')
    if maximo is not None and numero > maximo:
        raise ErrorValidacion(f'{etiqueta} debe ser menor o igual que {maximo}.')
    return numero


def a_fecha(valor, etiqueta, obligatoria=False):
    """Convierte un valor YYYY-MM-DD en date, con mensaje claro."""
    texto = limpiar_texto(valor)
    if not texto:
        if obligatoria:
            raise ErrorValidacion(f'{etiqueta} es obligatoria.')
        return None
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError) as exc:
        raise ErrorValidacion(f'{etiqueta} no es una fecha válida.') from exc
