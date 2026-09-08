import re
import unicodedata

try:
    import pytesseract
    # --- CONFIGURAR LA RUTA DEL EJECUTABLE DE TESSERACT ---
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # -------------------------------------------------------
except ImportError:  # pragma: no cover - entorno sin dependencia OCR
    pytesseract = None

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover - entorno sin dependencia OCR
    convert_from_path = None

# Intentar detectar poppler automáticamente
POPPLER_PATH = None
try:
    # Intentar rutas comunes en Windows
    import os
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
except Exception:
    pass

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - entorno sin dependencia OCR
    Image = None
    ImageOps = None


OCR_LANGUAGES = ('spa+eng', 'eng', None)

ENERGY_CONTEXT = {
    'energia', 'electrica', 'electricidad', 'consumo', 'kwh', 'kw/h',
    'facturada', 'medidor', 'lectura', 'enel', 'cge', 'chilquinta',
    'saesa', 'frontel', 'luz',
}
FUEL_CONTEXT = {
    'combustible', 'litro', 'litros', 'lts', 'bencina', 'gasolina',
    'diesel', 'petroleo', 'volumen', 'carga', 'copec', 'shell',
    'petrobras', 'estacion', 'servicio',
}
MONEY_CONTEXT = {
    '$', 'total a pagar', 'monto', 'neto', 'iva', 'subtotal', 'clp',
    'pesos', 'precio', 'valor total', 'total boleta',
}


def procesar_archivo(ruta_archivo):
    if pytesseract is None:
        return ""

    if ruta_archivo.lower().endswith('.pdf'):
        if convert_from_path is None:
            return ""
        try:
            # Aumentar DPI para mejor OCR
            kwargs = {'dpi': 300}
            if POPPLER_PATH:
                kwargs['poppler_path'] = POPPLER_PATH
            paginas = convert_from_path(ruta_archivo, **kwargs)
            textos = []
            for pagina in paginas:
                texto = _ocr_imagen(pagina)
                if texto.strip():
                    textos.append(texto)
            return "\n".join(textos)
        except Exception as e:
            # Registrar el error pero no fallar completamente
            return ""

    if Image is None:
        return ""

    try:
        with Image.open(ruta_archivo) as imagen:
            return _ocr_imagen(imagen)
    except Exception as e:
        # Registrar el error pero no fallar completamente
        return ""


def _ocr_imagen(imagen):
    if pytesseract is None:
        return ""
    
    ultimo_error = None
    
    # Intenta diferentes estrategias de preprocesamiento
    estrategias = [
        (_preparar_imagen(imagen), 'preprocesado estándar'),
        (_preparar_imagen_agresiva(imagen), 'preprocesado agresivo'),
        (imagen, 'sin preprocesamiento'),
    ]
    
    for imagen_procesada, nombre_estrategia in estrategias:
        for idioma in OCR_LANGUAGES:
            try:
                kwargs = {'config': '--psm 6'}
                if idioma:
                    kwargs['lang'] = idioma
                texto = pytesseract.image_to_string(imagen_procesada, **kwargs)
                if texto.strip():
                    return texto
            except Exception as exc:
                ultimo_error = exc
    
    return ""


def _preparar_imagen_agresiva(imagen):
    """Preprocesamiento más agresivo para imágenes de baja calidad."""
    if ImageOps is None:
        return imagen

    try:
        imagen = ImageOps.exif_transpose(imagen)
        imagen = imagen.convert('L')
        # Aumentar contraste más agresivamente
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(imagen)
        imagen = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Sharpness(imagen)
        imagen = enhancer.enhance(2.0)
        imagen = ImageOps.autocontrast(imagen, cutoff=5)
    except Exception:
        return imagen

    return imagen


def _preparar_imagen(imagen):
    if ImageOps is None:
        return imagen

    try:
        imagen = ImageOps.exif_transpose(imagen)
        imagen = imagen.convert('L')
        imagen = ImageOps.autocontrast(imagen)
    except Exception:
        return imagen

    return imagen


