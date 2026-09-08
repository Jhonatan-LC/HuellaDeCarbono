# Solución: Problemas con Extracción de PDF e Imágenes (OCR)

## ¿Qué cambié en `extractor.py`?

### 1. **Arreglé la función `_ocr_imagen`** (línea ~71)
**Problema:** La función retornaba siempre `""` incluso cuando debería retornar el texto OCR

**Solución:** Ahora intenta cada idioma y retorna el primero que tenga éxito:
```python
for idioma in OCR_LANGUAGES:
    try:
        kwargs = {'config': '--psm 6'}
        if idioma:
            kwargs['lang'] = idioma
        texto = pytesseract.image_to_string(imagen, **kwargs)
        if texto.strip():
            return texto  # ✓ Retorna el texto si lo obtiene
    except Exception as exc:
        ultimo_error = exc

return ""  # Solo retorna vacío si ALL fallan
```

### 2. **Mejoré patrones de extracción**
- Agregué más variantes para energía: `kw.h`, `consumida`
- Agregué más variantes para combustible: `despacho`, `venta`
- Añadí búsqueda de contexto mejor: `lectura`, `referencia`
- Ahora busca con `re.IGNORECASE` para ser case-insensitive

### 3. **Mensajes de error más claros**
Si no se puede leer el archivo, ahora distingue entre:
- ✗ Tesseract no instalado
- ✗ Poppler no instalado (para PDF)
- ✗ Archivo corrupto/vacío

---

## Requisitos para que OCR funcione

### A. Python packages (ya instalados probablemente):
```bash
pip install pytesseract pdf2image Pillow
```

### B. **TESSERACT-OCR** (Software externo - CRÍTICO)
Sin esto NO funciona el OCR.

#### Windows:
1. Descarga el instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Instala en: `C:\Program Files\Tesseract-OCR`
3. Verifica que funciona:
   ```bash
   cd /c/"Program Files"/Tesseract-OCR
   ./tesseract.exe --version
   ```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install tesseract-ocr
```

#### macOS:
```bash
brew install tesseract
```

### C. **POPPLER** (Para PDF - Necesario si subes PDF)

#### Windows:
1. Descarga Release: https://github.com/oschwartz10612/poppler-windows/releases
2. Descomprime en: `C:\Program Files\poppler`
3. Añade a PATH o configura en Python

#### Linux:
```bash
sudo apt-get install poppler-utils
```

#### macOS:
```bash
brew install poppler
```

---

## Cómo verificar que todo funciona

### Opción 1: Ejecutar script de diagnóstico
```bash
cd huella-carbono-backend
python check_ocr_dependencies.py
```

Debería mostrar:
```
✓ pytesseract está instalado
✓ pdf2image está instalado
✓ Pillow (PIL) está instalada
✓ OCR funciona correctamente
```

### Opción 2: Test manual en Django
```bash
python manage.py shell
from auditoria.extractor import extraer_valor_boleta
resultado = extraer_valor_boleta('ruta/a/tu/boleta.pdf')
print(resultado)
```

---

## Qué esperar del OCR

| Tipo de archivo | Confianza esperada | Notas |
|---|---|---|
| PDF limpio (factura) | 70-90% | Mejor con facturas estándar |
| JPG/PNG de buena calidad | 60-80% | Depende de resolución |
| Foto borrosa | 20-40% | Intenta hacer zoom o mejorar imagen |
| Documento escaneado | 50-70% | A veces mejor que foto |

---

## ¿Qué hacer si aún no funciona?

1. **Verifica Tesseract:**
   ```powershell
   tesseract --version
   ```
   Si no existe comando, está mal instalado.

2. **Verifica idioma español:**
   ```powershell
   tesseract --list-langs
   ```
   Debería incluir `spa` (español).

3. **Si falta idioma español:**
   - En Windows: El instalador de Tesseract debería incluirlo
   - En Linux: `sudo apt-get install tesseract-ocr-spa`
   - En macOS: `brew install tesseract-ocr-spa`

4. **Prueba la extracción manualmente:**
   ```bash
   tesseract imagen.png stdout -l spa
   ```

---

## Cambios hechos en backend

```
✓ extractor.py - Mejoras en OCR y patrones
✓ check_ocr_dependencies.py - Script de diagnóstico nuevo
```

**No hay cambios en models.py, views.py o urls.py** - El API sigue igual, pero ahora retorna mejor información de diagnóstico.

---

## Resumen

**El OCR debería funcionar mejor ahora porque:**
1. ✓ Arreglé bug que siempre retornaba texto vacío
2. ✓ Mejoré patrones de búsqueda
3. ✓ Mejor manejo de errores
4. ✓ Mensajes de diagnóstico más claros

**Pero necesitas Tesseract + Poppler instalados en tu PC** para que funcione.
