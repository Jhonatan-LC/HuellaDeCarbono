#!/usr/bin/env python
"""
Script de debugging para analizar la extracción OCR de boletas.
Útil para diagnosticar por qué no se extraen correctamente los valores.
"""

import sys
import os

# Añadir el directorio al path
sys.path.insert(0, os.path.dirname(__file__))

# Detectar poppler ANTES de importar extractor
POPPLER_PATH = None
rutas_poppler = [
    r'C:\Program Files\poppler-26.02.0\Library\bin',
    r'C:\Program Files\poppler\Library\bin',
    r'C:\Program Files (x86)\poppler\Library\bin',
    r'C:\tools\poppler\Library\bin',
]
for ruta in rutas_poppler:
    if os.path.isdir(ruta):
        POPPLER_PATH = ruta
        break

# Establecer variable de entorno si se encontró
if POPPLER_PATH:
    os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')

from auditoria.extractor import (
    procesar_archivo,
    _normalizar_texto,
    extraer_valor_boleta,
)


def debug_boleta(ruta_archivo):
    """Analiza en detalle una boleta y muestra todo el proceso."""
    
    print("=" * 80)
    print(f"ANÁLISIS DE BOLETA: {os.path.basename(ruta_archivo)}")
    print("=" * 80)
    
    # Paso 1: Extraer texto OCR
    print("\n[1] TEXTO OCR EXTRAÍDO (raw):")
    print("-" * 80)
    texto_original = procesar_archivo(ruta_archivo)
    if texto_original:
        print(texto_original[:2000])  # Primeros 2000 caracteres
        if len(texto_original) > 2000:
            print(f"\n... (truncado, total: {len(texto_original)} caracteres)")
    else:
        print("❌ NO SE EXTRAJO TEXTO - Verifica que el PDF sea válido")
        return
    
    # Paso 2: Texto normalizado
    print("\n[2] TEXTO NORMALIZADO:")
    print("-" * 80)
    texto_limpio = _normalizar_texto(texto_original)
    print(texto_limpio[:2000])
    if len(texto_limpio) > 2000:
        print(f"\n... (truncado, total: {len(texto_limpio)} caracteres)")
    
    # Paso 3: Análisis completo
    print("\n[3] RESULTADO DE EXTRACCIÓN:")
    print("-" * 80)
    resultado = extraer_valor_boleta(ruta_archivo)
    
    print(f"Procesado: {resultado['procesado']}")
    print(f"Tipo detectado: {resultado['tipo_detectado']}")
    print(f"Confianza: {resultado['confianza']:.0%}")
    print(f"Mensaje: {resultado['mensaje']}")
    
    print("\n[4] VALORES EXTRAÍDOS:")
    print("-" * 80)
    valor_extraido = resultado['valor_extraido']
    print(f"Energía (kWh): {valor_extraido.get('energia_kwh')}")
    print(f"Combustible (litros): {valor_extraido.get('combustible_litros')}")
    print(f"Período: {valor_extraido.get('periodo')}")
    print(f"Campos detectados: {', '.join(valor_extraido.get('campos_detectados', []))}")
    
    # Paso 5: Búsqueda manual de patrones
    print("\n[5] BÚSQUEDA MANUAL DE PATRONES:")
    print("-" * 80)
    import re
    
    # Buscar números que podrían ser kWh
    patrones_kwh = [
        (r'\b(\d{1,6}(?:[.,]\d{1,3})?)\s*(?:kwh|kw/h|kw\.h|kwh-)', 'kWh directo'),
        (r'consumo\D{0,30}(\d{1,6}(?:[.,]\d{1,3})?)', 'Consumo'),
        (r'energia\D{0,30}(\d{1,6}(?:[.,]\d{1,3})?)', 'Energía'),
    ]
    
    print("Posibles valores de kWh:")
    encontrados = False
    for patron, descripcion in patrones_kwh:
        matches = re.findall(patron, texto_limpio, flags=re.IGNORECASE)
        if matches:
            encontrados = True
            print(f"  {descripcion}: {matches[:5]}")  # Máx 5 resultados
    
    if not encontrados:
        print("  (No se encontraron patrones de kWh)")
    
    # Buscar números que podrían ser litros
    patrones_litros = [
        (r'\b(\d{1,5}(?:[.,]\d{1,3})?)\s*(?:litros?|lts?|lt)\b', 'Litros directo'),
        (r'combustible\D{0,30}(\d{1,5}(?:[.,]\d{1,3})?)', 'Combustible'),
    ]
    
    print("\nPosibles valores de litros:")
    encontrados = False
    for patron, descripcion in patrones_litros:
        matches = re.findall(patron, texto_limpio, flags=re.IGNORECASE)
        if matches:
            encontrados = True
            print(f"  {descripcion}: {matches[:5]}")
    
    if not encontrados:
        print("  (No se encontraron patrones de litros)")
    
    # Buscar periodo
    patrones_periodo = [
        (r'\b((?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{4})\b', 'Mes + Año'),
        (r'\b(\d{4}[-/]\d{1,2})\b', 'Año-Mes'),
        (r'\b(\d{1,2}[-/]\d{4})\b', 'Mes-Año'),
    ]
    
    print("\nPosibles períodos:")
    encontrados = False
    for patron, descripcion in patrones_periodo:
        matches = re.findall(patron, texto_limpio, flags=re.IGNORECASE)
        if matches:
            encontrados = True
            print(f"  {descripcion}: {matches[:5]}")
    
    if not encontrados:
        print("  (No se encontraron patrones de período)")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python debug_extractor.py <ruta_relativa_o_absoluta_al_pdf>")
        print("\nEjemplo:")
        print("  python debug_extractor.py media/boletas/nombre_boleta.pdf")
        sys.exit(1)
    
    ruta_entrada = sys.argv[1]

    # Construir ruta absoluta si la entrada es relativa al directorio raíz del proyecto
    if not os.path.isabs(ruta_entrada):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        ruta = os.path.join(project_root, ruta_entrada)
    else:
        ruta = ruta_entrada

    if not os.path.exists(ruta):
        print(f"❌ Archivo no encontrado: {ruta}")
        sys.exit(1)
    
    debug_boleta(ruta)
