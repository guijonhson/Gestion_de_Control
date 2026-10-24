from datetime import date

from app.models import Cultivo, Finca, Gasto


def test_finca_rechaza_nombre_demasiado_largo(client, fabrica, login):
    fabrica.productor(correo='form-finca@example.com')
    login('form-finca@example.com')

    respuesta = client.post(
        '/fincas/crear',
        data={'nombre_finca': 'x' * 101, 'area_total': '1'},
        follow_redirects=True,
    )
    assert 'no puede superar 100' in respuesta.get_data(as_text=True)
    assert Finca.query.count() == 0


def test_finca_rechaza_area_negativa(client, fabrica, login):
    fabrica.productor(correo='form-area@example.com')
    login('form-area@example.com')

    respuesta = client.post(
        '/fincas/crear',
        data={'nombre_finca': 'Finca', 'area_total': '-5'},
        follow_redirects=True,
    )
    assert 'no puede ser negativo' in respuesta.get_data(as_text=True)
    assert Finca.query.count() == 0


def test_parcela_rechaza_duracion_cero(client, fabrica, login):
    usuario = fabrica.productor(correo='form-parcela@example.com')
    finca = fabrica.finca(usuario.productor, 'Finca')
    login('form-parcela@example.com')

    respuesta = client.post(
        '/parcelas/crear',
        data={
            'id_finca': str(finca.id),
            'numero_parcela': 'P1',
            'area': '1',
            'tipo_uso': 'agricola',
            'duracion_cultivo': '0',
        },
        follow_redirects=True,
    )
    assert 'mayor que 0' in respuesta.get_data(as_text=True)
    assert len(finca.parcelas) == 0


def test_parcela_rechaza_finca_ajena(client, fabrica, login):
    usuario1 = fabrica.productor(correo='form-p1@example.com')
    usuario2 = fabrica.productor(correo='form-p2@example.com')
    fabrica.finca(usuario1.productor, 'Finca 1')
    finca2 = fabrica.finca(usuario2.productor, 'Finca 2')
    login('form-p1@example.com')

    respuesta = client.post(
        '/parcelas/crear',
        data={
            'id_finca': str(finca2.id),
            'numero_parcela': 'P1',
            'area': '1',
            'tipo_uso': 'agricola',
        },
    )
    assert respuesta.status_code == 404


def test_gasto_rechaza_monto_negativo(client, fabrica, login):
    usuario = fabrica.productor(correo='form-gasto@example.com')
    finca = fabrica.finca(usuario.productor)
    login('form-gasto@example.com')

    respuesta = client.post(
        '/gastos/crear',
        data={
            'tipo_gasto': 'semilla',
            'id_finca': str(finca.id),
            'monto': '-10',
            'fecha': date.today().isoformat(),
        },
        follow_redirects=True,
    )
    assert 'no puede ser negativo' in respuesta.get_data(as_text=True)
    assert Gasto.query.count() == 0


def test_inventario_rechaza_cantidad_negativa(client, fabrica, login):
    usuario = fabrica.productor(correo='form-inv@example.com')
    finca = fabrica.finca(usuario.productor)
    producto = fabrica.producto()
    login('form-inv@example.com')

    respuesta = client.post(
        '/inventario/crear',
        data={
            'id_producto': str(producto.id),
            'id_finca': str(finca.id),
            'cantidad': '-1',
            'unidad_medida': 'kg',
        },
        follow_redirects=True,
    )
    assert 'no puede ser negativo' in respuesta.get_data(as_text=True)


def test_produccion_rechaza_cantidad_cero(client, fabrica, login):
    usuario = fabrica.productor(correo='form-prod@example.com')
    finca = fabrica.finca(usuario.productor)
    parcela = fabrica.parcela(finca)
    login('form-prod@example.com')

    respuesta = client.post(
        '/produccion/crear',
        data={
            'id_cultivo': str(Cultivo.query.first().id),
            'id_parcela': str(parcela.id),
            'fecha_cosecha': date.today().isoformat(),
            'cantidad': '0',
            'unidad_medida': 'kg',
        },
        follow_redirects=True,
    )
    assert 'mayor que 0' in respuesta.get_data(as_text=True)


def test_registro_rechaza_selects_invalidos(client, fabrica, login):
    usuario = fabrica.productor(correo='form-reg@example.com')
    finca = fabrica.finca(usuario.productor)
    parcela = fabrica.parcela(finca)
    login('form-reg@example.com')

    respuesta = client.post(
        '/registros/crear',
        data={
            'fecha': date.today().isoformat(),
            'id_cultivo': '999999',
            'id_producto': '999999',
            'id_parcela': str(parcela.id),
            'id_aplicador': '999999',
            'tipo_control': 'Herbicida',
        },
        follow_redirects=True,
    )
    texto = respuesta.get_data(as_text=True)
    assert 'no existe' in texto


def test_creacion_valida_completa(client, fabrica, login, app):
    usuario = fabrica.productor(correo='form-ok@example.com')
    login('form-ok@example.com')

    respuesta = client.post(
        '/fincas/crear',
        data={
            'nombre_finca': '  Finca   Nueva  ',
            'ubicacion': '  Panamá  ',
            'area_total': '12.5',
            'rubro': '  ganadería  ',
        },
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    finca = Finca.query.first()
    assert finca.nombre_finca == 'Finca Nueva'
    assert finca.ubicacion == 'Panamá'
    assert finca.rubro == 'ganadería'
    assert finca.area_total == 12.5
