#!/usr/bin/env python
"""
Script para verificar si pdf2image puede procesar los PDFs.
"""

import sys
import os
from pdf2image import convert_from_path
from PIL import Image

# Detectar poppler
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
        print(f"Poppler encontrado en: {ruta}")
        break

ruta = sys.argv[1] if len(sys.argv) > 1 else "media/boletas/F-27076291_310525_414.pdf"

try:
    print(f"Intentando convertir PDF: {ruta}")
    kwargs = {'dpi': 150, 'first_page': 1, 'last_page': 1}
    if POPPLER_PATH:
        kwargs['poppler_path'] = POPPLER_PATH
    paginas = convert_from_path(ruta, **kwargs)
    print(f"✓ Conversión exitosa: {len(paginas)} página(s)")
    
    # Verificar dimensiones
    for i, pagina in enumerate(paginas):
        print(f"  Página {i+1}: {pagina.size[0]}x{pagina.size[1]} píxeles")
        
        # Guardar una copia para inspección visual
        salida = f"debug_page_{i+1}.png"
        pagina.save(salida)
        print(f"  Guardado en: {salida}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
