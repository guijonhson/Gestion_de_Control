# Gestión de Control – AgroDev

Aplicación web de gestión agropecuaria para fincas, parcelas, cultivos,
aplicadores, inventario, gastos, producción y registros de aplicación.
Está construida con Flask, SQLAlchemy y Bootstrap, y funciona como PWA
instalable.

## Requisitos

- Python 3.11 o superior
- SQLite para desarrollo o PostgreSQL para producción
- Variables de entorno descritas en `.env.example`

## Instalación local

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # completar los valores
python run.py
```

La aplicación queda disponible en `http://127.0.0.1:5000`.

En Linux/macOS los comandos equivalentes son `source venv/bin/activate` y
`cp .env.example .env`.

### Variables obligatorias

- `SECRET_KEY`: clave privada de Flask. En producción es obligatoria.
- `FLASK_ENV`: `development`, `testing` o `production`.
- `DATABASE_URL`: cadena de conexión. Si se omite se usa SQLite local.
- `WEB3FORMS_ACCESS_KEY`: opcional. Si existe, se envían alertas por correo al
  administrador. Si falta, la app sigue funcionando y solo se crea la
  notificación interna.

Nunca se debe subir el archivo `.env` al repositorio.

## Base de datos y migraciones

Al arrancar, la aplicación crea las tablas que falten y aplica cambios
estructurales sencillos mediante `app/utils/migraciones.py`. El administrador
también puede ejecutarlos manualmente con el botón **Actualizar base de datos**
en **Usuarios**, que aparece solo cuando hay cambios pendientes.

Los nombres internos de los planes (`FREE`, `BÁSICO`, `PRO`, `EMPRESARIAL`) no
se modifican. La interfaz los muestra como Gratis, Básico, Profesional y
Empresarial mediante el filtro `nombre_plan_visible`.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Las pruebas usan SQLite en memoria y no tocan la base de datos real.

### Pruebas E2E con Playwright

En dos terminales:

```bash
python qa/run_e2e_server.py
python qa/e2e_flujo_critico.py
```

El servidor E2E usa una base temporal. La primera vez hay que instalar el
navegador:

```bash
python -m playwright install chromium
```

El script recorre registro, finca, parcela, aplicador, registro agrícola,
cierre y apertura de sesión, manifest, service worker y página sin conexión.
La captura queda en `qa/evidencias/`.

## PWA

- Manifest: `/manifest.webmanifest`
- Service worker: `/sw.js` (alcance `/`)
- Página sin conexión: `/offline`
- Iconos: `app/static/img/icons/`

El service worker solo guarda archivos estáticos y la página sin conexión.
**No cachea HTML autenticado, peticiones POST ni rutas de autenticación.**
Para regenerar los iconos:

```bash
python scripts/generar_iconos.py
```

La aplicación necesita conexión para consultar y guardar datos. La instalación
no habilita edición offline.

## Seguridad

- Cada productor solo puede consultar sus propios datos; las rutas con ID
  responden 404 cuando el recurso no pertenece al usuario.
- El administrador puede consultar los datos de todos los productores y
  gestionar las notificaciones generales.
- El cierre de sesión es solo por `POST` y todos los formularios usan CSRF.
- Los catálogos de cultivos y productos solo los puede eliminar un
  administrador, y no se eliminan si están en uso.
- Las respuestas HTML y las rutas autenticadas llevan `Cache-Control: no-store`.
- Las contraseñas se almacenan con hash; nunca en texto plano.

## Despliegue en Render

- Comando de arranque: `gunicorn run:app`
- Variables: `SECRET_KEY`, `DATABASE_URL`, `WEB3FORMS_ACCESS_KEY` y
  `FLASK_ENV=production`.
- Verificación de vida: `GET /health`.

La rama de producción es `main`. El trabajo de QA y PWA se desarrolla en la
rama `qa-pwa` y no debe desplegarse desde ahí.
