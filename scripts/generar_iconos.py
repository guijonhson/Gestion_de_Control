"""Genera los iconos PWA a partir de app/static/img/logo.jpeg.

Uso (solo desarrollo):
    python scripts/generar_iconos.py

Requiere Pillow (incluido en requirements-dev.txt).
"""
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / 'app' / 'static' / 'img' / 'logo.jpeg'
DESTINO = RAIZ / 'app' / 'static' / 'img' / 'icons'
VERDE = (46, 125, 50)


def generar(tamano, nombre, maskable=False):
    DESTINO.mkdir(parents=True, exist_ok=True)
    with Image.open(ORIGEN) as original:
        original = original.convert('RGBA')
        lienzo = Image.new(
            'RGBA',
            (tamano, tamano),
            VERDE if maskable else (255, 255, 255, 255),
        )
        caja = int(tamano * (0.8 if maskable else 0.9))
        copia = original.copy()
        copia.thumbnail((caja, caja), Image.Resampling.LANCZOS)
        x = (tamano - copia.width) // 2
        y = (tamano - copia.height) // 2
        lienzo.alpha_composite(copia, (x, y))
        lienzo.convert('RGB').save(DESTINO / nombre, 'PNG', optimize=True)
        print(f'Generado {nombre} ({tamano}x{tamano})')


if __name__ == '__main__':
    generar(192, 'icon-192.png')
    generar(512, 'icon-512.png')
    generar(512, 'icon-maskable-512.png', maskable=True)
    generar(180, 'apple-touch-icon-180.png')
