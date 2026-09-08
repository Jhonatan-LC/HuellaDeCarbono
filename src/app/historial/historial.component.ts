import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { BaseChartDirective, provideCharts, withDefaultRegisterables } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { TopbarComponent } from '../shared/topbar.component';

interface HistorialItem {
  id: string;
  archivo_url: string | null;
  periodo_referencia: string;
  procesado: boolean;
  valor_extraido: { energia_kwh: number | null; combustible_litros: number | null; periodo: string | null };
  estado: string;
  creado_en: string;
}

interface MonthlySummary {
  month: string;
  energia: number;
  combustible: number;
}

const COLOR_PRIMARY = '#1f5c4b';
const COLOR_MUTED = '#64748b';
const COLOR_LINE = '#e2e8f0';

@Component({
  selector: 'app-historial',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective, TopbarComponent],
  providers: [provideCharts(withDefaultRegisterables())],
  template: `
    <app-topbar></app-topbar>

    <div class="history-shell">
      <div class="page-heading">
        <div>
          <p class="eyebrow">Seguimiento</p>
          <h1>Historial de boletas</h1>
          <p class="subtitle">Revisa tus registros, ajusta los valores extraídos y observa la evolución mensual de tu huella de carbono.</p>
        </div>
        <span class="badge badge-success">{{ items.length }} registros</span>
      </div>

      <section class="stats-grid" *ngIf="items.length; else emptyState">
        <article class="card stat-card">
          <span>Total de boletas</span>
          <strong>{{ items.length }}</strong>
        </article>
        <article class="card stat-card stat-card-accent">
          <span>Procesadas</span>
          <strong>{{ processedCount }}</strong>
        </article>
        <article class="card stat-card stat-card-warning">
          <span>En revisión</span>
          <strong>{{ pendingCount }}</strong>
        </article>
      </section>

      <section class="charts-container" *ngIf="(chartData.labels?.length ?? 0) > 0">
        <article class="card chart-card">
          <div class="card-header">
            <div>
              <h3>Evolución de energía eléctrica</h3>
              <p class="chart-subtitle">Consumo mensual en kWh</p>
            </div>
            <div class="chart-meta">
              <span class="badge-unit">kWh</span>
              <span class="chart-avg">Prom: {{ avgEnergia.toFixed(1) }}</span>
            </div>
          </div>
          <div class="chart-wrapper">
            <canvas baseChart
              [data]="chartData"
              [options]="energyChartOptions"
              [type]="'line'">
            </canvas>
          </div>
          <div class="chart-footer">
            <span>Último valor: {{ lastEnergia.toFixed(1) }} kWh</span>
          </div>
        </article>

        <article class="card chart-card">
          <div class="card-header">
            <div>
              <h3>Evolución de combustible</h3>
              <p class="chart-subtitle">Consumo mensual en litros</p>
            </div>
            <div class="chart-meta">
              <span class="badge-unit">L</span>
              <span class="chart-avg">Prom: {{ avgCombustible.toFixed(1) }}</span>
            </div>
          </div>
          <div class="chart-wrapper">
            <canvas baseChart
              [data]="fuelChartData"
              [options]="fuelChartOptions"
              [type]="'line'">
            </canvas>
          </div>
          <div class="chart-footer">
            <span>Último valor: {{ lastCombustible.toFixed(1) }} L</span>
          </div>
        </article>
      </section>

      <section class="card table-card">
        <div class="card-header">
          <div>
            <h3>Boletas recientes</h3>
            <p class="chart-subtitle">Ajusta los valores si la extracción OCR no fue precisa</p>
          </div>
        </div>

        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Periodo</th>
                <th>Estado</th>
                <th>Energía</th>
                <th>Combustible</th>
                <th>Archivo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let item of items">
                <td class="period-cell">{{ item.periodo_referencia || item.valor_extraido.periodo || 'Sin periodo' }}</td>
                <td>
                  <span class="badge" [class.badge-success]="item.procesado" [class.badge-warning]="!item.procesado">
                    {{ item.procesado ? 'Procesado' : 'Pendiente' }}
                  </span>
                </td>
                <td class="number-cell">{{ formatValue(item.valor_extraido.energia_kwh) }} <span class="unit">kWh</span></td>
                <td class="number-cell">{{ formatValue(item.valor_extraido.combustible_litros) }} <span class="unit">L</span></td>
                <td>
                  <a *ngIf="item.archivo_url; else manualRecord" [href]="item.archivo_url" target="_blank" rel="noopener noreferrer" class="link-file">Ver archivo</a>
                  <ng-template #manualRecord><span class="unit">Manual</span></ng-template>
                </td>
                <td>
                  <button class="btn btn-secondary btn-sm" type="button" (click)="abrirModal(item)">Editar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <ng-template #emptyState>
      <div class="history-shell">
        <div class="page-heading">
          <div>
            <p class="eyebrow">Seguimiento</p>
            <h1>Historial de boletas</h1>
          </div>
        </div>
        <div class="card empty-state">
          <p class="empty-text">Aún no hay boletas para mostrar.</p>
          <p class="empty-subtext">Sube tu primera boleta en la calculadora para comenzar.</p>
        </div>
      </div>
    </ng-template>

    <div class="modal-backdrop" *ngIf="selectedItem" (click)="cerrarModal()">
      <div class="card modal-card" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3>Editar valores de boleta</h3>
          <button type="button" class="btn-close" (click)="cerrarModal()" aria-label="Cerrar">×</button>
        </div>

        <div class="form-group">
          <label for="energia">Energía (kWh)</label>
          <input id="energia" type="number" step="0.01" [(ngModel)]="editedEnergia" />
        </div>

        <div class="form-group">
          <label for="combustible">Combustible (L)</label>
          <input id="combustible" type="number" step="0.01" [(ngModel)]="editedCombustible" />
        </div>

        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" (click)="cerrarModal()">Cancelar</button>
          <button type="button" class="btn btn-primary" (click)="guardarCorreccion()" [disabled]="saving">
            {{ saving ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .history-shell {
      width: min(1280px, calc(100% - 2rem));
      margin: 0 auto;
      display: grid;
      gap: 1.25rem;
      padding: 0 0 3rem;
    }

    .page-heading {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .page-heading h1 {
      font-size: 1.5rem;
      font-weight: 700;
      margin-top: 0.15rem;
    }

    .subtitle {
      color: var(--muted);
      margin-top: 0.5rem;
      line-height: 1.55;
      font-size: 0.92rem;
      max-width: 560px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
    }

    .stat-card {
      padding: 1.1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      border-left: 3px solid var(--line-strong);
    }

    .stat-card-accent {
      border-left-color: var(--primary);
    }

    .stat-card-warning {
      border-left-color: var(--warning);
    }

    .stat-card span {
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 600;
    }

    .stat-card strong {
      font-size: 1.6rem;
      color: var(--text);
      font-weight: 700;
    }

    .charts-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 1rem;
    }

    .chart-card {
      padding: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      padding: 1.25rem 1.25rem 0.5rem;
      flex-wrap: wrap;
    }

    .card-header h3 {
      font-size: 1rem;
      font-weight: 700;
    }

    .card-header > div:first-child {
      flex: 1;
    }

    .chart-subtitle {
      color: var(--muted);
      font-size: 0.85rem;
      margin-top: 0.2rem;
    }

    .chart-meta {
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    .badge-unit {
      background: var(--surface-soft);
      color: var(--muted);
      padding: 0.25rem 0.55rem;
      border-radius: var(--radius-sm);
      font-size: 0.75rem;
      font-weight: 700;
    }

    .chart-avg {
      font-size: 0.8rem;
      color: var(--muted);
    }

    .chart-wrapper {
      position: relative;
      height: 240px;
      padding: 0.5rem 1.25rem;
    }

    .chart-footer {
      padding: 0.65rem 1.25rem 1.1rem;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.82rem;
    }

    .period-cell {
      font-weight: 600;
      color: var(--text);
    }

    .number-cell {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .unit {
      color: var(--muted-soft);
      font-size: 0.82rem;
      margin-left: 0.2rem;
    }

    .link-file {
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
    }

    .link-file:hover {
      text-decoration: underline;
    }

    .btn-sm {
      min-height: 2.1rem;
      padding: 0.4rem 0.8rem;
      font-size: 0.82rem;
    }

    .empty-state {
      padding: 2.5rem;
      text-align: center;
    }

    .empty-text {
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.35rem;
    }

    .empty-subtext {
      color: var(--muted);
      font-size: 0.9rem;
    }

    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.5);
      display: grid;
      place-items: center;
      padding: 1rem;
      z-index: 20;
    }

    .modal-card {
      width: min(100%, 420px);
      padding: 1.75rem;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }

    .modal-header h3 {
      font-size: 1.1rem;
      font-weight: 700;
    }

    .btn-close {
      background: transparent;
      border: none;
      font-size: 1.4rem;
      color: var(--muted);
      cursor: pointer;
      line-height: 1;
      padding: 0.25rem;
    }

    .btn-close:hover {
      color: var(--text);
    }

    .form-group {
      display: grid;
      gap: 0.4rem;
      margin-bottom: 1rem;
    }

    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.65rem;
      margin-top: 1.25rem;
      padding-top: 1.25rem;
      border-top: 1px solid var(--line);
    }

    @media (max-width: 768px) {
      .page-heading {
        flex-direction: column;
      }
    }
  `]
})
export class HistorialComponent implements OnInit {
  items: HistorialItem[] = [];
  processedCount = 0;
  pendingCount = 0;
  selectedItem: HistorialItem | null = null;
  editedEnergia = '';
  editedCombustible = '';
  saving = false;
  avgEnergia = 0;
  avgCombustible = 0;
  lastEnergia = 0;
  lastCombustible = 0;

