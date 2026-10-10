from app.config.database import db


class ParcelaAgricola(db.Model):
    """Detalle de una parcela de uso agricola (uno a uno con Parcela)."""

    __tablename__ = 'parcela_agricola'

    id = db.Column(db.Integer, primary_key=True)
    id_parcela = db.Column(db.Integer, db.ForeignKey('parcela.id'), nullable=False, unique=True)
    id_cultivo = db.Column(db.Integer, db.ForeignKey('cultivo.id'), nullable=True)
    densidad_plantas_ha = db.Column(db.Float, nullable=True)

    parcela = db.relationship('Parcela', back_populates='agricola')
    cultivo = db.relationship('Cultivo')

    def resumen(self):
        partes = []
        if self.cultivo:
            partes.append(self.cultivo.nombre_cultivo)
        if self.densidad_plantas_ha:
            partes.append('{:,.0f} pl/ha'.format(self.densidad_plantas_ha))
        return ', '.join(partes) if partes else None
