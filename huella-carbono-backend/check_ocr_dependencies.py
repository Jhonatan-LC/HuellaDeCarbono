#!/usr/bin/env python
"""
Script de diagnóstico para verificar si las dependencias OCR están instaladas
correctamente y funcionan con archivos de prueba.
"""

import os
import sys

try:
    import pytesseract
    # --- CONFIGURAR LA RUTA DEL EJECUTABLE DE TESSERACT ---
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # -------------------------------------------------------
except ImportError:
    pytesseract = None

try:
    from pdf2image import convert_from_path
    # Detectar poppler automáticamente
    import os
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
except ImportError:
    convert_from_path = None
    POPPLER_PATH = None

def check_tesseract():
    """Verifica si pytesseract y tesseract están disponibles."""
    if pytesseract is None:
        print("✗ pytesseract no está instalado")
        print("  Instálalo con: pip install pytesseract")
        return False
    
    print("✓ pytesseract está instalado")
    
    # Intentar obtener la versión de Tesseract
    try:
        version = pytesseract.pytesseract.get_tesseract_version()
        print(f"  Versión de Tesseract: {version}")
        return True
    except Exception as e:
        print(f"✗ No se pudo determinar la versión de Tesseract: {e}")
        print("  Asegúrate de haber instalado el ejecutable de Tesseract-OCR")
        return False

def check_poppler():
    """Verifica si pdf2image y poppler están disponibles."""
    if convert_from_path is None:
        print("✗ pdf2image no está instalado")
        print("  Instálalo con: pip install pdf2image")
        print("  También necesitas descargar Poppler desde https://github.com/oschwartz10612/poppler-windows/releases/")
        return False
    
    print("✓ pdf2image está instalado")
    
    if POPPLER_PATH:
        print(f"✓ Poppler encontrado en: {POPPLER_PATH}")
        return True
    else:
        print("✗ Poppler no encontrado en las rutas comunes")
        print("  Descarga desde: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("  E instala en una de estas rutas:")
        print("    - C:\\Program Files\\poppler-26.02.0\\Library\\bin")
        print("    - C:\\Program Files\\poppler\\Library\\bin")
        print("    - C:\\Program Files (x86)\\poppler\\Library\\bin")
        print("    - C:\\tools\\poppler\\Library\\bin")
        return False

def check_pillow():
    """Verifica si PIL/Pillow está instalada."""
    try:
        from PIL import Image
        print("✓ Pillow (PIL) está instalada")
        return True
    except ImportError:
        print("✗ Pillow no está instalada")
        print("  Instálalo con: pip install Pillow")
        return False

def test_ocr_simple():
    """Intenta una extracción OCR simple."""
    try:
        import pytesseract
        from PIL import Image
        import numpy as np
        
        # Crear una imagen de prueba simple
        print("\nProbando OCR con imagen de prueba...")
        img = Image.new('RGB', (200, 100), color='white')
        
        # Intentar OCR
        try:
            texto = pytesseract.image_to_string(img, lang='spa+eng')
            print("✓ OCR funciona correctamente")
            return True
        except Exception as e:
            print(f"✗ Error en OCR: {e}")
            return False
    except Exception as e:
        print(f"✗ No se pudo probar OCR: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DIAGNÓSTICO DE DEPENDENCIAS OCR")
    print("=" * 60)
    
    results = {
        'Tesseract': check_tesseract(),
        'Poppler (PDF)': check_poppler(),
        'Pillow (Imágenes)': check_pillow(),
    }
    
    test_ocr_simple()
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print("=" * 60)
    
    for nombre, resultado in results.items():
        estado = "✓ OK" if resultado else "✗ FALTA"
        print(f"{nombre}: {estado}")
    
    if all(results.values()):
        print("\n✓ Todas las dependencias están correctamente instaladas")
        sys.exit(0)
    else:
        print("\n✗ Faltan dependencias. Revisa los mensajes arriba.")
        sys.exit(1)
