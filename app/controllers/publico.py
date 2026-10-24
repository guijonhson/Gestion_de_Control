import os

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    url_for,
)

from app.models import Plan

bp = Blueprint('publico', __name__)

# Datos de contacto tomados de setup_admin.py (no inventar otros).
CONTACTO = {
    'correo': 'agrodevpty@gmail.com',
    'telefono': '6944-2874',
    'pais': 'Panamá',
}


@bp.route('/health')
def health():
    """Comprobación de vida para monitores externos. No toca la base de datos."""
    return Response('ok', mimetype='text/plain')


@bp.route('/manifest.webmanifest')
def manifest():
    datos = {
        'name': 'AgroDev – Gestión de Control',
        'short_name': 'AgroDev',
        'description': (
            'Gestión agropecuaria para fincas, parcelas, inventario, gastos, '
            'producción y registros de aplicación.'
        ),
        'start_url': '/?source=pwa',
        'scope': '/',
        'display': 'standalone',
        'orientation': 'portrait-primary',
        'theme_color': '#2e7d32',
        'background_color': '#ffffff',
        'lang': 'es',
        'icons': [
            {
                'src': url_for('static', filename='img/icons/icon-192.png'),
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': url_for('static', filename='img/icons/icon-512.png'),
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': url_for('static', filename='img/icons/icon-maskable-512.png'),
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'maskable',
            },
        ],
    }
    respuesta = jsonify(datos)
    respuesta.mimetype = 'application/manifest+json'
    return respuesta


@bp.route('/sw.js')
def service_worker():
    ruta = os.path.join(current_app.static_folder, 'sw.js')
    with open(ruta, encoding='utf-8') as archivo:
        contenido = archivo.read()
    respuesta = Response(contenido, mimetype='application/javascript')
    respuesta.headers['Service-Worker-Allowed'] = '/'
    respuesta.headers['Cache-Control'] = 'no-cache'
    return respuesta


@bp.route('/offline')
def offline():
    return render_template('publico/offline.html')


@bp.route('/planes')
def planes():
    planes_activos = Plan.query.filter_by(activo=True).order_by(Plan.precio_mensual).all()
    return render_template(
        'publico/planes.html', planes=planes_activos, contacto=CONTACTO
    )


@bp.route('/legal/terminos')
def terminos():
    return render_template('publico/terminos.html', contacto=CONTACTO)


@bp.route('/legal/privacidad')
def privacidad():
    return render_template('publico/privacidad.html', contacto=CONTACTO)