def _normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto or '')
    texto = ''.join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = texto.lower()
    # Normalizar variantes de kWh y litros
    texto = texto.replace('kw h', 'kwh').replace('k w h', 'kwh')
    texto = texto.replace('kw-h', 'kwh').replace('kw/h', 'kwh')
    texto = texto.replace('k.w.h', 'kwh').replace('k.w', 'kw')
    texto = texto.replace('lts.', 'lts').replace('lt.', 'lt')
    texto = texto.replace('l.', 'l ').replace('lts ', 'lts ')
    # Normalizar espacios múltiples
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto


def _normalizar_numero(valor):
    """
    Normaliza números con diferentes formatos.
    En contexto COPEC (facturas de energía/combustible):
    - Punto (.) = separador de miles
    - Coma (,) = separador decimal
    - Última posición es siempre decimal si hay ambos
    
    Ejemplos:
    - "380,445" => 380.445
    - "1.944,202" => 1944.202
    - "8084,84" => 8084.84
    - "5.522,53" => 5522.53
    - "1,234.56" => 1234.56 (formato USA raro, pero manejado)
    """
    if valor is None:
        return None

    texto = str(valor).strip().replace(' ', '')
    
    # Si no hay separadores, es un número simple
    if ',' not in texto and '.' not in texto:
        try:
            return float(texto)
        except (ValueError, TypeError):
            return None
    
    # Contar separadores
    num_comas = texto.count(',')
    num_puntos = texto.count('.')
    
    # ESTRATEGIA: Si hay ambos separadores, el ÚLTIMO es decimal
    if num_comas > 0 and num_puntos > 0:
        pos_ultima_coma = texto.rfind(',')
        pos_ultimo_punto = texto.rfind('.')
        
        if pos_ultima_coma > pos_ultimo_punto:
            # Coma es última => formato europeo: 1.234,56
            # Remover puntos, cambiar coma por punto
            texto = texto.replace('.', '').replace(',', '.')
        else:
            # Punto es última => formato USA: 1,234.56
            # Remover comas
            texto = texto.replace(',', '')
    # Solo comas => coma es decimal
    elif num_comas > 0:
        texto = texto.replace(',', '.')
    # Solo puntos => punto es separador de miles (contexto europeo)
    elif num_puntos > 0:
        texto = texto.replace('.', '')
    
    try:
        return float(texto)
    except ValueError:
        return None


def _lineas_con_contexto(texto):
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    ventanas = []
    for indice, linea in enumerate(lineas):
        anterior = lineas[indice - 1] if indice > 0 else ''
        siguiente = lineas[indice + 1] if indice + 1 < len(lineas) else ''
        ventanas.append((linea, f'{anterior} {linea} {siguiente}'.strip()))
    return ventanas or [(texto, texto)]


def _puntuar_contexto(texto, palabras):
    return sum(1 for palabra in palabras if palabra in texto)


def _parece_monto_dinero(texto):
    return any(indicador in texto for indicador in MONEY_CONTEXT)


def _mejor_candidato(candidatos):
    candidatos_validos = [candidato for candidato in candidatos if candidato['valor'] is not None]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=lambda candidato: (candidato['puntaje'], -candidato['orden']))


