"""
Script para resetear correo y/o contraseña del administrador.

Uso:
    python reset_admin.py
"""
from app import create_app
from app.config.database import db
from app.models import Usuario


def reset_admin():
    app = create_app()
    
    with app.app_context():
        # Buscar el admin (el primer usuario con rol administrador)
        admin = Usuario.query.filter_by(rol='administrador').first()
        
        if not admin:
            print("\n❌ No se encontró ningún usuario administrador en la DB.")
            print("   Usa init_demo.py o el registro web para crear uno.\n")
            return
        
        print("\n" + "="*60)
        print(" RESET DE ADMINISTRADOR - AGRODEV ")
        print("="*60)
        print(f"\n📋 Admin encontrado:")
        print(f"   ID:               {admin.id}")
        print(f"   Nombre:           {admin.nombre_usuario}")
        print(f"   Correo actual:    {admin.correo}")
        print(f"   Rol:              {admin.rol}")
        print(f"   Activo:           {admin.activo}")
        
        # Pedir nuevos valores
        print("\n" + "-"*60)
        print("Deja en blanco para MANTENER el valor actual.")
        print("-"*60 + "\n")
        
        nuevo_correo = input(f"Nuevo correo [{admin.correo}]: ").strip()
        nuevo_nombre = input(f"Nuevo nombre [{admin.nombre_usuario}]: ").strip()
        nueva_password = input("Nueva contraseña (mínimo 6 caracteres): ").strip()
        
        # Aplicar cambios
        if nuevo_correo:
            # Verificar que no exista otro usuario con ese correo
            existente = Usuario.query.filter_by(correo=nuevo_correo).first()
            if existente and existente.id != admin.id:
                print(f"\n❌ Ya existe otro usuario con el correo '{nuevo_correo}'.")
                return
            admin.correo = nuevo_correo
        
        if nuevo_nombre:
            admin.nombre_usuario = nuevo_nombre
        
        if nueva_password:
            if len(nueva_password) < 6:
                print("\n❌ La contraseña debe tener al menos 6 caracteres.")
                return
            admin.set_password(nueva_password)
            print(f"\n✅ Contraseña actualizada.")
        else:
            print(f"\n⚠️  Contraseña no modificada.")
        
        # Asegurar que esté activo
        admin.activo = True
        
        db.session.commit()
        
        print("\n" + "="*60)
        print(" ✅ ACTUALIZACIÓN EXITOSA ")
        print("="*60)
        print(f"\n   Correo:    {admin.correo}")
        print(f"   Nombre:    {admin.nombre_usuario}")
        print(f"   Rol:       {admin.rol}")
        print(f"   Activo:    {admin.activo}")
        print(f"\n   Ya puedes iniciar sesión con las credenciales actualizadas.\n")


if __name__ == '__main__':
    reset_admin()