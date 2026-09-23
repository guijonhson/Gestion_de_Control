from app.config.database import db
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash


class Usuario(db.Model):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    id_productor = db.Column(db.Integer, db.ForeignKey('productor.id'), nullable=False)
    nombre_usuario = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='cliente')
    activo = db.Column(db.Boolean, default=True)
    ultimo_acceso = db.Column(db.DateTime)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        # Si activo es None, considerar activo (para compatibilidad con datos viejos)
        if self.activo is None:
            return True
        return bool(self.activo)
    
    @property
    def is_anonymous(self):
        return False
    
    def __repr__(self):
        return f'<Usuario {self.id}: {self.correo} ({self.rol})>'