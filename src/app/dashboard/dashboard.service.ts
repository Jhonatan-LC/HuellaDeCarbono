import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CarbonFootprintData {
  name: string;
  value: number;
}

export interface GastoMesActual {
  monto_clp: number | null;
  periodo: string;
  desglose: { [key: string]: number };
}

export interface RachaMeses {
  cantidad: number;
  activa: boolean;
}

export interface AlertaAnomalia {
  detectada: boolean;
  campo?: string;
  valor_actual?: number;
  promedio_historico?: number;
  porcentaje_desviacion?: number;
  mensaje: string;
}

export interface ComparativaAnual {
  disponible: boolean;
  mes_actual_co2_kg?: number;
  mismo_mes_año_anterior_co2_kg?: number;
  porcentaje_variacion?: number;
  mensaje?: string;
}

export interface DashboardKpis {
  gasto_mes_actual: GastoMesActual;
  racha_meses: RachaMeses;
  alerta_anomalia: AlertaAnomalia;
  comparativa_anual: ComparativaAnual;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private kpisUrl = `${environment.apiBaseUrl}/api/dashboard/kpis/`;
  private analyticsUrl = `${environment.apiBaseUrl}/api/analytics/carbon-footprint/`;

  constructor(private http: HttpClient) {}

  getCarbonFootprint(): Observable<CarbonFootprintData[]> {
    return this.http.get<CarbonFootprintData[]>(this.analyticsUrl, { withCredentials: true });
  }

  getKpis(): Observable<DashboardKpis> {
    return this.http.get<DashboardKpis>(this.kpisUrl, { withCredentials: true });
  }
}
