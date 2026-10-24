from app.config.database import db
from app.models import Finca, Gasto, Inventario, Notificacion, Parcela, Produccion, Producto, RegistroAgricola


def test_aislamiento_entre_productores(app, client, fabrica, login):
    usuario1 = fabrica.productor(correo='p1@example.com', rol='cliente')
    usuario2 = fabrica.productor(correo='p2@example.com', rol='cliente')

    finca1 = fabrica.finca(usuario1.productor, 'Finca 1')
    finca2 = fabrica.finca(usuario2.productor, 'Finca 2')
    parcela1 = fabrica.parcela(finca1, 'Parcela 1')
    parcela2 = fabrica.parcela(finca2, 'Parcela 2')
    aplicador1 = fabrica.aplicador(usuario1.productor)
    aplicador2 = fabrica.aplicador(usuario2.productor)
    registro1 = fabrica.registro(parcela1, aplicador1)
    registro2 = fabrica.registro(parcela2, aplicador2)
    inventario2 = fabrica.inventario(finca2)
    gasto2 = fabrica.gasto(finca2)
    produccion2 = fabrica.produccion(parcela2)
    notificacion2 = fabrica.notificacion(usuario2.productor)
    notificacion_general = fabrica.notificacion(None, 'Aviso general')

    assert login('p1@example.com').status_code == 302

    rutas_get = [
        f'/fincas/ver/{finca2.id}',
        f'/fincas/editar/{finca2.id}',
        f'/parcelas/editar/{parcela2.id}',
        f'/registros/ver/{registro2.id}',
        f'/inventario/editar/{inventario2.id}',
        f'/gastos/editar/{gasto2.id}',
        f'/produccion/editar/{produccion2.id}',
        f'/productores/ver/{usuario2.productor.id}',
    ]
    for ruta in rutas_get:
        respuesta = client.get(ruta)
        assert respuesta.status_code == 404, ruta

    rutas_post = [
        f'/fincas/eliminar/{finca2.id}',
        f'/parcelas/eliminar/{parcela2.id}',
        f'/aplicadores/eliminar/{aplicador2.id}',
        f'/registros/eliminar/{registro2.id}',
        f'/inventario/eliminar/{inventario2.id}',
        f'/produccion/eliminar/{produccion2.id}',
        f'/notificaciones/marcar_leida/{notificacion2.id}',
    ]
    for ruta in rutas_post:
        respuesta = client.post(ruta)
        assert respuesta.status_code == 404, ruta

    # Ni las notificaciones generales ni los datos ajenos se alteran.
    assert client.post(f'/notificaciones/marcar_leida/{notificacion_general.id}').status_code == 404

    assert db.session.get(Finca, finca2.id) is not None
    assert db.session.get(Parcela, parcela2.id) is not None
    assert db.session.get(RegistroAgricola, registro2.id) is not None
    assert db.session.get(Inventario, inventario2.id) is not None
    assert db.session.get(Gasto, gasto2.id) is not None
    assert db.session.get(Produccion, produccion2.id) is not None
    assert db.session.get(Notificacion, notificacion2.id).leido is False
    assert db.session.get(Notificacion, notificacion_general.id).leido is False


def test_admin_solo_gestiona_notificaciones_generales(client, fabrica, login):
    admin = fabrica.productor(correo='admin@example.com', rol='administrador')
    otro = fabrica.productor(correo='otro@example.com', rol='administrador')
    general = fabrica.notificacion(None, 'Aviso general')
    ajena = fabrica.notificacion(otro.productor, 'Aviso de otro productor')

    assert login('admin@example.com').status_code == 302

    respuesta = client.get('/notificaciones/')
    assert respuesta.status_code == 200
    assert b'Aviso general' in respuesta.data
    assert b'Aviso de otro productor' not in respuesta.data

    assert client.post(f'/notificaciones/marcar_leida/{ajena.id}').status_code == 404
    assert client.post(f'/notificaciones/marcar_leida/{general.id}').status_code == 302
    assert db.session.get(Notificacion, general.id).leido is True
    assert db.session.get(Notificacion, ajena.id).leido is False


