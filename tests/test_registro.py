from datetime import datetime

from app.config.database import db
from app.controllers import auth as auth_controller
from app.models import Notificacion, Productor, Suscripcion, Usuario


def datos_registro(**cambios):
    datos = {
        'nombre': 'Productor Nuevo',
        'telefono': '6000-0000',
        'correo': 'nuevo@example.com',
        'nombre_usuario': 'nuevo',
        'password': 'Clave1234',
        'password_confirmacion': 'Clave1234',
        'acepto_terminos': '1',
    }
    datos.update(cambios)
    return datos


def test_registro_valido_crea_cuenta_y_sesion(app, client):
    respuesta = client.post(
        '/auth/register', data=datos_registro(), follow_redirects=False
    )
    assert respuesta.status_code == 302
    assert '/dashboard/' in respuesta.headers['Location']

    usuario = Usuario.query.filter_by(correo='nuevo@example.com').first()
    assert usuario is not None
    assert usuario.rol == 'administrador'  # primer usuario
    assert usuario.check_password('Clave1234')
    assert usuario.fecha_aceptacion_terminos is not None
    assert usuario.productor.nombre == 'Productor Nuevo'
    assert usuario.productor.suscripciones[0].plan.nombre_plan == 'FREE'
    assert Notificacion.query.count() == 1

    dashboard = client.get('/dashboard/')
    assert dashboard.status_code == 200
    assert b'Primeros pasos' in dashboard.data


def test_registro_exige_terminos(client):
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(acepto_terminos=''),
        follow_redirects=True,
    )
    texto = respuesta.get_data(as_text=True)
    assert 'Debes aceptar' in texto
    assert Usuario.query.count() == 0


def test_registro_valida_password(client):
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(password='corta', password_confirmacion='corta'),
        follow_redirects=True,
    )
    assert 'al menos 8 caracteres' in respuesta.get_data(as_text=True)
    assert Usuario.query.count() == 0


def test_registro_valida_confirmacion(client):
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(password_confirmacion='OtraClave123'),
        follow_redirects=True,
    )
    assert 'no coinciden' in respuesta.get_data(as_text=True)


def test_registro_valida_correo(client):
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(correo='correo-invalido'),
        follow_redirects=True,
    )
    assert 'correo válido' in respuesta.get_data(as_text=True)


def test_registro_valida_telefono(client):
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(telefono='abc'),
        follow_redirects=True,
    )
    assert 'teléfono' in respuesta.get_data(as_text=True).lower()


def test_registro_duplicado_ignora_mayusculas(app, client, fabrica):
    fabrica.productor(correo='duplicado@example.com')
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(correo='DUPLICADO@example.com'),
        follow_redirects=True,
    )
    assert 'ya está registrado' in respuesta.get_data(as_text=True)
    assert Usuario.query.filter_by(correo='duplicado@example.com').count() == 1


def test_segundo_usuario_es_cliente(app, client, fabrica):
    fabrica.productor(correo='primero@example.com')
    respuesta = client.post(
        '/auth/register',
        data=datos_registro(correo='segundo@example.com'),
        follow_redirects=False,
    )
    assert respuesta.status_code == 302
    usuario = Usuario.query.filter_by(correo='segundo@example.com').first()
    assert usuario.rol == 'cliente'
    assert usuario.fecha_aceptacion_terminos is not None


def test_login_normaliza_correo_y_mantiene_sesion(client, fabrica):
    fabrica.productor(correo='login@example.com')
    respuesta = client.post(
        '/auth/login',
        data={
            'correo': '  LOGIN@EXAMPLE.COM ',
            'password': 'Clave1234',
            'remember': '1',
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 302
    assert '/dashboard/' in respuesta.headers['Location']
    cookies = respuesta.headers.getlist('Set-Cookie')
    assert any('remember_token=' in cookie for cookie in cookies)


def test_login_usuario_inactivo(app, client, fabrica):
    usuario = fabrica.productor(correo='inactivo@example.com')
    usuario.activo = False
    db.session.commit()

    respuesta = client.post(
        '/auth/login',
        data={'correo': 'inactivo@example.com', 'password': 'Clave1234'},
        follow_redirects=True,
    )
    assert 'inactivo' in respuesta.get_data(as_text=True).lower()


def test_login_limita_intentos(client, app):
    auth_controller._INTENTOS_LOGIN.clear()
    for _ in range(10):
        respuesta = client.post(
            '/auth/login',
            data={'correo': 'nadie@example.com', 'password': 'incorrecta'},
        )
        assert respuesta.status_code == 200

    respuesta = client.post(
        '/auth/login',
        data={'correo': 'nadie@example.com', 'password': 'incorrecta'},
    )
    assert respuesta.status_code == 429
    assert 'Demasiados intentos' in respuesta.get_data(as_text=True)
    auth_controller._INTENTOS_LOGIN.clear()


def test_recuperacion_es_neutral_y_limita_solicitudes(app, client, fabrica):
    auth_controller._SOLICITUDES_RECUPERACION.clear()
    fabrica.productor(correo='recuperar@example.com')

    for correo in [
        'recuperar@example.com',
        'no-existe@example.com',
        'recuperar@example.com',
    ]:
        respuesta = client.post(
            '/auth/recuperar', data={'correo': correo}, follow_redirects=True
        )
        assert respuesta.status_code == 200
        assert 'Si el correo está registrado' in respuesta.get_data(as_text=True)

    # Ya hay 2 solicitudes para ese correo; la tercera se acepta y la cuarta se ignora.
    client.post('/auth/recuperar', data={'correo': 'recuperar@example.com'})
    assert Notificacion.query.count() == 4
    client.post('/auth/recuperar', data={'correo': 'recuperar@example.com'})
    assert Notificacion.query.count() == 4


def test_migracion_agrega_fecha_aceptacion(app):
    from app.utils.migraciones import COLUMNAS_NUEVAS

    assert ('usuario', 'fecha_aceptacion_terminos', 'TIMESTAMP') in COLUMNAS_NUEVAS