def _extraer_energia(texto):
    candidatos = []
    
    # ESTRATEGIA 1: Buscar líneas con contexto energético
    lineas = texto.split('\n')
    total_energia = 0.0
    encontrados_energia = []
    
    for linea in lineas:
        # Detectar si la línea contiene contexto de energía
        tiene_energia = any(prod in linea.lower() for prod in [
            'energia', 'electrica', 'kwh', 'kw/h', 'consumo electrico', 'facturada'
        ])
        
        if tiene_energia and any(kwh in linea.lower() for kwh in ['kwh', 'kw']):
            # Buscar números seguidos de kWh/kwh
            patron = r'(\d{1,6}(?:[\.,]\d{1,3})?)\s*(?:kwh|kw/h|kw\.h|kw\s*h)\b'
            matches = re.findall(patron, linea, flags=re.IGNORECASE)
            
            for match in matches:
                valor = _normalizar_numero(match)
                if valor and 0 < valor < 500000:  # Rango realista para kWh
                    encontrados_energia.append(valor)
                    total_energia += valor
    
    # Si encontramos líneas de energía, devolver el total
    if total_energia > 0:
        return total_energia
    
    # ESTRATEGIA 2: Patrones generales si la búsqueda específica falla
    patrones = [
        # Patrones muy explícitos que evitan falsos positivos
        r"(?P<valor>\d{1,6}(?:[\.,]\d{1,3})?)\s*(?:kwh|kw/h|kw\.h|kw\s*h)\b",
        r"(?:energia\s+(?:facturada|consumida|total|neta|electrica))\D{0,25}(?P<valor>\d{1,6}(?:[\.,]\d{1,3})?)",
        r"(?:consumo\s+(?:energetico|total|electrico|de\s+energia))\D{0,25}(?P<valor>\d{1,6}(?:[\.,]\d{1,3})?)",
        r"(?:medicion|lectura|actual|facturado)\s*\D{0,20}(?P<valor>\d{1,6}(?:[\.,]\d{1,3})?)\s*(?:kwh|kw/h)",
        r"(?:kwh|kw/h)\s*(?:facturados?|consumidos?|totales?)\D{0,15}(?P<valor>\d{1,6}(?:[\.,]\d{1,3})?)",
    ]

    for orden, (linea, contexto) in enumerate(_lineas_con_contexto(texto)):
        for patron in patrones:
            for match in re.finditer(patron, linea, flags=re.IGNORECASE):
                valor_str = match.group('valor')
                valor = _normalizar_numero(valor_str)
                if valor is None:
                    continue
                
                # Calcular puntaje
                puntaje = 10  # Base mayor para energía
                puntaje += _puntuar_contexto(contexto, ENERGY_CONTEXT) * 2
                
                # Bonus fuerte si aparece explícitamente kWh
                if re.search(r"kwh|kw/h|kw\.h|kw\s*h", linea, flags=re.IGNORECASE):
                    puntaje += 20
                
                # Penalidad si está en contexto de dinero y NO tiene kWh
                if _parece_monto_dinero(contexto) and not re.search(r"kwh|kw/h", linea, flags=re.IGNORECASE):
                    puntaje -= 30
                
                # Penalidad si está en contexto de números de identificación
                if re.search(r"r\.?u\.?t\.?|rut|n°|numero|nro", linea, flags=re.IGNORECASE):
                    puntaje -= 40
                
                # Rango válido para kWh
                if 0 < valor < 500000:
                    candidatos.append({'valor': valor, 'puntaje': puntaje, 'orden': orden})

    mejor = _mejor_candidato(candidatos)
    return mejor['valor'] if mejor else None


