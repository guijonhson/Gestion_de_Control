# Peso de la pantalla de login

Medición hecha el 24 de octubre de 2026 comparando `main` con la rama
`qa-pwa`. Se cuentan los archivos que el navegador descarga en la primera
visita a `/auth/login`:

- HTML generado de `base.html` + `auth/login.html`
- Bootstrap CSS y JS (antes desde CDN, ahora locales)
- Bootstrap Icons CSS y fuente WOFF2
- `responsive.css`
- Logo
- Icono de pestaña (antes `static/icons/icon-192.png`, después
  `img/icons/icon-192.png`)
- Manifest (solo después)

Los tamaños "gzip" son el resultado de comprimir cada archivo localmente con
gzip nivel 6. No incluyen cabeceras HTTP ni TLS.

| Recurso | Antes (bytes) | Después (bytes) | Antes gzip | Después gzip |
|---|---:|---:|---:|---:|
| HTML | 3.595 | 11.569 | 1.406 | 3.257 |
| Bootstrap CSS | 232.914 | 232.914 | 31.170 | 31.170 |
| Bootstrap JS | 80.421 | 80.421 | 23.296 | 23.296 |
| Bootstrap Icons CSS | 95.609 | 95.609 | 13.455 | 13.455 |
| Fuente WOFF2 | 121.084 | 121.084 | 120.949 | 120.949 |
| `responsive.css` | 6.669 | 6.669 | 1.745 | 1.745 |
| Logo | 35.754 | 35.754 | 27.535 | 27.535 |
| Icono de pestaña | 35.754 | 9.144 | 35.754 | 8.629 |
| Manifest | 0 | 672 | 0 | 347 |
| **Total** | **611.800** | **593.836** | **255.310** | **220.383** |
| **Total (KiB)** | **597,5** | **579,9** | **249,3** | **215,2** |

Resultado de la primera carga:

- **17.964 bytes menos** sin comprimir (-17,5 KiB).
- **34.927 bytes menos con gzip** (-34,1 KiB, aproximadamente -13,7 %).
- Se eliminan las peticiones a `cdn.jsdelivr.net` (CSS, JS y fuente).
- Los archivos locales se sirven con `Cache-Control: public, max-age=604800`
  (7 días) y llevan `?v=` para invalidar caché al desplegar.
- El HTML sigue con `Cache-Control: no-store`, por lo que una visita repetida
  descarga solo el HTML y el manifest; CSS, JS, fuente, logo e icono salen de
  caché.

## Costo adicional de la PWA

El service worker, después de la primera carga, precarga el shell de la
aplicación en segundo plano. Esa descarga adicional es de aproximadamente
**569 KiB sin comprimir**:

- Bootstrap CSS y JS
- Bootstrap Icons CSS y WOFF2
- `responsive.css`
- Logo
- Icono 192
- Página `/offline`

La mayor parte de esos archivos ya se descargó para pintar el login, por lo que
el navegador puede reutilizar la caché HTTP. Los iconos 512, maskable y Apple no
se precargan: se sirven desde el manifest cuando el dispositivo los necesita.
Este costo es el precio de tener una pantalla de "sin conexión" y recursos
básicos disponibles sin red.
