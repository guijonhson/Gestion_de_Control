import os
from datetime import date

import pytest

# Debe definirse antes de importar la aplicación.
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('SECRET_KEY', 'clave-solo-para-pruebas')

from app import _init_catalogs, create_app  # noqa: E402
from app.config.database import db  # noqa: E402
from app.models import (  # noqa: E402
    Aplicador,
    Cultivo,
    Finca,
    Gasto,
    Inventario,
    Notificacion,
    Parcela,
    Plan,
    Produccion,
    Productor,
    RegistroAgricola,
    Suscripcion,
    Usuario,
)


@pytest.fixture()
def app():
    aplicacion = create_app()
    aplicacion.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SERVER_NAME='localhost',
    )

    with aplicacion.app_context():
        db.drop_all()
        db.create_all()
        _init_catalogs()
        yield aplicacion
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


class Fabrica:
    """Crea productores, usuarios y datos de prueba sin pasar por HTTP."""

    def __init__(self, app):
        self.app = app
        self.contador = 0

    def _siguiente(self, prefijo):
        self.contador += 1
        return f'{prefijo}{self.contador}'

    def plan(self, nombre='FREE'):
        plan = Plan.query.filter_by(nombre_plan=nombre).first()
        if not plan:
            plan = Plan.query.first()
        assert plan is not None, 'No hay planes inicializados'
        return plan

    def productor(self, nombre=None, correo=None, password='Clave1234',
                  rol='administrador', plan='FREE'):
        nombre = nombre or self._siguiente('Productor ')
        correo = correo or f'{self._siguiente("productor")}@example.com'
        productor = Productor(nombre=nombre, telefono='6000-0000', correo=correo)
        db.session.add(productor)
        db.session.flush()

        usuario = Usuario(
            id_productor=productor.id,
            nombre_usuario=self._siguiente('usuario'),
            correo=correo,
            rol=rol,
            activo=True,
            fecha_registro=date.today(),
        )
        usuario.set_password(password)
        db.session.add(usuario)

        db.session.add(
            Suscripcion(
                id_productor=productor.id,
                id_plan=self.plan(plan).id,
                fecha_inicio=date.today(),
                fecha_fin=None,
                estado='activa',
            )
        )
        db.session.commit()
        return usuario

    def finca(self, productor, nombre=None):
        finca = Finca(
            id_productor=productor.id,
            nombre_finca=nombre or self._siguiente('Finca '),
            ubicacion='Panamá',
            area_total=10,
            rubro='agricultura',
        )
        db.session.add(finca)
        db.session.commit()
        return finca

    def parcela(self, finca, numero=None):
        parcela = Parcela(
            id_finca=finca.id,
            numero_parcela=numero or self._siguiente('Parcela '),
            area=2,
            tipo_uso='agricola',
        )
        db.session.add(parcela)
        db.session.commit()
        return parcela

    def aplicador(self, productor):
        aplicador = Aplicador(
            id_productor=productor.id,
            nombre=self._siguiente('Aplicador '),
            cargo='Técnico',
            telefono='6000-1111',
        )
        db.session.add(aplicador)
        db.session.commit()
        return aplicador

    def registro(self, parcela, aplicador):
        cultivo = Cultivo.query.first()
        producto = self.producto()
        registro = RegistroAgricola(
            id_parcela=parcela.id,
            id_cultivo=cultivo.id,
            id_producto=producto.id,
            id_aplicador=aplicador.id,
            fecha=date.today(),
            tipo_control='Herbicida',
            dosis='1 L/ha',
        )
        db.session.add(registro)
        db.session.commit()
        return registro

    def producto(self, nombre=None):
        from app.models import Producto

        producto = Producto.query.first()
        if producto:
            return producto
        producto = Producto(
            nombre_producto=nombre or self._siguiente('Producto '),
            tipo_producto='herbicida',
        )
        db.session.add(producto)
        db.session.commit()
        return producto

    def inventario(self, finca):
        inventario = Inventario(
            id_producto=self.producto().id,
            id_finca=finca.id,
            cantidad=10,
            unidad_medida='kg',
            stock_minimo=1,
            costo_unitario=5,
            fecha_ingreso=date.today(),
        )
        db.session.add(inventario)
        db.session.commit()
        return inventario

    def gasto(self, finca):
        gasto = Gasto(
            id_finca=finca.id,
            tipo_gasto='semilla',
            monto=100,
            descripcion='Prueba',
            fecha=date.today(),
        )
        db.session.add(gasto)
        db.session.commit()
        return gasto

    def produccion(self, parcela):
        produccion = Produccion(
            id_parcela=parcela.id,
            id_cultivo=Cultivo.query.first().id,
            fecha_cosecha=date.today(),
            cantidad=100,
            unidad_medida='kg',
            precio_venta=2,
        )
        db.session.add(produccion)
        db.session.commit()
        return produccion

    def notificacion(self, productor=None, mensaje='Aviso de prueba'):
        notificacion = Notificacion(
            id_productor=productor.id if productor else None,
            mensaje=mensaje,
            tipo='info',
            leido=False,
        )
        db.session.add(notificacion)
        db.session.commit()
        return notificacion


@pytest.fixture()
def fabrica(app):
    # El fixture app mantiene un contexto de aplicación activo durante el test.
    return Fabrica(app)


@pytest.fixture()
def login(client):
    def _login(correo, password='Clave1234'):
        return client.post(
            '/auth/login',
            data={'correo': correo, 'password': password},
            follow_redirects=False,
        )

    return _login