def _extraer_combustible(texto):
    candidatos = []
    
    # ESTRATEGIA 1: Buscar líneas con "PETROLEO DIESEL", "BENCINA", "GASOLINA", etc.
    # y extraer el primer número seguido de "L" (litros)
    lineas = texto.split('\n')
    total_litros = 0.0
    encontrados_combustibles = []
    
    for linea in lineas:
        # Detectar si la línea contiene un producto combustible
        tiene_combustible = any(prod in linea.lower() for prod in [
            'petroleo', 'diesel', 'bencina', 'gasolina', 'combustible'
        ])
        
        if tiene_combustible:
            # Buscar TODOS los números seguidos de "L" en esta línea
            # Patrón: captura números como "1.944,202" o "380,445"
            patron = r'(\d{1,2}\.\d{3}(?:[\.,]\d{1,3})?|\d{1,5}(?:[\.,]\d{1,3})?)\s*l\b'
            matches = re.findall(patron, linea, flags=re.IGNORECASE)
            
            for match in matches:
                valor = _normalizar_numero(match)
                if valor and 0 < valor < 50000:  # Rango realista para litros
                    encontrados_combustibles.append(valor)
                    total_litros += valor
    
    # Si encontramos líneas de combustible, devolver el total
    if total_litros > 0:
        return total_litros
    
    # ESTRATEGIA 2: Si no encontramos con la búsqueda específica, usar patrones generales
    patrones = [
        # Patrones muy específicos
        r"(?P<valor>\d{1,2}\.\d{3}(?:[\.,]\d{1,3})?|\d{1,5}(?:[\.,]\d{1,3})?)\s*(?:litros?|lts?|lt\.?|l\b)",
        r"(?:volumen|despacho|venta|cantidad|carga)\s*(?:de\s+)?(?:combustible|bencina|gasolina|diesel|petroleo)\D{0,25}(?P<valor>\d{1,5}(?:[\.,]\d{1,3})?)",
        r"(?:combustible|bencina|gasolina|diesel|petroleo)\D{0,25}(?P<valor>\d{1,5}(?:[\.,]\d{1,3})?)\s*(?:litros?|lts?|lt)",
        r"(?:total|subtotal|volumen|cantidad|litros?)\D{0,25}(?P<valor>\d{1,5}(?:[\.,]\d{1,3})?)\s*(?:litros?|lts?)",
    ]

    for orden, (linea, contexto) in enumerate(_lineas_con_contexto(texto)):
        for patron in patrones:
            for match in re.finditer(patron, linea, flags=re.IGNORECASE):
                valor_str = match.group('valor')
                valor = _normalizar_numero(valor_str)
                if valor is None:
                    continue
                
                # Calcular puntaje
                puntaje = 5
                puntaje += _puntuar_contexto(contexto, FUEL_CONTEXT) * 2
                
                # Bonus si aparece explícitamente litros
                if re.search(r"\b(?:litros?|lts?|lt\.?|l\b)", linea, flags=re.IGNORECASE):
                    puntaje += 15
                
                # Penalidad si está en contexto de dinero
                if _parece_monto_dinero(contexto) and not re.search(r"\b(?:litros?|lts?|lt\.?)\b", linea, flags=re.IGNORECASE):
                    puntaje -= 25
                
                # Rango válido
                if 0 < valor < 50000:
                    candidatos.append({'valor': valor, 'puntaje': puntaje, 'orden': orden})

    mejor = _mejor_candidato(candidatos)
    return mejor['valor'] if mejor else None


def _extraer_monto(texto):
    candidatos = []
    patrones = [
        # Patrones de alta especificidad primero
        r"(?:total\s+a\s+pagar|total\s+boleta|valor\s+total)\D*?(?P<valor>[\d\.,]+)",
        r"(?:\$|clp)\s*(?P<valor>[\d\.,]+)",
        # Patrón más general, se usará con menor puntaje
        r"(?P<valor>[\d\.,]{3,})", # Mínimo 3 caracteres para ser un monto
    ]

    for orden, (linea, contexto) in enumerate(_lineas_con_contexto(texto)):
        for i, patron in enumerate(patrones):
            for match in re.finditer(patron, linea, flags=re.IGNORECASE):
                valor_str = match.group('valor')
                valor = _normalizar_numero(valor_str)
                if valor is None:
                    continue

                puntaje = 0
                
                # Puntaje base por especificidad del patrón
                if i == 0: puntaje += 40
                elif i == 1: puntaje += 20
                
                # Bonus por palabras clave de "TOTAL" en la línea específica
                if any(k in linea.lower() for k in ['total a pagar', 'total boleta', 'valor total']):
                    puntaje += 30
                # Penalización fuerte si la línea es claramente de un sub-item
                elif any(k in linea.lower() for k in ['subtotal', 'neto', 'iva', 'impuesto']):
                    puntaje -= 50
                
                # Penalización por contexto de ID/RUT en la misma línea
                if re.search(r"rut|fono|cliente|nro|id|medidor|factura", linea, flags=re.IGNORECASE):
                    puntaje -= 40
                
                # Rango válido para un monto de boleta en CLP
                if 1000 <= valor <= 2000000:
                    candidatos.append({'valor': valor, 'puntaje': puntaje, 'orden': orden})

    if not candidatos:
        return None

    # Filtrar candidatos con puntaje negativo si hay positivos
    positivos = [c for c in candidatos if c['puntaje'] > 0]
    if positivos:
        mejor = _mejor_candidato(positivos)
        return mejor['valor'] if mejor else None
    
    mejor = _mejor_candidato(candidatos)
    return mejor['valor'] if mejor else None


