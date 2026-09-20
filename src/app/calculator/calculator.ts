import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { catchError, of } from 'rxjs';
import { TopbarComponent } from '../shared/topbar.component';
import { UbicacionSelectComponent } from '../shared/ubicacion-select/ubicacion-select.component';
import { CompactoKgCo2ePipe } from '../shared/compact-kg-co2e.pipe';
import { UiService } from '../shared/ui.service';
import { AnaliticaService } from '../analitica/analitica.service';
import { environment } from '../../environments/environment';

interface RegistroBoleta {
  id: string;
  fecha_subida: string;
  periodo_referencia: string;
  periodo?: string;
  archivo_url: string | null;
  valor_extraido: {
    energia_kwh?: number | null;
    combustible_litros?: number | null;
    actividades?: Record<string, number>;
    periodo: string | null;
  };
  estado: 'Procesado' | 'Pendiente' | 'Error';
  origen: 'Manual' | 'Boleta';
  co2_total_kg?: number;
  actividades_detalle?: ActividadDetalle[];
}

interface ActividadDetalle {
  categoria_codigo: string;
  categoria_nombre: string;
  alcance: number;
  cantidad: number;
  unidad: string;
  co2_kg: number;
}

interface Categoria {
  codigo: string;
  nombre: string;
  alcance: number;
  unidad_actividad: string;
  factor_vigente_kg_co2e: number | null;
}

interface Ubicacion {
  id: number;
  nombre: string;
  pais: string;
}

interface ComparativoMesAnterior {
  disponible: boolean;
  porcentaje: number;
}

/** Un icono barato (emoji) por familia de categoría — quita la sensación de formulario
 * administrativo sin necesitar una librería de iconos. */
function iconoPara(codigo: string): string {
  if (codigo.startsWith('agua_')) return '💧';
  if (codigo === 'electricidad') return '⚡';
  if (codigo.startsWith('combustible')) return '🔥';
  if (codigo.startsWith('residuos')) return '🗑️';
  return '🍃';
}

/** 'YYYY-MM' -> 'YYYY-MM' del mes anterior (mismo criterio que dashboard_views.py). */
function mesAnterior(periodo: string): string | null {
  const match = periodo.match(/^(\d{4})-(\d{2})$/);
  if (!match) return null;
  const anio = Number(match[1]);
  const mes = Number(match[2]);
  const fecha = new Date(Date.UTC(anio, mes - 1, 1));
  fecha.setUTCMonth(fecha.getUTCMonth() - 1);
  return `${fecha.getUTCFullYear()}-${String(fecha.getUTCMonth() + 1).padStart(2, '0')}`;
}

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [FormsModule, TopbarComponent, UbicacionSelectComponent, CompactoKgCo2ePipe, DecimalPipe],
  templateUrl: './calculator.html',
  styleUrl: './calculator.css'
})
export class Calculator implements OnInit {
  private readonly apiBaseUrl = environment.apiBaseUrl;

  categoriasAlcance1: Categoria[] = [];
  categoriasAlcance2: Categoria[] = [];
  categoriasAlcance3: Categoria[] = [];
  private categoriasPorCodigo = new Map<string, Categoria>();
  cantidades: Record<string, number | null> = {};
  periodoManual: string = '';

  // Alcance 3 colapsado por defecto: una lista de 31 campos abruma; 1 y 2 concentran la
  // mayoría de los casos de uso típicos (energía/combustible) y quedan abiertos.
  scopeExpandido: Record<1 | 2 | 3, boolean> = { 1: true, 2: true, 3: false };

  ubicaciones: Ubicacion[] = [];
  ubicacionSeleccionada: number | null = null;

  ultimoResultado: ActividadDetalle[] = [];
  huellaTotal: number = 0;
  comparativoMesAnterior: ComparativoMesAnterior | null = null;

