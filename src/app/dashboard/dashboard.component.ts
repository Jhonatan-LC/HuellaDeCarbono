import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { AsyncPipe, DecimalPipe } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartOptions, ChartType } from 'chart.js';
import { DashboardService, DashboardKpis, CarbonFootprintData } from './dashboard.service';
import { Observable, catchError, of, tap } from 'rxjs';
import { TopbarComponent } from '../shared/topbar.component';
import { RouterLink } from '@angular/router';
import { animateCountUp } from '../shared/animate-count-up';
import { leerChartTheme } from '../shared/chart-theme';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [AsyncPipe, DecimalPipe, BaseChartDirective, TopbarComponent, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  providers: [DashboardService],
})
export class DashboardComponent implements OnInit {
  public kpis$!: Observable<DashboardKpis>;
  public currentYear: number = new Date().getFullYear();
  public error: string | null = null;
  public gastoMesAnimado = 0;

  private tema = leerChartTheme();

  // Barras horizontales: las etiquetas de categoría (a veces largas) se leen mejor así que
  // rotadas a 45° en el eje X.
  public barChartOptions: ChartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: this.tema.tooltipBg,
        titleColor: this.tema.tooltipText,
        bodyColor: this.tema.tooltipText,
        padding: 10,
        cornerRadius: 6,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: { color: this.tema.gridLine },
        ticks: { color: this.tema.axisText, font: { size: 12 } },
      },
      y: {
        grid: { display: false },
        ticks: { color: this.tema.axisText, font: { size: 12 } },
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
      backgroundColor: this.tema.accent,
      borderRadius: 4,
      maxBarThickness: 32,
    }]
  };

  // KPIs vacíos como fallback mientras no hay datos
  private emptyKpis: DashboardKpis = {
    gasto_mes_actual: { monto_clp: null, periodo: '', desglose: {} },
    racha_meses: { cantidad: 0, activa: false },
    alerta_anomalia: { detectada: false, mensaje: 'Sin datos' },
    comparativa_anual: { disponible: false },
  }

  constructor(private dashboardService: DashboardService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    // Captura errores para no dejar el skeleton infinito
    this.kpis$ = this.dashboardService.getKpis().pipe(
      catchError((err) => {
        console.error('Error cargando KPIs:', err)
        this.error = `Error al cargar datos: ${err.status} ${err.statusText}`
        return of(this.emptyKpis)
      }),
      tap((kpis) => {
        if (kpis.gasto_mes_actual.monto_clp !== null) {
          animateCountUp(kpis.gasto_mes_actual.monto_clp, (v) => { this.gastoMesAnimado = v; this.cdr.markForCheck(); });
        }
      }),
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
          backgroundColor: this.tema.accent,
          borderRadius: 4,
          maxBarThickness: 32,
        }]
      };
      this.cdr.markForCheck();
    });
  }
}
