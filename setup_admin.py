"""
Crea el productor + admin inicial + suscripción EMPRESARIAL.
Uso: python setup_admin.py
"""
from app import create_app
from app.config.database import db
from app.models import Productor, Usuario, Suscripcion, Plan
from datetime import datetime, timedelta

CORREO_ADMIN = 'agrodevpty@gmail.com'
PASSWORD_ADMIN = 'admin123'   # ← cámbiala después de entrar
NOMBRE_ADMIN = 'Guillermo Jonhson'


def setup():
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print(" CREANDO ADMIN INICIAL ")
        print("="*60 + "\n")
        
        # 1. Productor
        productor = Productor(
            nombre=NOMBRE_ADMIN,
            telefono='6944-2874',
            correo=CORREO_ADMIN,
            fecha_creacion=datetime.utcnow().date()
        )
        db.session.add(productor)
        db.session.commit()
        print(f"✅ Productor creado (ID: {productor.id})")
        
        # 2. Usuario admin
        admin = Usuario(
            id_productor=productor.id,
            nombre_usuario=NOMBRE_ADMIN,
            correo=CORREO_ADMIN,
            rol='administrador',
            activo=True,
            fecha_registro=datetime.utcnow()
        )
        admin.set_password(PASSWORD_ADMIN)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario admin creado (ID: {admin.id})")
        
        # 3. Suscripción EMPRESARIAL
        plan = Plan.query.filter_by(nombre_plan='EMPRESARIAL').first()
        if not plan:
            print("❌ No existe plan EMPRESARIAL. Algo falló en _init_catalogs.")
            return
        
        suscripcion = Suscripcion(
            id_productor=productor.id,
            id_plan=plan.id,
            fecha_inicio=datetime.now().date(),
            fecha_fin=datetime.now().date() + timedelta(days=3650),
            estado='activa'
        )
        db.session.add(suscripcion)
        db.session.commit()
        print(f"✅ Suscripción EMPRESARIAL asignada")
        
        # 4. Finca inicial
        from app.models import Finca
        finca = Finca(
            id_productor=productor.id,
            nombre_finca='Mi Finca Principal',
            ubicacion='Por definir',
            area_total=1.0
        )
        db.session.add(finca)
        db.session.commit()
        print(f"✅ Finca inicial creada (ID: {finca.id})")
        
        print("\n" + "="*60)
        print(" LISTO ")
        print("="*60)
        print(f"\n  Correo:      {CORREO_ADMIN}")
        print(f"  Contraseña:  {PASSWORD_ADMIN}")
        print(f"\n  ⚠️  Cambia la contraseña después de entrar.")
        print()


if __name__ == '__main__':
    setup()