def _extraer_periodo(texto):
    meses = (
        "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
        "octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|"
        "january|february|march|april|may|june|july|august|september|october|november|december|"
        "jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec"
    )
    patrones = [
        # Período con palabra clave y formato mes-año o día-mes-año
        rf"(?:periodo|fecha|emision|referencia|factura|vencimiento|lectura)\s*(?:del?|de\s+)?(?:\s*:)?\s*(?P<periodo>\d{{1,2}}[-/](?:{meses})[-/]\d{{4}})",
        # Período mes escrito + año
        rf"(?:periodo|fecha|emision|referencia|factura|vencimiento|lectura)\s*(?:del?|de\s+)?(?:\s*:)?\s*(?P<periodo>(?:{meses})\s+\d{{4}})",
        # Período aislado en formato día-mes-año
        rf"\b(?P<periodo>\d{{1,2}}[-/](?:{meses})[-/]\d{{4}})\b",
        # Período en formato numérico: YYYY-MM o YYYY/MM o MM/YYYY o MM-YYYY
        r"(?:periodo|fecha|emision|referencia|factura|vencimiento|lectura)\s*(?::)?\s*(?P<periodo>\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?|\d{1,2}[-/]\d{4})",
        # Período mes escrito standalone
        rf"\b(?P<periodo>(?:{meses})\s+\d{{4}})\b",
        # Período en formato numérico standalone
        r"\b(?P<periodo>\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?|\d{1,2}[-/]\d{4})\b",
    ]

    for patron in patrones:
        match = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
        if match:
            periodo = match.group('periodo').strip()
            
            # Si el período es numérico con separadores (YYYY-MM, MM/YYYY, etc)
            # devolverlo tal cual sin normalizar
            if re.match(r'^\d{1,4}[-/]\d{1,4}(?:[-/]\d{1,4})?$', periodo):
                return periodo
            
            # Si contiene nombres de mes, normalizar el formato
            if re.search(rf"(?:{meses})", periodo, flags=re.IGNORECASE):
                # Reemplazar separadores por espacios para formato "mes año"
                periodo = re.sub(r'[-/]', ' ', periodo)
                return periodo
            
            return periodo
    
    return None


def _detectar_tipo(texto, energia, combustible):
    puntaje_electricidad = _puntuar_contexto(texto, ENERGY_CONTEXT)
    puntaje_combustible = _puntuar_contexto(texto, FUEL_CONTEXT)

    # Bonus por detección de valores
    if energia is not None:
        puntaje_electricidad += 10
    if combustible is not None:
        puntaje_combustible += 10

    # Umbral mínimo para considerarse detectado
    diferencia = abs(puntaje_electricidad - puntaje_combustible)
    
    # Si ambos tienen puntaje alto y son similares, es mixto
    if puntaje_electricidad >= 10 and puntaje_combustible >= 10 and diferencia <= 5:
        return 'mixto'
    if puntaje_electricidad > puntaje_combustible and puntaje_electricidad >= 5:
        return 'electricidad'
    if puntaje_combustible > puntaje_electricidad and puntaje_combustible >= 5:
        return 'combustible'
    return 'desconocido'


