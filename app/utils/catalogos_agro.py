"""
Catálogos agropecuarios para AgroDev.

Las listas se basan en la zonificación de pastos y forrajes del MIDA (2009,
con apoyo de la FAO) y en el cierre agrícola 2024-2025 del MIDA. Se mantienen
en código (no en la base de datos) para poder ajustarlas sin migraciones.
"""

# Pastos y forrajes: lista oficial MIDA (2009) + Mombasa y Tanzania (IDIAP)
PASTOS = [
    'Elefante', 'Pojuca', 'Angleton', 'Decumbens', 'Tanner', 'Humidicola',
    'Mulato II', 'Alicia (Bermuda)', 'Guinea', 'Aleman', 'Para', 'Andropogon',
    'Suazi', 'Estrella africana', 'Estrella puertorriqueña', 'Marandu',
    'Toledo', 'Cratylia', 'Mani forrajero', 'Leucaena', 'Morera',
    'Mombasa', 'Tanzania',
]

# Tipos de animal criados en una parcela ganadera
TIPOS_ANIMAL = [
    'Bovino', 'Equino', 'Caprino', 'Ovino', 'Porcino', 'Bufalino', 'Aves', 'Otro',
]

# Sugerencias de raza por tipo de animal (el campo sigue siendo texto libre).
# Solo los bovinos tienen respaldo en fuentes panameñas; el resto queda abierto.
RAZAS_SUGERIDAS = {
    'Bovino': [
        'Gyr', 'Brahman', 'Sindi', 'Guzerat', 'Nelore', 'Holstein',
        'Pardo Suizo', 'Senepol', 'Guaymí', 'Guibala',
    ],
    'Equino': [],
    'Caprino': [],
    'Ovino': [],
    'Porcino': [],
    'Bufalino': [],
    'Aves': [],
    'Otro': [],
}

# Advertencias de manejo por pasto (MIDA)
ADVERTENCIAS_PASTO = {
    'Humidicola': 'No recomendado para caballos: contiene oxalato de calcio.',
    'Decumbens': 'Asociado a lesiones hepaticas en bovinos jovenes.',
}

# Cultivos de Panama (cierre agricola 2024-2025, MIDA) con ciclo aproximado en dias.
# Los nombres que ya existen en el catalogo de la base de datos se respetan.
CULTIVOS_PANAMA = [
    ('Arroz', 150), ('Maiz', 120), ('Frijol', 90), ('Sorgo', 110),
    ('Caña de azucar', 365), ('Cafe', 270), ('Cacao', 180), ('Palma aceitera', 365),
    ('Papa', 120), ('Cebolla', 130), ('Tomate industrial', 90),
    ('Yuca', 180), ('Ñame', 240), ('Otoe', 270),
    ('Melon', 90), ('Sandia', 85), ('Zapallo', 100),
    'Platano', 'Citricos', 'Piña', 'Papaya',
]

# Densidad referencial (plantas por hectarea). Solo donde existe fuente tecnica.
DENSIDAD_REFERENCIAL = {
    'Maiz': 65000,    # IDIAP: maiz hibrido, aprox. 65 mil plantas/ha
    'Frijol': 200000, # IDIAP: orden de 200 mil plantas/ha (guia, por confirmar)
    'Poroto': 200000,
}
