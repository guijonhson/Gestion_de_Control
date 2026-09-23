from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from app.config.database import db
import os

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig())
    elif env == 'testing':
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    db.init_app(app)
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        try:
            return db.session.get(Usuario, int(user_id))
        except (ValueError, TypeError):
            return None
    
    @app.errorhandler(404)
    def error_404(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def error_500(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Captura errores de CSRF y los muestra en lugar de 400 silencioso"""
        app.logger.warning(f"CSRF error: {e.description}")
        return render_template('errors/csrf.html', reason=e.description), 400
    
    # Blueprints
    from app.controllers import auth, dashboard, gestion_usuarios, productores, fincas, parcelas, cultivos, productos, aplicadores, registros, reportes, inventario, gastos, produccion
    from app.controllers.notificaciones import bp as notificaciones_bp
    from app.controllers.suscripciones import bp as suscripciones_bp
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(gestion_usuarios.bp)
    app.register_blueprint(productores.bp)
    app.register_blueprint(fincas.bp)
    app.register_blueprint(parcelas.bp)
    app.register_blueprint(cultivos.bp)
    app.register_blueprint(productos.bp)
    app.register_blueprint(aplicadores.bp)
    app.register_blueprint(registros.bp)
    app.register_blueprint(reportes.bp)
    app.register_blueprint(inventario.bp)
    app.register_blueprint(gastos.bp)
    app.register_blueprint(produccion.bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(suscripciones_bp)
    
    # Crear DB y catálogos solo si no existen
    with app.app_context():
        db.create_all()
        _init_catalogs()
    
    return app


def _init_catalogs():
    from app.models import Cultivo, Producto
    from app.models.plan import init_planes
    
    if Cultivo.query.count() == 0:
        cultivos = [
            Cultivo(nombre_cultivo='Maíz', ciclo_dias_aprox=120),
            Cultivo(nombre_cultivo='Frijol', ciclo_dias_aprox=90),
            Cultivo(nombre_cultivo='Arroz', ciclo_dias_aprox=150),
            Cultivo(nombre_cultivo='Caña de azúcar', ciclo_dias_aprox=365),
            Cultivo(nombre_cultivo='Papa', ciclo_dias_aprox=120),
            Cultivo(nombre_cultivo='Tomate', ciclo_dias_aprox=90),
            Cultivo(nombre_cultivo='Plátano', ciclo_dias_aprox=300),
            Cultivo(nombre_cultivo='Yuca', ciclo_dias_aprox=180),
        ]
        for c in cultivos:
            db.session.add(c)
        db.session.commit()
    
    if Producto.query.count() == 0:
        productos = [
            Producto(nombre_producto='Glifosato', tipo_producto='herbicida'),
            Producto(nombre_producto='2,4-D', tipo_producto='herbicida'),
            Producto(nombre_producto='Atrazina', tipo_producto='herbicida'),
            Producto(nombre_producto='Mancozeb', tipo_producto='fungicida'),
            Producto(nombre_producto='Carbendazim', tipo_producto='fungicida'),
            Producto(nombre_producto='Urea', tipo_producto='fertilizante'),
            Producto(nombre_producto='NPK 10-30-10', tipo_producto='fertilizante'),
            Producto(nombre_producto='Fosfato diamónico', tipo_producto='fertilizante'),
            Producto(nombre_producto='Cypermethrin', tipo_producto='insecticida'),
            Producto(nombre_producto='Chlorpyrifos', tipo_producto='insecticida'),
        ]
        for p in productos:
            db.session.add(p)
        db.session.commit()
    
    init_planes()