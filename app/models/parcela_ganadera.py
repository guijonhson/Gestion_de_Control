from app.config.database import db


class ParcelaGanadera(db.Model):
    """Detalle de una parcela de uso ganadero (uno a uno con Parcela)."""

    __tablename__ = 'parcela_ganadera'

    id = db.Column(db.Integer, primary_key=True)
    id_parcela = db.Column(db.Integer, db.ForeignKey('parcela.id'), nullable=False, unique=True)
    pasto = db.Column(db.String(100), nullable=True)
    tipo_animal = db.Column(db.String(50), nullable=True)
    raza = db.Column(db.String(100), nullable=True)
    cantidad_animales = db.Column(db.Integer, nullable=True)

    parcela = db.relationship('Parcela', back_populates='ganadera')

    def resumen(self):
        partes = []
        if self.tipo_animal:
            partes.append(self.tipo_animal)
        if self.raza:
            partes.append(self.raza)
        if self.cantidad_animales:
            partes.append('{} animales'.format(self.cantidad_animales))
        detalle = ' '.join(partes) if partes else None
        if self.pasto:
            detalle = '{} (pasto {})'.format(detalle, self.pasto) if detalle else 'Pasto {}'.format(self.pasto)
        return detalle
