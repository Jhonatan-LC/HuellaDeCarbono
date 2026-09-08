import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ChartType } from 'chart.js';
import { DashboardService, DashboardKpis, CarbonFootprintData } from './dashboard.service';
import { Observable, catchError, of } from 'rxjs';
import { TopbarComponent } from '../shared/topbar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective, TopbarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  providers: [DashboardService],
})
export class DashboardComponent implements OnInit {
  public kpis$!: Observable<DashboardKpis>;
  public currentYear: number = new Date().getFullYear();
  public error: string | null = null;

  public barChartOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        padding: 10,
        cornerRadius: 6,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#e2e8f0' },
        ticks: { color: '#64748b' },
      },
      x: {
        grid: { display: false },
        ticks: { color: '#64748b' },
      },
    },
  };
  public barChartType: ChartType = 'bar';
  public barChartLegend = false;
  public barChartData: ChartConfiguration['data'] = {
    labels: [],
    datasets: [{
      data: [],
      label: 'Huella de Carbono (kg CO2e)',
      backgroundColor: '#1f5c4b',
      borderRadius: 4,
      maxBarThickness: 48,
    }]
  };

  // KPIs vacíos como fallback mientras no hay datos
  private emptyKpis: DashboardKpis = {
    gasto_mes_actual: { monto_clp: null, periodo: '', desglose: {} },
    racha_meses: { cantidad: 0, activa: false },
    alerta_anomalia: { detectada: false, mensaje: 'Sin datos' },
    comparativa_anual: { disponible: false },
  }

  constructor(private dashboardService: DashboardService) {}

  ngOnInit(): void {
    // Captura errores para no dejar el skeleton infinito
    this.kpis$ = this.dashboardService.getKpis().pipe(
      catchError((err) => {
        console.error('Error cargando KPIs:', err)
        this.error = `Error al cargar datos: ${err.status} ${err.statusText}`
        return of(this.emptyKpis)
      })
    );

    this.dashboardService.getCarbonFootprint().pipe(
      catchError((err) => {
        console.error('Error cargando gráfico:', err)
        return of([])
      })
    ).subscribe((data: CarbonFootprintData[]) => {
      this.barChartData = {
        labels: data.map(d => d.name),
        datasets: [{
          data: data.map(d => d.value),
          label: 'Huella de Carbono (kg CO2e)',
          backgroundColor: '#1f5c4b',
          borderRadius: 4,
          maxBarThickness: 48,
        }]
      };
    });
  }
}