  selectedFile: File | null = null;
  periodo: string = '';
  uploadError: string | null = null;
  uploadInProgress = false;
  isSubiendo = false;
  isGuardando = false;
  historialBoletas: RegistroBoleta[] = [];
  saveMessage: string | null = null;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private ui: UiService,
    private analiticaService: AnaliticaService,
  ) {}

  ngOnInit() {
    this.cargarCategorias();
    this.cargarHistorial();
    this.cargarUbicaciones();
  }

  calcularHuella() {
    this.guardarConsumoManual();
  }

  limpiarFormulario() {
    this.cantidades = {};
    this.ultimoResultado = [];
    this.huellaTotal = 0;
    this.comparativoMesAnterior = null;
    this.saveMessage = null;
  }

  icono(codigo: string): string {
    return iconoPara(codigo);
  }

  toggleScope(alcance: 1 | 2 | 3): void {
    this.scopeExpandido[alcance] = !this.scopeExpandido[alcance];
  }

  /** Estimado en vivo mientras se escribe (cantidad x factor vigente por categoría). Es una
   * previsualización client-side; el cálculo real y persistido lo sigue haciendo el backend
   * (emisiones.py::calcular_y_registrar) al guardar — ver Pendiente en CLAUDE.md sobre nunca
   * hardcodear factores: acá solo se multiplica por el factor que ya trajo /api/categorias/. */
  get estimadoKgCo2e(): number {
    let total = 0;
    for (const [codigo, cantidad] of Object.entries(this.cantidades)) {
      if (!cantidad || cantidad <= 0) continue;
      const factor = this.categoriasPorCodigo.get(codigo)?.factor_vigente_kg_co2e;
      if (factor) {
        total += cantidad * factor;
      }
    }
    return total;
  }

  get tieneEstimado(): boolean {
    return Object.values(this.cantidades).some((c) => !!c && c > 0);
  }

  formatValorExtraido(boleta: RegistroBoleta) {
    const energia = boleta.valor_extraido?.energia_kwh;
    const combustible = boleta.valor_extraido?.combustible_litros;
    const actividades = boleta.valor_extraido?.actividades;
    const values: string[] = [];

    if (energia !== null && energia !== undefined) {
      values.push(`${energia} kWh`);
    }

    if (combustible !== null && combustible !== undefined) {
      values.push(`${combustible} L`);
    }

    if (actividades) {
      for (const [codigo, cantidad] of Object.entries(actividades)) {
        const categoria = this.categoriasPorCodigo.get(codigo);
        const etiqueta = categoria?.nombre ?? codigo;
        const unidad = categoria?.unidad_actividad ?? '';
        values.push(`${etiqueta} · ${cantidad}${unidad ? ' ' + unidad : ''}`);
      }
    }

    return values.length > 0 ? values.join(' / ') : 'Sin datos';
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    if (!file) {
      this.selectedFile = null;
      this.uploadError = null;
      return;
    }

    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|png|jpe?g)$/i)) {
      this.selectedFile = null;
      this.uploadError = 'Solo se aceptan archivos PDF, JPG o PNG.';
      return;
    }

    this.selectedFile = file;
    this.uploadError = null;
  }

  uploadBoleta() {
    if (!this.selectedFile) {
      this.uploadError = 'Selecciona un archivo antes de subir.';
      return;
    }

    if (!this.periodo.trim()) {
      this.uploadError = 'Ingresa el periodo asociado a esta boleta.';
      return;
    }

    this.uploadInProgress = true;
    this.isSubiendo = true;
    this.uploadError = null;

    const formData = new FormData();
    formData.append('boleta', this.selectedFile);
    formData.append('periodo', this.periodo);
    if (this.ubicacionSeleccionada) {
      formData.append('ubicacion_id', String(this.ubicacionSeleccionada));
    }

    this.http.post<RegistroBoleta>(`${this.apiBaseUrl}/api/boletas/upload/`, formData, { withCredentials: true })
      .subscribe({
        next: (response) => {
          this.ui.showToast('Boleta subida correctamente para auditoría.');
          if (response) {
            this.historialBoletas.unshift(response);
          }
          this.isSubiendo = false;
          this.uploadInProgress = false;
          this.resetUpload();
          this.limpiarFormulario();
          this.cdr.markForCheck();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error', err);
          this.uploadError = 'No se pudo subir la boleta. Verifica la conexión o intenta de nuevo.';
          this.isSubiendo = false;
          this.uploadInProgress = false;
          this.cdr.markForCheck();
        }
      });
  }

  private cargarCategorias() {
    this.http.get<Categoria[]>(`${this.apiBaseUrl}/api/categorias/`, { withCredentials: true })
      .subscribe({
        next: (categorias) => {
          this.categoriasAlcance1 = categorias.filter((c) => c.alcance === 1);
          this.categoriasAlcance2 = categorias.filter((c) => c.alcance === 2);
          this.categoriasAlcance3 = categorias.filter((c) => c.alcance === 3);
          this.categoriasPorCodigo = new Map(categorias.map((c) => [c.codigo, c]));
          this.cdr.markForCheck();
        },
        error: () => {
          this.categoriasAlcance1 = [];
          this.categoriasAlcance2 = [];
          this.categoriasAlcance3 = [];
          this.cdr.markForCheck();
        }
      });
  }

  private guardarConsumoManual() {
    this.saveMessage = null;

    const actividades: Record<string, number> = {};
    for (const [codigo, cantidad] of Object.entries(this.cantidades)) {
      if (cantidad && cantidad > 0) {
        actividades[codigo] = cantidad;
      }
    }

    if (Object.keys(actividades).length === 0) {
      this.uploadError = 'Ingresa al menos un consumo mayor a cero.';
      return;
    }

    if (!this.periodoManual.trim()) {
      this.uploadError = 'Ingresa el periodo del cálculo para guardarlo en tu historial.';
      return;
    }

    this.isGuardando = true;
    this.http.post<RegistroBoleta>(
      `${this.apiBaseUrl}/api/consumos/registrar/`,
      { periodo: this.periodoManual, actividades, ubicacion_id: this.ubicacionSeleccionada },
      { withCredentials: true }
    ).subscribe({
      next: (registro) => {
        this.isGuardando = false;
        this.historialBoletas.unshift(registro);
        this.ultimoResultado = registro.actividades_detalle || [];
        this.huellaTotal = registro.co2_total_kg || 0;
        this.saveMessage = 'Registro guardado en tu historial.';
        this.uploadError = null;
        this.ui.showToast('Registro guardado en tu historial.');
        this.cargarComparativoMesAnterior(this.periodoManual, this.huellaTotal);
        this.cdr.markForCheck();
      },
      error: (err: HttpErrorResponse) => {
        this.isGuardando = false;
        this.saveMessage = null;
        this.uploadError = err.error?.detail || 'No se pudo guardar el cálculo en el backend.';
        this.cdr.markForCheck();
      }
    });
  }

  /** Tarjeta de resultado: además del total recién calculado, compara contra el mismo total
   * del mes anterior (tendencia_periodo ya lo trae calculado el backend — se reutiliza en vez
   * de duplicar la lógica de agregación acá). */
  private cargarComparativoMesAnterior(periodoActual: string, totalActual: number): void {
    const anterior = mesAnterior(periodoActual);
    if (!anterior) {
      this.comparativoMesAnterior = null;
      return;
    }

    this.analiticaService.getOverview().pipe(
      catchError(() => of(null))
    ).subscribe((overview) => {
      const totalAnterior = overview?.tendencia_periodo.find((p) => p.periodo === anterior)?.valor_kg_co2e;
      if (!totalAnterior || totalAnterior <= 0) {
        this.comparativoMesAnterior = null;
      } else {
        this.comparativoMesAnterior = {
          disponible: true,
          porcentaje: Math.round(((totalActual - totalAnterior) / totalAnterior) * 1000) / 10,
        };
      }
      this.cdr.markForCheck();
    });
  }

  private cargarUbicaciones() {
    this.http.get<Ubicacion[]>(`${this.apiBaseUrl}/api/ubicaciones/`, { withCredentials: true })
      .subscribe({
        next: (ubicaciones) => { this.ubicaciones = ubicaciones; this.cdr.markForCheck(); },
        error: () => { this.ubicaciones = []; this.cdr.markForCheck(); },
      });
  }

  private cargarHistorial() {
    this.http.get<{ results: RegistroBoleta[] }>(`${this.apiBaseUrl}/api/boletas/historial/`, { withCredentials: true })
      .subscribe({
        next: (response) => {
          this.historialBoletas = response.results;
          this.cdr.markForCheck();
        },
        error: () => {
          this.historialBoletas = [];
          this.cdr.markForCheck();
        }
      });
  }

  private resetUpload() {
    this.selectedFile = null;
    this.periodo = '';
    this.uploadInProgress = false;
    this.uploadError = null;
  }
}
