from pathlib import Path

from app.utils.planes import nombre_plan_visible

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLAS = RAIZ / 'app' / 'templates'


def test_nombre_plan_visible_sin_cambiar_valores():
    assert nombre_plan_visible('FREE') == 'Gratis'
    assert nombre_plan_visible('BÁSICO') == 'Básico'
    assert nombre_plan_visible('BASICO') == 'Básico'
    assert nombre_plan_visible('B\ufffdSICO') == 'Básico'
    assert nombre_plan_visible('PRO') == 'Profesional'
    assert nombre_plan_visible('EMPRESARIAL') == 'Empresarial'


def test_planes_publicos_muestran_precios_de_la_base(client):
    respuesta = client.get('/planes')
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert 'Gratis' in texto
    assert 'Básico' in texto
    assert 'Profesional' in texto
    assert 'Empresarial' in texto
    assert '$10.00' in texto
    assert '$25.00' in texto
    assert '$50.00' in texto
    assert '>FREE<' not in texto
    assert '>PRO<' not in texto


def test_login_tiene_atributos_y_recuperacion(client):
    texto = client.get('/auth/login').get_data(as_text=True)
    assert 'autocomplete="username"' not in texto
    assert 'autocomplete="email"' in texto
    assert 'autocomplete="current-password"' in texto
    assert 'maxlength="100"' in texto
    assert 'Mantener sesión iniciada' in texto
    assert '¿Olvidaste tu contraseña?' in texto
    assert 'data-toggle-password' in texto


def test_registro_tiene_terminos_plan_y_limites(client):
    texto = client.get('/auth/register').get_data(as_text=True)
    assert 'Acepto los' in texto
    assert '/legal/terminos' in texto
    assert '/legal/privacidad' in texto
    assert 'Plan Gratis' in texto
    assert 'minlength="8"' in texto
    assert 'maxlength="100"' in texto
    assert 'name="acepto_terminos"' in texto


def test_paginas_publicas_sin_sesion(client):
    for ruta in ['/planes', '/legal/terminos', '/legal/privacidad', '/offline']:
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert 'AgroDev' in respuesta.get_data(as_text=True)


def test_legal_es_borrador_y_no_inventa_datos(client):
    terminos = client.get('/legal/terminos').get_data(as_text=True)
    privacidad = client.get('/legal/privacidad').get_data(as_text=True)
    assert 'Borrador pendiente de revisión legal' in terminos
    assert 'Borrador pendiente de revisión legal' in privacidad
    assert 'agrodevpty@gmail.com' in terminos
    assert '6944-2874' in terminos
    assert 'David' not in terminos
    assert 'Horario' not in terminos


def test_estados_vacios_en_formularios(client, fabrica, login):
    fabrica.productor(correo='vacio@example.com')
    login('vacio@example.com')

    casos = {
        '/parcelas/crear': 'Primero debes crear una finca',
        '/gastos/crear': 'Primero debes crear una finca',
        '/registros/crear': 'Antes de registrar una aplicación',
        '/inventario/crear': 'Para agregar inventario',
        '/produccion/crear': 'Para registrar una cosecha',
    }
    for ruta, mensaje in casos.items():
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert mensaje in respuesta.get_data(as_text=True), ruta
        assert 'disabled' in respuesta.get_data(as_text=True), ruta


def test_onboarding_y_pasos_completados(client, fabrica, login):
    usuario = fabrica.productor(correo='onboarding@example.com')
    login('onboarding@example.com')

    dashboard = client.get('/dashboard/').get_data(as_text=True)
    assert 'Primeros pasos' in dashboard
    assert 'Crear tu primera finca' in dashboard
    assert 'Crear una parcela' in dashboard

    fabrica.finca(usuario.productor, 'Finca')
    dashboard = client.get('/dashboard/').get_data(as_text=True)
    assert 'Crear tu primera finca' in dashboard
    assert 'Hecho' in dashboard


def test_no_queda_texto_basura_en_plantillas():
    encontrados = []
    for archivo in PLANTILLAS.rglob('*.html'):
        contenido = archivo.read_text(encoding='utf-8')
        if 'successfully downloaded text file' in contenido:
            encontrados.append(str(archivo.relative_to(RAIZ)))
    assert encontrados == []


def test_no_quedan_cdn_externos_en_plantillas():
    externos = []
    for archivo in PLANTILLAS.rglob('*.html'):
        contenido = archivo.read_text(encoding='utf-8')
        if 'cdn.jsdelivr.net' in contenido or 'cdnjs.cloudflare.com' in contenido:
            externos.append(str(archivo.relative_to(RAIZ)))
    assert externos == []


def test_navbar_usa_formulario_post_para_salir(client, fabrica, login):
    fabrica.productor(correo='nav@example.com')
    login('nav@example.com')
    texto = client.get('/dashboard/').get_data(as_text=True)
    assert 'action="/auth/logout"' in texto
    assert 'name="csrf_token"' in texto


def test_paginas_protegidas_redirigen_al_login(client):
    for ruta in ['/dashboard/', '/fincas/', '/inventario/', '/gestion/usuarios/']:
        respuesta = client.get(ruta)
        assert respuesta.status_code == 302
        assert '/auth/login' in respuesta.headers['Location']