def test_catalogos_solo_admin(client, fabrica, login):
    from app.models import Cultivo

    admin = fabrica.productor(correo='admin-cat@example.com', rol='administrador')
    cliente = fabrica.productor(correo='cliente-cat@example.com', rol='cliente')

    cultivo = Cultivo.query.filter(Cultivo.nombre_cultivo == 'Yuca').first()
    assert cultivo is not None

    assert login('cliente-cat@example.com').status_code == 302
    assert client.post(f'/cultivos/eliminar/{cultivo.id}').status_code == 404
    assert db.session.get(Cultivo, cultivo.id) is not None

    client.post('/auth/logout')
    assert login('admin-cat@example.com').status_code == 302
    respuesta = client.post(f'/cultivos/eliminar/{cultivo.id}', follow_redirects=True)
    assert respuesta.status_code == 200
    assert b'Cultivo eliminado' in respuesta.data
    assert db.session.get(Cultivo, cultivo.id) is None


def test_no_elimina_catalogo_en_uso(client, fabrica, login):
    from app.models import Cultivo

    admin = fabrica.productor(correo='admin-uso@example.com', rol='administrador')
    finca = fabrica.finca(admin.productor)
    parcela = fabrica.parcela(finca)
    aplicador = fabrica.aplicador(admin.productor)
    registro = fabrica.registro(parcela, aplicador)
    cultivo = db.session.get(Cultivo, registro.id_cultivo)

    assert login('admin-uso@example.com').status_code == 302
    respuesta = client.post(
        f'/cultivos/eliminar/{cultivo.id}', follow_redirects=True
    )
    assert respuesta.status_code == 200
    assert 'en uso'.encode() in respuesta.data
    assert db.session.get(Cultivo, cultivo.id) is not None


def test_logout_solo_por_post(client, fabrica, login):
    fabrica.productor(correo='logout@example.com')
    assert login('logout@example.com').status_code == 302

    assert client.get('/auth/logout').status_code == 405
    respuesta = client.post('/auth/logout')
    assert respuesta.status_code == 302
    assert '/auth/login' in respuesta.headers['Location']

    # La sesión quedó cerrada: una ruta protegida redirige al login.
    assert client.get('/dashboard/').status_code == 302


def test_cabeceras_de_seguridad(client, fabrica, login):
    respuesta = client.get('/auth/login')
    assert respuesta.headers['X-Content-Type-Options'] == 'nosniff'
    assert respuesta.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert respuesta.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert respuesta.headers['Cache-Control'] == 'no-store'

    estatico = client.get('/static/vendor/bootstrap/css/bootstrap.min.css')
    assert estatico.status_code == 200
    assert 'no-store' not in estatico.headers.get('Cache-Control', '')
    assert 'max-age=604800' in estatico.headers.get('Cache-Control', '')

    fabrica.productor(correo='headers@example.com')
    login('headers@example.com')
    autenticada = client.get('/dashboard/')
    assert autenticada.headers['Cache-Control'] == 'no-store'


def test_ids_no_numericos_devuelven_404(client, fabrica, login):
    fabrica.productor(correo='ids@example.com')
    login('ids@example.com')

    assert client.get('/fincas/ver/abc').status_code == 404
    assert client.get('/parcelas/editar/abc').status_code == 404
    assert client.post('/registros/eliminar/abc').status_code == 404


def test_csrf_activo_rechaza_post_sin_token(app, client):
    app.config['WTF_CSRF_ENABLED'] = True
    respuesta = client.post(
        '/auth/login', data={'correo': 'x@example.com', 'password': 'x'}
    )
    assert respuesta.status_code == 400
    assert b'CSRF' in respuesta.data or b'csrf' in respuesta.data
