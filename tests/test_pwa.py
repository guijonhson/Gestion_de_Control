import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_manifest_es_valido_y_tiene_iconos(client):
    respuesta = client.get('/manifest.webmanifest')
    assert respuesta.status_code == 200
    assert respuesta.mimetype == 'application/manifest+json'
    datos = json.loads(respuesta.get_data(as_text=True))
    assert datos['name'].startswith('AgroDev')
    assert datos['display'] == 'standalone'
    assert datos['start_url'] == '/?source=pwa'
    assert datos['theme_color'] == '#2e7d32'
    assert datos['lang'] == 'es'
    tamanos = {icono['sizes'] for icono in datos['icons']}
    assert {'192x192', '512x512'} <= tamanos
    assert any(icono['purpose'] == 'maskable' for icono in datos['icons'])


def test_iconos_existen_y_son_png():
    for nombre in [
        'icon-192.png',
        'icon-512.png',
        'icon-maskable-512.png',
        'apple-touch-icon-180.png',
    ]:
        ruta = RAIZ / 'app' / 'static' / 'img' / 'icons' / nombre
        assert ruta.exists(), nombre
        assert ruta.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', nombre


def test_service_worker_se_sirve_desde_la_raiz(client):
    respuesta = client.get('/sw.js')
    assert respuesta.status_code == 200
    assert respuesta.mimetype == 'application/javascript'
    assert respuesta.headers['Service-Worker-Allowed'] == '/'
    assert respuesta.headers['Cache-Control'] == 'no-cache'
    texto = respuesta.get_data(as_text=True)
    assert "CACHE_VERSION" in texto
    assert "PRECACHE_URLS" in texto
    assert "'SKIP_WAITING'" in texto
    assert "url.pathname.startsWith('/static/')" in texto


def test_service_worker_no_cachea_html_autenticado(client):
    texto = client.get('/sw.js').get_data(as_text=True)
    # Las navegaciones van a red y solo caen a /offline; no se guardan.
    assert "event.request.mode === 'navigate'" in texto
    assert "redPrimero(event.request)" in texto
    assert "cache.put(event.request" not in texto


def test_pagina_offline(client):
    respuesta = client.get('/offline')
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert 'Sin conexión' in texto
    assert 'Reintentar' in texto


def test_plantillas_incluyen_manifest_e_instalacion(client):
    texto = client.get('/auth/login').get_data(as_text=True)
    assert 'rel="manifest"' in texto
    assert 'apple-touch-icon' in texto
    assert 'btnInstalarApp' in texto
    assert 'pwaUpdate' in texto
    assert "serviceWorker.register('/sw.js'" in texto


def test_configuracion_de_sesion_y_estaticos(app):
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['WTF_CSRF_TIME_LIMIT'] is None
    assert app.config['SEND_FILE_MAX_AGE_DEFAULT'] == 60 * 60 * 24 * 7
