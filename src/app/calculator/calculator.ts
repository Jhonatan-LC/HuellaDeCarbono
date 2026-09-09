import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule, HttpErrorResponse } from '@angular/common/http';
import { TopbarComponent } from '../shared/topbar.component';

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
}

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [FormsModule, CommonModule, HttpClientModule, TopbarComponent],
  templateUrl: './calculator.html',
  styleUrl: './calculator.css'
})
export class Calculator implements OnInit {
  categoriasAlcance1: Categoria[] = [];
  categoriasAlcance2: Categoria[] = [];
  categoriasAlcance3: Categoria[] = [];
  cantidades: Record<string, number | null> = {};
  periodoManual: string = '';

  ultimoResultado: ActividadDetalle[] = [];
  huellaTotal: number = 0;

  selectedFile: File | null = null;
  periodo: string = '';
  uploadError: string | null = null;
  uploadInProgress = false;
  isSubiendo = false;
  isGuardando = false;
  historialBoletas: RegistroBoleta[] = [];
  saveMessage: string | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarCategorias();
    this.cargarHistorial();
  }

  calcularHuella() {
    this.guardarConsumoManual();
  }

  limpiarFormulario() {
    this.cantidades = {};
    this.ultimoResultado = [];
    this.huellaTotal = 0;
    this.saveMessage = null;
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
        values.push(`${codigo}: ${cantidad}`);
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

    this.http.post<RegistroBoleta>('http://localhost:8000/api/boletas/upload/', formData, { withCredentials: true })
      .subscribe({
        next: (response) => {
          alert('Boleta subida correctamente para auditoría');
          if (response) {
            this.historialBoletas.unshift(response);
          }
          this.isSubiendo = false;
          this.uploadInProgress = false;
          this.resetUpload();
          this.limpiarFormulario();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error', err);
          this.uploadError = 'No se pudo subir la boleta. Verifica la conexión o intenta de nuevo.';
          this.isSubiendo = false;
          this.uploadInProgress = false;
        }
      });
  }

  private cargarCategorias() {
    this.http.get<Categoria[]>('http://localhost:8000/api/categorias/', { withCredentials: true })
      .subscribe({
        next: (categorias) => {
          this.categoriasAlcance1 = categorias.filter((c) => c.alcance === 1);
          this.categoriasAlcance2 = categorias.filter((c) => c.alcance === 2);
          this.categoriasAlcance3 = categorias.filter((c) => c.alcance === 3);
        },
        error: () => {
          this.categoriasAlcance1 = [];
          this.categoriasAlcance2 = [];
          this.categoriasAlcance3 = [];
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
      'http://localhost:8000/api/consumos/registrar/',
      { periodo: this.periodoManual, actividades },
      { withCredentials: true }
    ).subscribe({
      next: (registro) => {
        this.isGuardando = false;
        this.historialBoletas.unshift(registro);
        this.ultimoResultado = registro.actividades_detalle || [];
        this.huellaTotal = registro.co2_total_kg || 0;
        this.saveMessage = 'Registro guardado en tu historial.';
        this.uploadError = null;
      },
      error: (err: HttpErrorResponse) => {
        this.isGuardando = false;
        this.saveMessage = null;
        this.uploadError = err.error?.detail || 'No se pudo guardar el cálculo en el backend.';
      }
    });
  }

  private cargarHistorial() {
    this.http.get<{ results: RegistroBoleta[] }>('http://localhost:8000/api/boletas/historial/', { withCredentials: true })
      .subscribe({
        next: (response) => {
          this.historialBoletas = response.results;
        },
        error: () => {
          this.historialBoletas = [];
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
