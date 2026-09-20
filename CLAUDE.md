# Huella de Carbono App — contexto del proyecto

Calculadora de huella de carbono (inventario GEI alineado a ISO 14064-1) que evoluciona de
"hogar individual" a multi-organización (miembros, sitios, roles). Base metodológica: herramienta
de inventario de SKIC (Alcance 1/2/3, factores DEFRA UK + IPCC AR5).

## Entorno de trabajo

- SO / ruta: Windows, `C:\Users\Jhonatan\huella-carbono-app`
- Frontend (raíz del repo): Angular 21.2 con SSR (`@angular/ssr`, Express 5, `outputMode: server`),
  builder `@angular/build:application`, TypeScript 5.9, RxJS 7.8, npm 10.9.3
- Gráficos: ECharts 6 (`ngx-echarts`) y Chart.js 4 (`ng2-charts`)
- Tests frontend: Vitest 4 vía `ng test` (`@angular/build:unit-test`), jsdom
- Móvil: Capacitor 8 (Android), carpeta `android/`
- Backend (`huella-carbono-backend/`): Django 6.0.6 + Django REST Framework + django-cors-headers,
  una sola app `auditoria`, entorno virtual en `huella-carbono-backend/venv`
- BD: SQLite (`db.sqlite3`) en desarrollo. Medios subidos en `media/` (boletas)
- Auth actual: sesiones de Django + CSRF + código de verificación por email (no JWT)
- Config por variables de entorno `DJANGO_*` (ver `.env.example`); en desarrollo el email sale por consola
- CORS/CSRF permitidos solo para `http://localhost:4200` y `127.0.0.1:4200`
- OCR de boletas: Tesseract (`auditoria/extractor.py`); ver `OCR_FIXES.md`
- CI: `.github/` solo contiene hooks de "modernize"; no hay workflows de CI/CD todavía

## Comandos

Frontend (desde la raíz):

    npm start            # ng serve en http://localhost:4200
    npm test             # ng test (Vitest)
    npm run build        # build de producción con SSR
    npm run serve:ssr:huella-carbono-app

Backend (desde `huella-carbono-backend/`, con el venv activado: `venv\Scripts\activate`):

    python manage.py runserver
    python manage.py migrate
    python manage.py test auditoria

## Modelo de dominio (backend, `auditoria/models.py`)

- Tenant: `Organizacion` (tipo `hogar`|`organizacion`) -> `Membresia` (roles `admin`|`miembro`) -> `Ubicacion` (sitio)
- Catálogo: `CategoriaEmision` (alcance 1/2/3) y `FactorEmision` versionado por vigencia con fuente citada
- Flujo de datos: `RegistroBoleta` (OCR/manual) -> `RegistroActividad` (dato crudo) -> `CalculoEmision`
  (cantidad x factor vigente; derivado, nunca se edita a mano)
- `CorreccionBoleta` guarda historial de correcciones manuales sobre lo extraído por OCR
- `organizaciones.organizacion_activa(usuario)` es el único punto que resuelve la organización activa

## Reglas del proyecto

- Toda consulta a datos de negocio debe filtrarse por la organización activa del usuario; nunca
  devolver querysets sin ese filtro (riesgo de fuga entre organizaciones)
- Los factores de emisión viven en la BD con vigencia y fuente; nunca hardcodearlos en el código
- Los cálculos son derivados y reproducibles; los históricos no deben cambiar al actualizar un factor
- Angular: componentes standalone, signals, control flow `@if/@for`, nada de `*ngIf`/NgModules nuevos;
  código compatible con SSR (no tocar `window`/`document` directamente sin guardas)
- Django/DRF: serializers explícitos, permisos por rol, `select_related`/`prefetch_related` en listados
- Cambios en permisos, querysets o modelos requieren tests (backend: `auditoria/tests.py`)
- Idioma del dominio y de la UI: español (nombres de modelos y campos en español)

## Skills recomendadas (verificadas el 2026-09-20)

- `angular/skills` (oficial, equipo de Angular): `npx skills add https://github.com/angular/skills`
  (`angular-developer`; `angular-new-app` no es necesaria porque el proyecto ya existe)
- `django-expert` de `Jeffallan/claude-skills` (Django + DRF; documentada para Django 5, este proyecto usa 6)
- Skills de ingeniería ya disponibles en Cowork: `engineering:system-design`, `code-review`,
  `testing-strategy`, `architecture`, `deploy-checklist`

## Pendiente / a definir

- Roles más finos que `admin`/`miembro` (por ejemplo editor de sitio, solo lectura, auditor)
- `organizacion` es nullable en `RegistroBoleta` y `RegistroActividad`: decidir si pasa a obligatoria
- Migrar de SQLite a PostgreSQL antes de producción
- Registro de auditoría (quién cambió qué y cuándo) más allá de `CorreccionBoleta`
