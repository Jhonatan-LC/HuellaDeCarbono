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
  valor_extraido: { energia_kwh: number | null; combustible_litros: number | null; periodo: string | null };
  estado: 'Procesado' | 'Pendiente' | 'Error';
  origen: 'Manual' | 'Boleta';
}

@Component({
  selector: 'app-calculator',
  standalone: true,
  imports: [FormsModule, CommonModule, HttpClientModule, TopbarComponent],
  templateUrl: './calculator.html',
  styleUrl: './calculator.css'
})
export class Calculator implements OnInit {
  consumoLuzKwh: number | null = null;
  consumoCombustibleLitros: number | null = null;
  periodoManual: string = '';

  huellaLuz: number = 0;
  huellaCombustible: number = 0;
  huellaTotal: number = 0;

  selectedFile: File | null = null;
  periodo: string = '';
  uploadError: string | null = null;
  uploadInProgress = false;
  isSubiendo = false;
  historialBoletas: RegistroBoleta[] = [];
  saveMessage: string | null = null;

  // kg CO2e por kWh — Chile 2024, energiaabierta.cl (debe coincidir con el factor 'electricidad' sembrado en el backend)
  readonly FACTOR_LUZ = 0.2021;
  // kg CO2 por litro de diésel (debe coincidir con el factor 'combustible' sembrado en el backend)
  readonly FACTOR_COMBUSTIBLE = 2.68;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarHistorial();
  }

  calcularHuella() {
    this.huellaLuz = (this.consumoLuzKwh || 0) * this.FACTOR_LUZ;
    this.huellaCombustible = (this.consumoCombustibleLitros || 0) * this.FACTOR_COMBUSTIBLE;
    this.huellaTotal = this.huellaLuz + this.huellaCombustible;
    this.guardarConsumoManual();
  }

  limpiarFormulario() {
    this.consumoLuzKwh = null;
    this.consumoCombustibleLitros = null;
    this.huellaLuz = 0;
    this.huellaCombustible = 0;
    this.huellaTotal = 0;
    this.saveMessage = null;
  }

  formatValorExtraido(boleta: RegistroBoleta) {
    const energia = boleta.valor_extraido?.energia_kwh;
    const combustible = boleta.valor_extraido?.combustible_litros;
    const values = [];

    if (energia !== null && energia !== undefined) {
      values.push(`${energia} kWh`);
    }

    if (combustible !== null && combustible !== undefined) {
      values.push(`${combustible} L`);
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
          console.log('Exito', response);
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

  private guardarConsumoManual() {
    this.saveMessage = null;

    if (this.huellaTotal <= 0) {
      this.uploadError = 'Ingresa al menos un consumo mayor a cero.';
      return;
    }

    if (!this.periodoManual.trim()) {
      this.uploadError = 'Ingresa el periodo del cálculo para guardarlo en tu historial.';
      return;
    }

    this.http.post<RegistroBoleta>(
      'http://localhost:8000/api/consumos/registrar/',
      {
        periodo: this.periodoManual,
        energia_kwh: this.consumoLuzKwh || 0,
        combustible_litros: this.consumoCombustibleLitros || 0,
      },
      { withCredentials: true }
    ).subscribe({
      next: (registro) => {
        this.historialBoletas.unshift(registro);
        this.saveMessage = 'Registro guardado en tu historial.';
        this.uploadError = null;
      },
      error: (err: HttpErrorResponse) => {
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
