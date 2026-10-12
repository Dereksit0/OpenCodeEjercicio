"""Banco de palabras: dato puro, cero logica.

Reglas que cumple cada palabra, a proposito:
  - exactamente 5 letras
  - mayusculas, sin tildes ni ñ, para que validar un intento sea un
    recorte a "A".."Z" y no una lista de excepciones
  - las letras pueden repetirse (como en el Wordle real: CRANE, ARRAY).
    Es justo esa repeticion la que obliga al algoritmo de dos pasadas:
    si nunca se repitieran, bastaria con un "esta en la palabra?".
Los grupos son solo para leerlo comodo; el juego los mezcla todos.
"""

ANIMALES = (
    "GATOS", "RABIA", "PERRO", "PLUMA", "COLAS", "MOSCA", "ABEJA", "CERDO", "OVEJA",
    "CABRA", "ZORRO", "MIRLO", "CISNE", "GANSO", "HIENA", "SIMIO", "BURRO", "PECES",
    "PULPO", "BAGRE", "POLLO",
)

CASA = (
    "MESAS", "COJIN", "RELOJ", "TAZAS", "VASOS", "CABLE", "BANCO", "SILLA", "SUELO",
    "PARED", "TECHO", "PLATO", "HORNO", "BOLSA", "GORRA", "BOTAS", "BOLSO", "LLAVE",
    "COFRE", "CARGA", "METAL", "PLOMO", "COBRE", "ROBLE", "OLIVO", "RIEGO", "GRIFO",
    "DUCHA", "PAPEL", "LIBRO", "RADIO", "LENTE", "MARCO", "TINTA", "SELLO", "CINTA",
    "LISTA", "CARTA", "FAROL", "BIDON", "GARRA", "ZARPA", "BRAZO", "BARRA",
)

NATURALEZA = (
    "NUBES", "HIELO", "MIEDO", "FUEGO", "LLAMA", "NIEVE", "TRIGO", "ROCAS", "MONTE",
    "VALLE", "MAREA", "CALMA", "BRUMA", "LUCES", "NOCHE", "BARRO", "CAMPO", "PRADO",
    "SELVA", "HOJAS", "SAVIA", "MUSGO", "POLEN", "OCASO", "BRISA", "PLAYA", "ARENA",
    "DUNAS", "SAUCE", "PINOS", "CEDRO", "LIRIO", "CIELO", "VENUS", "RAYOS", "ASCUA",
    "BRASA", "VAPOR", "GRAVA", "SENDA", "ATRIO", "PATIO",
)

COMIDA = (
    "PANES", "AVENA", "CACAO", "QUESO", "LECHE", "HUEVO", "SALSA", "GUISO", "CALDO",
    "CREMA", "TARTA", "DULCE", "FRUTA", "MANGO", "CLAVO", "ARROZ", "CLARA", "TORTA",
    "CUAJO", "MOSTO", "SIDRA", "PECHO",
)

ACCIONES = (
    "HACER", "DECIR", "TENER", "COMER", "BAILE", "CANTO", "PAGAR", "FIJAR", "ANDAR",
    "VOLAR", "NADAR", "TOCAR", "JUGAR", "GANAR", "ABRIR", "VENIR", "MIRAR", "SABER",
    "CREER", "DUDAR", "TEMER", "BESAR", "LAVAR", "TIRAR", "BOTAR", "DEJAR", "PASAR",
    "SALIR", "SUBIR", "BAJAR", "NACER", "VIVIR", "MORIR", "HELAR", "VOTAR", "MUDAR",
    "LAMER", "BATIR", "PEGAR", "COSER", "TEJER", "MOVER", "GIRAR", "ECHAR", "PEDIR",
    "NEGAR",
)

CUALIDADES = (
    "CLARO", "VERDE", "NEGRO", "AGRIO", "LENTO", "CIEGO", "SORDO", "TONTO", "LISTO",
    "TORPE", "POBRE", "LARGO", "CORTO", "NUEVO", "VIEJO", "JOVEN", "BUENO", "BREVE",
    "RECIO", "SUAVE", "SUTIL", "ANCHO", "VASTO", "UNICO", "DOBLE", "IGUAL", "MEJOR",
)

LUGARES = (
    "PLAZA", "CALLE", "MUSEO", "HOTEL", "ALDEA", "LUGAR", "NORTE", "OESTE", "CERCA",
    "ISLAS", "MARTE", "FINCA", "CHOZA", "TORRE", "ACERA", "ANCLA", "CANOA", "BARCA",
    "BALSA", "GOLFO",
)

VARIOS = (
    "PUNTO", "TRAZO", "OBRAS", "PROSA", "VERSO", "POEMA", "RONDA", "TURNO", "FECHA",
    "AHORA", "TARDE", "MEDIO", "LOGRO", "BORDE", "COSTA", "SABOR", "COLOR", "RITMO",
    "SUCIO", "ORDEN", "RUIDO", "GOLPE", "VALOR", "LABOR", "MAGIA", "TRUCO", "HECHO",
    "BICHO", "CELOS", "TIBIO", "SUDOR", "FALDA", "MANTA", "CUERO", "SALTO", "FLOJO",
    "RONCO", "TAPON", "BOINA", "GORRO", "GAFAS", "AGUJA", "DEDAL", "BOTON",
)

# El banco completo: la suma de todos los grupos.
PALABRAS = ANIMALES + CASA + NATURALEZA + COMIDA + ACCIONES + CUALIDADES + LUGARES + VARIOS
