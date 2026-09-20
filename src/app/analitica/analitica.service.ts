import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ResumenAnalitica {
  total_kg_co2e: number;
  por_alcance: { [alcance: string]: number };
}

export interface CategoriaValor {
  categoria: string;
  alcance: number;
  valor_kg_co2e: number;
}

export interface PeriodoValor {
  periodo: string;
  valor_kg_co2e: number;
}

export interface DesgloseCategoria {
  categoria: string;
  codigo: string;
  unidad: string;
  cantidad_total: number;
  co2e_total: number | null;
}

export interface PlantaValor {
  ubicacion_id: number;
  nombre: string;
  pais: string;
  latitud: number | null;
  longitud: number | null;
  valor_kg_co2e: number;
}

export interface AnalyticsOverview {
  resumen: ResumenAnalitica;
  por_categoria: CategoriaValor[];
  tendencia_periodo: PeriodoValor[];
  combustibles: DesgloseCategoria[];
  agua: DesgloseCategoria[];
  residuos: DesgloseCategoria[];
  por_planta: PlantaValor[];
}

export interface Ubicacion {
  id: number;
  nombre: string;
  pais: string;
  latitud: number | null;
  longitud: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class AnaliticaService {
  private overviewUrl = `${environment.apiBaseUrl}/api/analytics/overview/`;
  private ubicacionesUrl = `${environment.apiBaseUrl}/api/ubicaciones/`;

  constructor(private http: HttpClient) {}

  getOverview(ubicacionId?: number | null): Observable<AnalyticsOverview> {
    const params = ubicacionId ? new HttpParams().set('ubicacion_id', ubicacionId) : undefined;
    return this.http.get<AnalyticsOverview>(this.overviewUrl, { params, withCredentials: true });
  }

  getUbicaciones(): Observable<Ubicacion[]> {
    return this.http.get<Ubicacion[]>(this.ubicacionesUrl, { withCredentials: true });
  }

  crearUbicacion(datos: { nombre: string; pais?: string; latitud?: number | null; longitud?: number | null }): Observable<Ubicacion> {
    return this.http.post<Ubicacion>(this.ubicacionesUrl, datos, { withCredentials: true });
  }
}
