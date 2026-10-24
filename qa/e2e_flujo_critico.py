"""Flujo crítico E2E con Playwright.

Requiere el servidor local:
    python qa/run_e2e_server.py

Y en otra terminal:
    python qa/e2e_flujo_critico.py

Variables opcionales:
    BASE_URL=http://127.0.0.1:5000
    HEADLESS=0   (para ver el navegador)
"""
import os
import re
import time
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
HEADLESS = os.environ.get('HEADLESS', '1') != '0'
EVIDENCIAS = Path(__file__).resolve().parent / 'evidencias'
EVIDENCIAS.mkdir(exist_ok=True)

sufijo = f'{int(time.time())}-{uuid.uuid4().hex[:6]}'
correo = f'e2e-{sufijo}@example.com'
password = 'Clave1234'


def url(ruta):
    return f'{BASE_URL}{ruta}'


def ejecutar():
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=HEADLESS)
        contexto = navegador.new_context(viewport={'width': 1280, 'height': 900})
        pagina = contexto.new_page()
        errores_consola = []
        pagina.on(
            'console',
            lambda mensaje: errores_consola.append(mensaje.text)
            if mensaje.type == 'error'
            else None,
        )

        # 1. Registro público con aceptación de términos.
        pagina.goto(url('/auth/register'))
        pagina.fill('#nombre', 'Productor E2E')
        pagina.fill('#telefono', '6000-0000')
        pagina.fill('#correo', correo)
        pagina.fill('#nombre_usuario', f'e2e-{sufijo}')
        pagina.fill('#password', password)
        pagina.fill('#password_confirmacion', password)
        pagina.check('#acepto_terminos')
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/dashboard/')
        expect(pagina.get_by_text('Primeros pasos')).to_be_visible()
        print('OK registro y onboarding')

        # 2. Primera finca.
        pagina.goto(url('/fincas/crear'))
        pagina.fill('input[name="nombre_finca"]', 'Finca E2E')
        pagina.fill('input[name="ubicacion"]', 'Panamá')
        pagina.fill('input[name="area_total"]', '5')
        pagina.fill('input[name="rubro"]', 'agricultura')
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/fincas/')
        expect(pagina.get_by_text('Finca E2E')).to_be_visible()
        print('OK finca')

        # 3. Parcela.
        pagina.goto(url('/parcelas/crear'))
        pagina.locator('select[name="id_finca"]').select_option(index=1)
        pagina.fill('input[name="numero_parcela"]', 'Parcela E2E')
        pagina.fill('input[name="area"]', '1.5')
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/parcelas/')
        expect(pagina.get_by_text('Parcela E2E')).to_be_visible()
        print('OK parcela')

        # 4. Aplicador.
        pagina.goto(url('/aplicadores/crear'))
        pagina.fill('input[name="nombre"]', 'Aplicador E2E')
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/aplicadores/')
        expect(pagina.get_by_text('Aplicador E2E')).to_be_visible()
        print('OK aplicador')

        # 5. Registro agrícola.
        pagina.goto(url('/registros/crear'))
        pagina.fill('input[name="fecha"]', time.strftime('%Y-%m-%d'))
        pagina.locator('select[name="id_cultivo"]').select_option(index=1)
        pagina.locator('select[name="id_producto"]').select_option(index=1)
        pagina.locator('select[name="id_parcela"]').select_option(index=1)
        pagina.locator('select[name="id_aplicador"]').select_option(index=1)
        pagina.locator('select[name="tipo_control"]').select_option(
            value='herbicida'
        )
        pagina.fill('input[name="dosis"]', '1 L/ha')
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/registros/')
        expect(pagina.get_by_text('Herbicida')).to_be_visible()
        print('OK registro agrícola')

        # 6. Cerrar sesión y entrar de nuevo.
        pagina.locator('form[action="/auth/logout"] button[type="submit"]').first.click()
        pagina.wait_for_url('**/auth/login')
        pagina.fill('#correo', correo)
        pagina.fill('#password', password)
        pagina.locator('form:not([action]) button[type="submit"]').click()
        pagina.wait_for_url('**/dashboard/')
        expect(pagina.get_by_text('Bienvenido,')).to_be_visible()
        print('OK logout / login')

        # 7. Manifest y service worker.
        manifest = pagina.evaluate(
            "fetch('/manifest.webmanifest').then(r => r.json())"
        )
        assert manifest['name'].startswith('AgroDev')
        assert manifest['display'] == 'standalone'
        pagina.wait_for_function(
            "navigator.serviceWorker && navigator.serviceWorker.controller !== null",
            timeout=15000,
        )
        print('OK manifest y service worker')

        # 8. La página offline está guardada en la caché del service worker.
        en_cache = pagina.evaluate(
            """
            caches.keys().then(claves => Promise.all(
                claves.map(clave => caches.open(clave)
                    .then(cache => cache.match('/offline'))
                    .then(respuesta => Boolean(respuesta)))
            )).then(resultados => resultados.some(Boolean))
            """
        )
        assert en_cache, 'El service worker no guardó /offline'
        pagina.goto(url('/offline'))
        expect(pagina.get_by_text('Sin conexión')).to_be_visible()
        print('OK página offline en caché')

        # Comprobación adicional: el navegador puede simular falta de red.
        contexto.set_offline(True)
        try:
            sin_red = pagina.evaluate(
                "fetch('/health').then(() => false).catch(() => true)"
            )
            assert sin_red, 'El modo sin conexión del navegador no se activó'
            print('OK simulación de falta de red')
        finally:
            contexto.set_offline(False)

        pagina.goto(url('/dashboard/'))
        pagina.screenshot(
            path=str(EVIDENCIAS / 'e2e_dashboard.png'), full_page=True
        )

        if errores_consola:
            print('Avisos de consola:')
            for error in errores_consola:
                print(' -', error)

        print(f'E2E completado con {correo}')
        navegador.close()


if __name__ == '__main__':
    ejecutar()
