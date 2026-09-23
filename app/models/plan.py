from app.config.database import db


class Plan(db.Model):
    __tablename__ = 'plan'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_plan = db.Column(db.String(50), nullable=False, unique=True)
    precio_mensual = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    
    # Límites de recursos (None = ilimitado)
    limite_fincas = db.Column(db.Integer, default=1)
    limite_usuarios = db.Column(db.Integer, default=1)
    limite_parcelas = db.Column(db.Integer, default=5)
    limite_productos = db.Column(db.Integer, default=50)
    limite_inventario = db.Column(db.Integer, default=50)
    limite_registros = db.Column(db.Integer, default=10)
    limite_gastos = db.Column(db.Integer, default=10)
    
    # Funcionalidades booleanas
    reportes_avanzados = db.Column(db.Boolean, default=False)
    exportar_datos = db.Column(db.Boolean, default=False)
    
    suscripciones = db.relationship('Suscripcion', back_populates='plan')
    
    def __repr__(self):
        return f'<Plan {self.nombre_plan} (${self.precio_mensual})>'


def init_planes():
    """Inicializa los planes si no existen."""
    from app.models import Plan as PlanModel
    
    if PlanModel.query.count() > 0:
        return
    
    planes_data = [
        {
            'nombre_plan': 'FREE',
            'precio_mensual': 0.0,
            'descripcion': 'Plan gratuito para empezar',
            'limite_fincas': 1,
            'limite_usuarios': 1,
            'limite_parcelas': 5,
            'limite_productos': 50,
            'limite_inventario': 50,
            'limite_registros': 10,
            'limite_gastos': 10,
            'reportes_avanzados': False,
            'exportar_datos': False,
            'activo': True,
        },
        {
            'nombre_plan': 'BÁSICO',
            'precio_mensual': 10.0,
            'descripcion': 'Plan para pequeñas empresas agrícolas',
            'limite_fincas': 3,
            'limite_usuarios': 2,
            'limite_parcelas': 15,
            'limite_productos': 200,
            'limite_inventario': 50,
            'limite_registros': 10,
            'limite_gastos': 10,
            'reportes_avanzados': True,
            'exportar_datos': False,
            'activo': True,
        },
        {
            'nombre_plan': 'PRO',
            'precio_mensual': 25.0,
            'descripcion': 'Plan profesional',
            'limite_fincas': 10,
            'limite_usuarios': 5,
            'limite_parcelas': 50,
            'limite_productos': 1000,
            'limite_inventario': 50,
            'limite_registros': 10,
            'limite_gastos': 10,
            'reportes_avanzados': True,
            'exportar_datos': True,
            'activo': True,
        },
        {
            'nombre_plan': 'EMPRESARIAL',
            'precio_mensual': 50.0,
            'descripcion': 'Plan ilimitado',
            'limite_fincas': None,
            'limite_usuarios': None,
            'limite_parcelas': None,
            'limite_productos': None,
            'limite_inventario': None,
            'limite_registros': None,
            'limite_gastos': None,
            'reportes_avanzados': True,
            'exportar_datos': True,
            'activo': True,
        },
    ]
    
    for data in planes_data:
        db.session.add(PlanModel(**data))
    db.session.commit()