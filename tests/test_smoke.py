from app.models import Plan


def test_paginas_principales_cargan_sin_error(client, fabrica, login):
    usuario = fabrica.productor(correo='smoke@example.com', rol='administrador')
    finca = fabrica.finca(usuario.productor)
    parcela = fabrica.parcela(finca)
    aplicador = fabrica.aplicador(usuario.productor)
    fabrica.registro(parcela, aplicador)
    fabrica.inventario(finca)
    fabrica.gasto(finca)
    fabrica.produccion(parcela)
    fabrica.notificacion(None, 'Aviso general')

    assert login('smoke@example.com').status_code == 302

    rutas = [
        '/dashboard/',
        '/fincas/',
        '/fincas/crear',
        f'/fincas/ver/{finca.id}',
        f'/fincas/editar/{finca.id}',
        '/parcelas/',
        '/parcelas/crear',
        f'/parcelas/editar/{parcela.id}',
        '/cultivos/',
        '/cultivos/crear',
        '/productos/',
        '/productos/crear',
        '/aplicadores/',
        '/aplicadores/crear',
        '/registros/',
        '/registros/crear',
        '/reportes/',
        '/reportes/resumen',
        '/inventario/',
        '/inventario/crear',
        '/inventario/alertas',
        '/inventario/reportes',
        '/gastos/',
        '/gastos/crear',
        '/produccion/',
        '/produccion/crear',
        '/produccion/resumen',
        '/notificaciones/',
        '/notificaciones/contador',
        '/suscripciones/',
        '/suscripciones/upgrade',
        '/suscripciones/mi_plan',
        '/suscripciones/pagos_pendientes',
        '/gestion/usuarios/',
        '/gestion/usuarios/crear',
        '/productores/',
        '/productores/crear',
        f'/productores/ver/{usuario.productor.id}',
    ]
    for ruta in rutas:
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert b'Traceback' not in respuesta.data, ruta


def test_ruta_inexistente_muestra_404(client):
    respuesta = client.get('/esta-ruta-no-existe')
    assert respuesta.status_code == 404
    assert '404' in respuesta.get_data(as_text=True)


def test_health_no_depende_de_base_de_datos(client):
    respuesta = client.get('/health')
    assert respuesta.status_code == 200
    assert respuesta.get_data(as_text=True) == 'ok'
