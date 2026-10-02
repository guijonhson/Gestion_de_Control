"""
Utilidad para enviar alertas por correo usando Web3Forms.
Usa el mismo servicio (sin backend de correo propio) que el sitio de AgroDev PTY.

Requiere la variable de entorno WEB3FORMS_ACCESS_KEY configurada en producción
(en Render: Environment -> Add Environment Variable).
Si no está configurada, la alerta simplemente no se envía (pero el sistema
sigue funcionando con normalidad: la notificación interna siempre se crea).
"""
import os
import requests

WEB3FORMS_URL = "https://api.web3forms.com/submit"


def enviar_alerta_email(asunto, mensaje):
    """
    Envía un correo de alerta al administrador de AgroDev PTY.
    No lanza excepciones si falla: solo registra el error en consola,
    para que un problema de correo nunca rompa el flujo normal del sistema
    (registro de usuario, solicitud de pago, etc).
    """
    access_key = os.environ.get("WEB3FORMS_ACCESS_KEY")

    if not access_key:
        print("[email] WEB3FORMS_ACCESS_KEY no configurada; alerta no enviada.")
        return False

    try:
        response = requests.post(
            WEB3FORMS_URL,
            data={
                "access_key": access_key,
                "subject": asunto,
                "from_name": "Gestión de Control - AgroDev PTY",
                "message": mensaje,
            },
            timeout=5,
        )
        data = response.json()
        if not (response.ok and data.get("success")):
            print(f"[email] Web3Forms respondió con error: {data}")
            return False
        return True
    except Exception as e:
        print(f"[email] Error enviando alerta: {e}")
        return False