def _calcular_confianza(tipo_detectado, energia, combustible, periodo, total):
    puntaje = 0.0
    if tipo_detectado != 'desconocido':
        puntaje += 0.20
    if energia is not None:
        puntaje += 0.25
    if combustible is not None:
        puntaje += 0.25
    if periodo:
        puntaje += 0.10
    if total is not None:
        puntaje += 0.20
    return min(round(puntaje, 2), 1.0)


def _respuesta_vacia(mensaje):
    return {
        "procesado": False,
        "tipo_detectado": "desconocido",
        "confianza": 0,
        "valor_extraido": {
            "energia_kwh": None,
            "combustible_litros": None,
            "periodo": None,
            "tipo_detectado": "desconocido",
            # Campos para futura extracción con LLM
            "proveedor": None,
            "neto": None,
            "iva": None,
            "impuesto_especifico": None,
            "total": None,
            "campos_detectados": [],
            "confianza": 0,
        },
        "mensaje": mensaje,
    }


def extraer_valor_boleta(ruta_archivo):
    # Verificar dependencias
    si_falta_tesseract = pytesseract is None
    si_falta_poppler = convert_from_path is None and ruta_archivo.lower().endswith('.pdf')
    
    texto_original = procesar_archivo(ruta_archivo)
    texto_limpio = _normalizar_texto(texto_original).strip()

    if not texto_limpio:
        msg_error = "No se pudo leer el contenido del archivo."
        if si_falta_tesseract:
            msg_error += " Tesseract-OCR no está instalado."
        elif si_falta_poppler:
            msg_error += " Poppler no está instalado (requerido para PDF)."
        else:
            msg_error += " El archivo podría estar vacío, corrupto o contener solo imágenes de muy baja calidad."
        return _respuesta_vacia(msg_error)

    energia = _extraer_energia(texto_limpio)
    combustible = _extraer_combustible(texto_limpio)
    periodo = _extraer_periodo(texto_limpio)
    total = _extraer_monto(texto_limpio)
    
    # Redondear valores a 2 decimales si existen
    if energia is not None:
        energia = round(energia, 2)
    if combustible is not None:
        combustible = round(combustible, 2)
    if total is not None:
        total = round(total, 2)
    
    tipo_detectado = _detectar_tipo(texto_limpio, energia, combustible)
    confianza = _calcular_confianza(tipo_detectado, energia, combustible, periodo, total)

    campos_detectados = []
    if energia is not None:
        campos_detectados.append('energia_kwh')
    if combustible is not None:
        campos_detectados.append('combustible_litros')
    if periodo:
        campos_detectados.append('periodo')
    if total is not None:
        campos_detectados.append('total')

    procesado = bool(campos_detectados)
    
    if procesado:
        mensaje = f"Extracción completada. Tipo: {tipo_detectado}. Confianza: {confianza:.0%}."
    else:
        mensaje = (
            "Advertencia: Se leyó el archivo pero no se identificaron valores claros. "
            "Verifica la calidad del escaneo o el formato del documento."
        )

    return {
        "procesado": procesado,
        "tipo_detectado": tipo_detectado,
        "confianza": confianza,
        "valor_extraido": {
            "energia_kwh": energia,
            "combustible_litros": combustible,
            "periodo": periodo,
            # --- CAMPOS PARA FUTURA EXTRACCIÓN CON LLM ---
            "proveedor": None,  # TODO: Implementar clasificador de proveedor
            "neto": None,
            "iva": None,
            "impuesto_especifico": None,
            "total": total,
            "tipo_detectado": tipo_detectado,
            "campos_detectados": campos_detectados,
            "confianza": confianza,
        },
        "mensaje": mensaje,
    }
