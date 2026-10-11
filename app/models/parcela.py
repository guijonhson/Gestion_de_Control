from app.config.database import db
from datetime import datetime


class Parcela(db.Model):
    __tablename__ = 'parcela'
    
    id = db.Column(db.Integer, primary_key=True)
    id_finca = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    numero_parcela = db.Column(db.String(50), nullable=False)
    area = db.Column(db.Float)
    cultivo_actual = db.Column(db.String(100))
    fecha_inicio_siembra = db.Column(db.Date)
    duracion_cultivo = db.Column(db.Integer)  # en días
    tipo_uso = db.Column(db.String(20), default='agricola', nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    registros = db.relationship('RegistroAgricola', back_populates='parcela', lazy=True, cascade='all, delete-orphan')
    producciones = db.relationship('Produccion', back_populates='parcela', lazy=True, cascade='all, delete-orphan')
    finca = db.relationship('Finca', back_populates='parcelas')
    agricola = db.relationship('ParcelaAgricola', back_populates='parcela', uselist=False, cascade='all, delete-orphan')
    ganadera = db.relationship('ParcelaGanadera', back_populates='parcela', uselist=False, cascade='all, delete-orphan')
    
    @property
    def detalle(self):
        """Resumen legible del detalle segun el tipo de uso."""
        if self.tipo_uso == 'ganadera':
            return self.ganadera.resumen() if self.ganadera else None
        return self.agricola.resumen() if self.agricola else None
