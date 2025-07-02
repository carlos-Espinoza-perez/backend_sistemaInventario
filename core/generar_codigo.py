import random
import re

def generar_codigo(nombre: str) -> str:
    # Limpiar caracteres no alfanuméricos y dividir palabras
    palabras = re.findall(r'\b\w+', nombre.upper())
    
    if not palabras:
        return "PROD_" + str(random.randint(1000, 9999))

    # Tomar primeras dos letras de la primera palabra
    primera = palabras[0][:2]

    # Tomar la última palabra completa si es diferente
    ultima = palabras[-1] if palabras[-1] != palabras[0] else ""

    # Generar número aleatorio opcional para unicidad
    numero = random.randint(10, 99)

    # Construir código
    codigo = f"{primera}_{ultima}".strip("_")
    return f"{codigo}_{numero}" if ultima else f"{primera}_{numero}"
