"""
Catálogos agropecuarios para AgroDev.

Las listas se basan en la zonificación de pastos y forrajes del MIDA (2009,
con apoyo de la FAO) y en el cierre agrícola 2024-2025 del MIDA. Se mantienen
en código (no en la base de datos) para poder ajustarlas sin migraciones.
"""

# Pastos y forrajes: lista oficial MIDA (2009) + Mombasa y Tanzania (IDIAP)
PASTOS = [
    'Elefante', 'Pojuca', 'Angleton', 'Decumbens', 'Tanner', 'Humidícola',
    'Mulato II', 'Alicia (Bermuda)', 'Guinea', 'Alemán', 'Pará', 'Andropogon',
    'Suazi', 'Estrella africana', 'Estrella puertorriqueña', 'Marandú',
    'Toledo', 'Cratylia', 'Maní forrajero', 'Leucaena', 'Morera',
    'Mombasa', 'Tanzania', 'Otro',
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
        'Pardo Suizo', 'Senepol', 'Guaymí', 'Guabalá',
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
    'Humidícola': 'No recomendado para caballos: contiene oxalato de calcio.',
    'Decumbens': 'Asociado a lesiones hepáticas en bovinos jóvenes.',
}

# Cultivos de Panamá (cierre agrícola 2024-2025, MIDA) con ciclo aproximado en días.
# Los que ya existen en el catálogo de la base de datos se respetan.
CULTIVOS_PANAMA = [
    ('Arroz', 150), ('Maíz', 120), ('Frijol', 90), ('Sorgo', 110),
    ('Caña de azúcar', 365), ('Café', 270), ('Cacao', 180), ('Palma aceitera', 365),
    ('Papa', 120), ('Cebolla', 130), ('Tomate', 90),
    ('Yuca', 180), ('Ñame', 240), ('Otoe', 270),
    ('Melón', 90), ('Sandía', 85), ('Zapallo', 100),
    ('Plátano', 300), ('Cítricos', 365), ('Piña', 540), ('Papaya', 270),
]

# Densidad referencial (plantas por hectárea). Solo donde existe fuente técnica.
DENSIDAD_REFERENCIAL = {
    'Maíz': 65000,     # IDIAP: maíz híbrido, aprox. 65 mil plantas/ha
    'Frijol': 200000,  # IDIAP: orden de 200 mil plantas/ha (guía, por confirmar)
    'Poroto': 200000,
}
