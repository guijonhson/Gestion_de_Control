"""
Script para actualizar los planes de suscripcion
"""
from app import create_app
from app.config.database import db
from app.models import Plan, Suscripcion
from datetime import datetime, timedelta


def actualizar_planes():
    """Actualiza los planes con los nuevos valores"""
    app = create_app()
    
    with app.app_context():
        print("Eliminando planes antiguos...")
        Plan.query.delete()
        Suscripcion.query.delete()
        db.session.commit()
        print("Planes eliminados.\n")
        
        # Crear nuevos planes
        planes_data = [
            {
                'nombre_plan': 'FREE',
                'precio_mensual': 0.0,
                'descripcion': 'Plan gratuito para empezar con tu negocio agricola',
                'limite_fincas': 1,
                'limite_usuarios': 1,
                'limite_parcelas': 5,
                'limite_productos': 50,
                'reportes_avanzados': False,
                'exportar_datos': False,
                'activo': True
            },
            {
                'nombre_plan': 'BÁSICO',
                'precio_mensual': 10.0,
                'descripcion': 'Plan ideal para pequenas empresas agricolas',
                'limite_fincas': 3,
                'limite_usuarios': 2,
                'limite_parcelas': 15,
                'limite_productos': 200,
                'reportes_avanzados': True,
                'exportar_datos': False,
                'activo': True
            },
            {
                'nombre_plan': 'PRO',
                'precio_mensual': 25.0,
                'descripcion': 'Plan profesional para empresas en crecimiento',
                'limite_fincas': 10,
                'limite_usuarios': 5,
                'limite_parcelas': 50,
                'limite_productos': 1000,
                'reportes_avanzados': True,
                'exportar_datos': True,
                'activo': True
            },
            {
                'nombre_plan': 'EMPRESARIAL',
                'precio_mensual': 50.0,
                'descripcion': 'Hasta 10 usuarios, fincas, parcelas y productos ilimitados',
                'limite_fincas': None,
                'limite_usuarios': 10,
                'limite_parcelas': None,
                'limite_productos': None,
                'reportes_avanzados': True,
                'exportar_datos': True,
                'activo': True
            }
        ]
        
        print("Creando nuevos planes...")
        for plan_data in planes_data:
            plan = Plan(**plan_data)
            db.session.add(plan)
        
        db.session.commit()
        
        # Asignar EMPRESARIAL al admin
        from app.models.usuario import Usuario
        admin = Usuario.query.filter_by(rol='administrador').first()
        
        if admin:
            print(f"\nAsignando plan EMPRESARIAL al admin: {admin.correo}")
            
            plan_empresarial = Plan.query.filter_by(nombre_plan='EMPRESARIAL').first()
            
            # Eliminar suscripcion anterior del admin
            Suscripcion.query.filter_by(id_productor=admin.id_productor).delete()
            
            # Crear nueva suscripcion EMPRESARIAL
            suscripcion = Suscripcion(
                id_productor=admin.id_productor,
                id_plan=plan_empresarial.id,
                fecha_inicio=datetime.now().date(),
                fecha_fin=datetime.now().date() + timedelta(days=365),  # 1 año
                estado='activa'
            )
            db.session.add(suscripcion)
            db.session.commit()
            
            print(f"[OK] Plan EMPRESARIAL asignado hasta: {suscripcion.fecha_fin}")
        else:
            print("\n[ERROR] No se encontró usuario administrador")
        
        # Mostrar resumen
        print("\n" + "="*50)
        print("PLANES ACTUALIZADOS")
        print("="*50)
        
        planes = Plan.query.all()
        for p in planes:
            print(f"\n{p.nombre_plan} - ${p.precio_mensual}/mes")
            print(f"   Fincas: {p.limite_fincas or 'Ilimitado'}")
            print(f"   Usuarios: {p.limite_usuarios or 'Ilimitado'}")
            print(f"   Parcelas: {p.limite_parcelas or 'Ilimitado'}")
            print(f"   Productos: {p.limite_productos or 'Ilimitado'}")


if __name__ == '__main__':
    actualizar_planes()