  chartData: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: []
  };

  fuelChartData: ChartConfiguration<'line'>['data'] = {
    labels: [],
    datasets: []
  };

  private readonly baseChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        padding: 10,
        cornerRadius: 6,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: COLOR_LINE },
        ticks: { color: COLOR_MUTED, font: { size: 11 } }
      },
      x: { grid: { display: false }, ticks: { color: COLOR_MUTED, font: { size: 11 } } }
    }
  };

  energyChartOptions = this.baseChartOptions;
  fuelChartOptions = this.baseChartOptions;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargar();
  }

  cargar() {
    this.http
      .get<{ results: HistorialItem[] }>('http://localhost:8000/api/boletas/historial/', {
        withCredentials: true
      })
      .subscribe({
        next: (response) => {
          this.items = response.results;
          this.processedCount = this.items.filter((item) => item.procesado).length;
          this.pendingCount = this.items.filter((item) => !item.procesado).length;
          this.actualizarGraficas();
        },
        error: () => {
          this.items = [];
          this.processedCount = 0;
          this.pendingCount = 0;
          this.actualizarGraficas();
        }
      });
  }

  abrirModal(item: HistorialItem) {
    this.selectedItem = item;
    this.editedEnergia = String(item.valor_extraido.energia_kwh ?? '');
    this.editedCombustible = String(item.valor_extraido.combustible_litros ?? '');
  }

  cerrarModal() {
    this.selectedItem = null;
    this.editedEnergia = '';
    this.editedCombustible = '';
  }

  guardarCorreccion() {
    if (!this.selectedItem) {
      return;
    }

    this.saving = true;
    const energia = Number(this.editedEnergia || 0);
    const combustible = Number(this.editedCombustible || 0);

    this.http
      .patch(
        `http://localhost:8000/api/boletas/${this.selectedItem.id}/corregir/`,
        { energia_kwh: energia, combustible_litros: combustible },
        { withCredentials: true }
      )
      .subscribe({
        next: () => {
          this.saving = false;
          this.cerrarModal();
          this.cargar();
        },
        error: () => {
          this.saving = false;
          alert('No se pudo guardar la corrección.');
        }
      });
  }

  formatValue(value: number | null) {
    return value === null || value === undefined ? '—' : value.toLocaleString('es-ES', { maximumFractionDigits: 2 });
  }

  private actualizarGraficas() {
    const monthly = this.agruparMensual();
    const energias = monthly.map((entry) => entry.energia);
    const combustibles = monthly.map((entry) => entry.combustible);

    this.avgEnergia = energias.length > 0 ? energias.reduce((a, b) => a + b, 0) / energias.length : 0;
    this.avgCombustible = combustibles.length > 0 ? combustibles.reduce((a, b) => a + b, 0) / combustibles.length : 0;
    this.lastEnergia = energias.length > 0 ? energias[energias.length - 1] : 0;
    this.lastCombustible = combustibles.length > 0 ? combustibles[combustibles.length - 1] : 0;

    this.chartData = {
      labels: monthly.map((entry) => this.formatearMes(entry.month)),
      datasets: [
        {
          label: 'Energía (kWh)',
          data: energias,
          borderColor: COLOR_PRIMARY,
          backgroundColor: 'rgba(31,92,75,0.1)',
          borderWidth: 2,
          pointBackgroundColor: COLOR_PRIMARY,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.35,
          fill: true
        }
      ]
    };

    this.fuelChartData = {
      labels: monthly.map((entry) => this.formatearMes(entry.month)),
      datasets: [
        {
          label: 'Combustible (L)',
          data: combustibles,
          borderColor: '#64748b',
          backgroundColor: 'rgba(100,116,139,0.1)',
          borderWidth: 2,
          pointBackgroundColor: '#64748b',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.35,
          fill: true
        }
      ]
    };
  }

  private agruparMensual(): MonthlySummary[] {
    const map = new Map<string, MonthlySummary>();

    this.items.forEach((item) => {
      const month = this.extraerMes(item);
      if (!month) {
        return;
      }

      const current = map.get(month) ?? { month, energia: 0, combustible: 0 };
      current.energia += Number(item.valor_extraido.energia_kwh ?? 0);
      current.combustible += Number(item.valor_extraido.combustible_litros ?? 0);
      map.set(month, current);
    });

    return Array.from(map.values()).sort((a, b) => a.month.localeCompare(b.month));
  }

  private extraerMes(item: HistorialItem): string | null {
    const source = item.periodo_referencia || item.valor_extraido.periodo || item.creado_en || '';
    const direct = source.match(/(\d{4})[-/](\d{1,2})/);
    if (direct) {
      return `${direct[1]}-${direct[2].padStart(2, '0')}`;
    }

    const date = new Date(source);
    if (!Number.isNaN(date.getTime())) {
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    }

    return null;
  }

  private formatearMes(month: string): string {
    const [year, monthNumber] = month.split('-').map(Number);
    const date = new Date(year, monthNumber - 1, 1);
    return date.toLocaleDateString('es-ES', { month: 'short', year: '2-digit' });
  }
}
