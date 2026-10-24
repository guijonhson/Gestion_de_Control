"""Servidor local con base de datos temporal para las pruebas E2E.

Uso:
    python qa/run_e2e_server.py

No usa la base de datos real ni las credenciales de producción.
"""
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

RUTA_DB = Path(tempfile.gettempdir()) / 'agrodev_e2e.db'
if RUTA_DB.exists():
    RUTA_DB.unlink()

os.environ['DATABASE_URL'] = f'sqlite:///{RUTA_DB.as_posix()}'
os.environ.setdefault('SECRET_KEY', 'clave-solo-para-e2e')
os.environ['FLASK_ENV'] = 'development'

from app import create_app  # noqa: E402

app = create_app()

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', '5000'))
    print(f'Servidor E2E en http://127.0.0.1:{puerto}')
    print(f'Base temporal: {RUTA_DB}')
    app.run(host='127.0.0.1', port=puerto, debug=False, use_reloader=False)
