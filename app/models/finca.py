from app.config.database import db
from datetime import datetime

class Finca(db.Model):
    __tablename__ = 'finca'
    
    id = db.Column(db.Integer, primary_key=True)
    id_productor = db.Column(db.Integer, db.ForeignKey('productor.id'), nullable=False)
    nombre_finca = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    area_total = db.Column(db.Float)
    rubro = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    parcelas = db.relationship('Parcela', back_populates='finca', lazy=True, cascade='all, delete-orphan')
    gastos = db.relationship('Gasto', back_populates='finca', lazy=True, cascade='all, delete-orphan')
    inventarios = db.relationship('Inventario', back_populates='finca', lazy=True, cascade='all, delete-orphan')
