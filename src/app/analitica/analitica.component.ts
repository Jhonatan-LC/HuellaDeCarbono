import { ChangeDetectorRef, Component, OnInit, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgxEchartsDirective } from 'ngx-echarts';
import type { ECElementEvent, ECharts, EChartsOption } from 'echarts';
import { catchError, of } from 'rxjs';
import {
  AnaliticaService,
  AnalyticsOverview,
  DesgloseCategoria,
  Ubicacion,
} from './analitica.service';
import { TopbarComponent } from '../shared/topbar.component';
import { CompactoKgCo2ePipe } from '../shared/compact-kg-co2e.pipe';
import { animateCountUp } from '../shared/animate-count-up';
import { ChartTheme, colorPorAlcance, leerChartTheme } from '../shared/chart-theme';

const PALETA = ['#1f5c4b', '#2f7a63', '#7fb2a3', '#b45309', '#64748b', '#94a3b8'];

const NOMBRES_ALCANCE: { [alcance: string]: string } = {
  '1': 'Alcance 1 · Directas',
  '2': 'Alcance 2 · Energía',
  '3': 'Alcance 3 · Indirectas',
};

interface GeoFeature {
  type: 'Feature';
  properties: { name: string };
  geometry: { type: string; coordinates: unknown };
}

interface GeoJson {
  type: 'FeatureCollection';
  features: GeoFeature[];
}

interface PuntoPlanta {
  ubicacionId: number;
  nombre: string;
  pais: string;
  longitud: number;
  latitud: number;
  valorKgCo2e: number | null;
}

// Módulo-scope: el mapa mundial (GeoJSON + registerMap en echarts) se carga y registra
// una sola vez por sesión de navegador, no por cada vez que se entra a /analitica.
let worldGeoJsonCache: GeoJson | null = null;
let worldMapRegistrado = false;

@Component({
  selector: 'app-analitica',
  standalone: true,
  imports: [FormsModule, NgxEchartsDirective, TopbarComponent, CompactoKgCo2ePipe],
  templateUrl: './analitica.component.html',
  styleUrls: ['./analitica.component.css'],
})
export class AnaliticaComponent implements OnInit {
  public overview: AnalyticsOverview | null = null;
  public ubicaciones: Ubicacion[] = [];
  public error: string | null = null;
  public cargando = true;
  // ngx-echarts necesita un DOM real (canvas) para inicializar los gráficos: no existe
  // durante el renderizado en el servidor (SSR), así que los charts solo se montan en
  // el navegador, tras la hidratación.
  public isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  public mapaListo = false;
  public nombresPaises: string[] = [];

  // Filial seleccionada en el mapa: filtra toda la analítica (resumen, categorías,
  // tendencia, combustibles/agua/residuos) a esa ubicación. null = todas las filiales.
  public selectedUbicacionId: number | null = null;
  public selectedUbicacionNombre: string | null = null;

  // Formulario "Agregar planta"
  public mostrarFormularioPlanta = false;
  public nuevaPlanta = { nombre: '', pais: '', latitud: null as number | null, longitud: null as number | null };
  public guardandoPlanta = false;
  public errorPlanta: string | null = null;
  // Punto recién clickeado en el mapa, aún sin guardar (se dibuja como marcador temporal).
  private puntoPendiente: { longitud: number; latitud: number } | null = null;

  public alcanceDonut: EChartsOption = {};
  public categoriaBar: EChartsOption = {};
  public tendenciaLine: EChartsOption = {};
  public combustiblesBar: EChartsOption = {};
  public aguaBar: EChartsOption = {};
  public residuosBar: EChartsOption = {};
  public plantaBar: EChartsOption = {};
  public mapaPlantasOption: EChartsOption = {};

  private chart: ECharts | null = null;
  private chartTheme: ChartTheme = leerChartTheme();

  // Valores animados (0 -> total) para el "momento" de carga de los KPI — ver
  // animateCountUp en src/app/shared/animate-count-up.ts.
  public totalCo2eAnimado = 0;
  public alcance1Animado = 0;
  public alcance2Animado = 0;
  public alcance3Animado = 0;

  constructor(private analiticaService: AnaliticaService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    if (this.isBrowser) {
      this.chartTheme = leerChartTheme();
    }
    this.cargarOverview();
    this.cargarUbicaciones();
    if (this.isBrowser) {
      this.cargarMapaMundial();
    }
  }

  private cargarOverview(): void {
    this.cargando = true;
    this.analiticaService.getOverview(this.selectedUbicacionId).pipe(
      catchError((err) => {
        console.error('Error cargando analítica:', err);
        this.error = `Error al cargar datos: ${err.status} ${err.statusText}`;
        return of(null);
      })
    ).subscribe((data) => {
      this.cargando = false;
      if (!data) {
        this.cdr.markForCheck();
        return;
      }
      this.overview = data;
      this.construirGraficos(data);
      this.actualizarMapaPlantas();
      this.animarKpis(data);
      this.cdr.markForCheck();
    });
  }

  private animarKpis(data: AnalyticsOverview): void {
    if (!this.isBrowser) {
      this.totalCo2eAnimado = this.totalCo2e;
      this.alcance1Animado = this.alcance1;
      this.alcance2Animado = this.alcance2;
      this.alcance3Animado = this.alcance3;
      return;
    }
    animateCountUp(this.totalCo2e, (v) => { this.totalCo2eAnimado = v; this.cdr.markForCheck(); });
    animateCountUp(this.alcance1, (v) => { this.alcance1Animado = v; this.cdr.markForCheck(); });
    animateCountUp(this.alcance2, (v) => { this.alcance2Animado = v; this.cdr.markForCheck(); });
    animateCountUp(this.alcance3, (v) => { this.alcance3Animado = v; this.cdr.markForCheck(); });
  }

  private cargarUbicaciones(): void {
    this.analiticaService.getUbicaciones().pipe(
      catchError(() => of([]))
    ).subscribe((ubicaciones) => {
      this.ubicaciones = ubicaciones;
      this.actualizarMapaPlantas();
      this.cdr.markForCheck();
    });
  }

  private async cargarMapaMundial(): Promise<void> {
    try {
      if (!worldGeoJsonCache) {
        worldGeoJsonCache = await fetch('/world-countries.geojson').then((r) => r.json());
      }
      if (!worldMapRegistrado) {
        const echarts = await import('echarts');
        // El tipado de registerMap espera GeoJSON.FeatureCollection "crudo" del paquete
        // `geojson`; nuestra interfaz GeoJson es equivalente en runtime (mismo shape),
        // así que el cast es seguro.
        echarts.registerMap('world', worldGeoJsonCache as any);
        worldMapRegistrado = true;
      }
      this.nombresPaises = (worldGeoJsonCache?.features ?? [])
        .map((f) => f.properties.name)
        .sort((a, b) => a.localeCompare(b));
      this.mapaListo = true;
      this.actualizarMapaPlantas();
      this.cdr.markForCheck();
    } catch (err) {
      console.error('No se pudo cargar el mapa mundial:', err);
      this.cdr.markForCheck();
    }
  }

  get totalCo2e(): number {
    return this.overview?.resumen.total_kg_co2e ?? 0;
  }

  get alcance1(): number {
    return this.overview?.resumen.por_alcance['1'] ?? 0;
  }

  get alcance2(): number {
    return this.overview?.resumen.por_alcance['2'] ?? 0;
  }

  get alcance3(): number {
    return this.overview?.resumen.por_alcance['3'] ?? 0;
  }

  /** % reciclado vs. generado. Aproximado: compara categorías independientes
   * (residuos_reciclados vs. el resto de categorías de material), no un mismo
   * lote trazado de generación a destino. */
  get porcentajeReciclado(): number | null {
    const residuos = this.overview?.residuos ?? [];
    const reciclados = residuos.find(r => r.codigo === 'residuos_reciclados')?.cantidad_total ?? 0;
    const generadoMaterial = residuos
      .filter(r => r.codigo !== 'residuos_reciclados' && r.codigo !== 'residuos_disposicion_final')
      .reduce((acc, r) => acc + r.cantidad_total, 0);

    if (generadoMaterial === 0) return null;
    return Math.round((reciclados / generadoMaterial) * 1000) / 10;
  }

  get tienePlantas(): boolean {
    return (this.overview?.por_planta.length ?? 0) > 0;
  }

  get tieneUbicaciones(): boolean {
    return this.ubicaciones.length > 0;
  }

  toggleFormularioPlanta(): void {
    this.mostrarFormularioPlanta = !this.mostrarFormularioPlanta;
    this.errorPlanta = null;
    if (!this.mostrarFormularioPlanta) {
      this.puntoPendiente = null;
      this.actualizarMapaPlantas();
    }
  }

  guardarPlanta(): void {
    const nombre = this.nuevaPlanta.nombre.trim();
    if (!nombre) {
      this.errorPlanta = 'El nombre de la planta es obligatorio.';
      return;
    }

    this.guardandoPlanta = true;
    this.errorPlanta = null;

    this.analiticaService.crearUbicacion({
      nombre,
      pais: this.nuevaPlanta.pais.trim(),
      latitud: this.nuevaPlanta.latitud,
      longitud: this.nuevaPlanta.longitud,
    }).pipe(
      catchError((err) => {
        this.errorPlanta = `No se pudo guardar la planta: ${err.status} ${err.statusText}`;
        return of(null);
      })
    ).subscribe((ubicacion) => {
      this.guardandoPlanta = false;
      if (!ubicacion) {
        this.cdr.markForCheck();
        return;
      }
      this.ubicaciones = [...this.ubicaciones, ubicacion];
      this.nuevaPlanta = { nombre: '', pais: '', latitud: null, longitud: null };
      this.mostrarFormularioPlanta = false;
      this.puntoPendiente = null;
      this.actualizarMapaPlantas();
      this.cdr.markForCheck();
    });
  }

  /** Click sobre un pin (filtra la analítica) o sobre el mapa/país de fondo
   * (precarga el formulario de "agregar planta" con esas coordenadas). */
  onChartInit(chart: ECharts): void {
    this.chart = chart;
  }

  onChartClick(event: ECElementEvent): void {
    if (event.componentType === 'series' && event.seriesType === 'scatter') {
      const data = event.data as { ubicacionId?: number } | null;
      if (data?.ubicacionId) {
        this.seleccionarUbicacion(data.ubicacionId, event.name);
      }
      return;
    }

    // Click en el mapa/país de fondo: solo dispara si el punto cae sobre algún país
    // renderizado (el fondo del océano, sin geometría, no es clickeable en ECharts).
    if (event.componentType === 'geo' && this.chart) {
      const nativeEvent = event.event;
      if (!nativeEvent) return;
      const coords = this.chart.convertFromPixel({ geoIndex: 0 }, [nativeEvent.offsetX, nativeEvent.offsetY]);
      if (!coords) return;

      const [longitud, latitud] = coords as number[];
      this.nuevaPlanta.longitud = Math.round(longitud * 1e6) / 1e6;
      this.nuevaPlanta.latitud = Math.round(latitud * 1e6) / 1e6;
      if (!this.nuevaPlanta.pais && event.name) {
        this.nuevaPlanta.pais = event.name;
      }
      this.mostrarFormularioPlanta = true;
      this.errorPlanta = null;
      this.puntoPendiente = { longitud, latitud };
      this.actualizarMapaPlantas();
      this.cdr.markForCheck();
    }
  }

  seleccionarUbicacion(id: number, nombre: string): void {
    if (this.selectedUbicacionId === id) return;
    this.selectedUbicacionId = id;
    this.selectedUbicacionNombre = nombre;
    this.actualizarMapaPlantas();
    this.cargarOverview();
  }

  verTodasLasFiliales(): void {
    this.selectedUbicacionId = null;
    this.selectedUbicacionNombre = null;
    this.actualizarMapaPlantas();
    this.cargarOverview();
  }

  centrarEnPais(nombrePais: string): void {
    if (!nombrePais || !this.chart || !worldGeoJsonCache) return;
    const feature = worldGeoJsonCache.features.find((f) => f.properties.name === nombrePais);
    if (!feature) return;
    const [cx, cy] = this.centroDeFeature(feature);
    this.chart.setOption({ geo: { center: [cx, cy], zoom: 5 } });
  }

  /** Centro del polígono más grande de la feature (por área de su bbox), no el promedio de
   * toda la geometría. Países que cruzan el antimeridiano (Rusia, Fiyi — ver
   * public/world-countries.geojson, generado con geojson-antimeridian-cut) quedan partidos en
   * varios polígonos; promediar el bbox de TODOS daría un centro a mitad de camino en el
   * Atlántico en vez del territorio principal. */
  private centroDeFeature(feature: GeoFeature): [number, number] {
    const poligonos: number[][][] =
      feature.geometry.type === 'MultiPolygon'
        ? (feature.geometry.coordinates as number[][][][]).map((poly) => poly[0])
        : [(feature.geometry.coordinates as number[][][])[0]];

    let mejorBbox: { minLng: number; maxLng: number; minLat: number; maxLat: number } | null = null;
    let mejorArea = -1;

    for (const anillo of poligonos) {
      let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
      for (const [lng, lat] of anillo) {
        if (lng < minLng) minLng = lng;
        if (lng > maxLng) maxLng = lng;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      }
      const area = (maxLng - minLng) * (maxLat - minLat);
      if (area > mejorArea) {
        mejorArea = area;
        mejorBbox = { minLng, maxLng, minLat, maxLat };
      }
    }

    if (!mejorBbox) return [0, 0];
    return [(mejorBbox.minLng + mejorBbox.maxLng) / 2, (mejorBbox.minLat + mejorBbox.maxLat) / 2];
  }

  private construirGraficos(data: AnalyticsOverview): void {
    const tema = this.chartTheme;

    this.alcanceDonut = this.donut(
      Object.entries(data.resumen.por_alcance)
        .filter(([, valor]) => valor > 0)
        .map(([alcance, valor]) => ({
          name: NOMBRES_ALCANCE[alcance] ?? `Alcance ${alcance}`,
          value: valor,
          itemStyle: { color: colorPorAlcance(Number(alcance), tema) },
        }))
    );

    this.categoriaBar = this.barraHorizontal(
      data.por_categoria.map(c => c.categoria),
      data.por_categoria.map((c) => ({ value: c.valor_kg_co2e, itemStyle: { color: colorPorAlcance(c.alcance, tema) } })),
      'kg CO2e'
    );

    this.tendenciaLine = this.linea(
      data.tendencia_periodo.map(p => p.periodo),
      data.tendencia_periodo.map(p => p.valor_kg_co2e)
    );

    this.combustiblesBar = this.barraCantidad(data.combustibles);
    this.aguaBar = this.barraCantidad(data.agua);
    this.residuosBar = this.barraCantidad(data.residuos);

    this.plantaBar = this.barraHorizontal(
      data.por_planta.map(p => p.nombre),
      data.por_planta.map(p => ({ value: p.valor_kg_co2e, itemStyle: { color: tema.accent } })),
      'kg CO2e'
    );
  }

  private donut(datos: { name: string; value: number; itemStyle: { color: string } }[]): EChartsOption {
    const tema = this.chartTheme;
    return {
      // La tarjeta de este gráfico es angosta (1/3 del ancho): las etiquetas de
      // porcentaje fuera del anillo no tienen espacio y chocan con la leyenda.
      // Se muestran solo en el tooltip al pasar el mouse; la leyenda ya identifica
      // cada alcance por color.
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} kg CO2e ({d}%)',
        backgroundColor: tema.tooltipBg,
        textStyle: { color: tema.tooltipText },
      },
      legend: { bottom: 0, itemGap: 6, textStyle: { fontSize: 12, color: tema.axisText } },
      series: [{
        type: 'pie',
        radius: ['45%', '65%'],
        center: ['50%', '42%'],
        // minAngle asegura que los alcances con valores muy chicos (ej. Alcance 2)
        // sigan teniendo un arco visible en vez de desaparecer.
        minAngle: 8,
        label: { show: false },
        labelLine: { show: false },
        data: datos,
      }],
    };
  }

  private barraHorizontal(categorias: string[], valores: { value: number; itemStyle: { color: string } }[], unidad: string): EChartsOption {
    const tema = this.chartTheme;
    return {
      grid: { left: '3%', right: '12%', bottom: '3%', top: '3%', containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        valueFormatter: (v) => `${v} ${unidad}`,
        backgroundColor: tema.tooltipBg,
        textStyle: { color: tema.tooltipText },
      },
      xAxis: { type: 'value', axisLabel: { fontSize: 12, color: tema.axisText }, splitLine: { lineStyle: { color: tema.gridLine } } },
      yAxis: { type: 'category', data: categorias, inverse: true, axisLabel: { fontSize: 12, color: tema.axisText } },
      series: [{
        type: 'bar',
        data: valores,
        // Valor al final de cada barra: no depende de leer el eje para saber la cifra.
        label: { show: true, position: 'right', fontSize: 12, color: tema.axisText, formatter: '{c}' },
      }],
    };
  }

  private linea(periodos: string[], valores: number[]): EChartsOption {
    const tema = this.chartTheme;
    return {
      color: [tema.accent],
      grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => `${v} kg CO2e`,
        backgroundColor: tema.tooltipBg,
        textStyle: { color: tema.tooltipText },
      },
      xAxis: { type: 'category', data: periodos, axisLabel: { fontSize: 12, color: tema.axisText } },
      yAxis: { type: 'value', axisLabel: { fontSize: 12, color: tema.axisText }, splitLine: { lineStyle: { color: tema.gridLine } } },
      series: [{ type: 'line', data: valores, smooth: true, areaStyle: {}, itemStyle: { color: tema.accent }, symbolSize: 8 }],
    };
  }

  private barraCantidad(items: DesgloseCategoria[]): EChartsOption {
    const tema = this.chartTheme;
    return {
      color: [tema.accent],
      grid: { left: '3%', right: '14%', bottom: '3%', top: '3%', containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const p = Array.isArray(params) ? params[0] : params;
          const item = items[p.dataIndex];
          return `${item.categoria}: ${p.value} ${item.unidad}`;
        },
        backgroundColor: tema.tooltipBg,
        textStyle: { color: tema.tooltipText },
      },
      xAxis: { type: 'value', axisLabel: { fontSize: 12, color: tema.axisText }, splitLine: { lineStyle: { color: tema.gridLine } } },
      yAxis: { type: 'category', data: items.map(i => i.categoria), inverse: true, axisLabel: { fontSize: 12, color: tema.axisText } },
      series: [{
        type: 'bar',
        data: items.map(i => i.cantidad_total),
        itemStyle: { color: tema.accent },
        label: { show: true, position: 'right', fontSize: 12, color: tema.axisText, formatter: (p: any) => `${p.value} ${items[p.dataIndex]?.unidad ?? ''}` },
      }],
    };
  }

  /** Todas las filiales de la organización (this.ubicaciones), enriquecidas con el
   * kg CO2e de overview.por_planta cuando existe — una filial sin actividad aún
   * (recién creada) sigue apareciendo en el mapa como punto neutro y clickeable. */
  private puntosPlanta(): PuntoPlanta[] {
    const co2ePorUbicacion = new Map(
      (this.overview?.por_planta ?? []).map((p) => [p.ubicacion_id, p.valor_kg_co2e])
    );
    return this.ubicaciones
      .filter((u) => u.latitud !== null && u.longitud !== null)
      .map((u) => ({
        ubicacionId: u.id,
        nombre: u.nombre,
        pais: u.pais,
        longitud: u.longitud as number,
        latitud: u.latitud as number,
        valorKgCo2e: co2ePorUbicacion.get(u.id) ?? null,
      }));
  }

  /** Mapa real (contorno de países vía GeoJSON, ver cargarMapaMundial) con las
   * filiales como pines sobre un componente `geo` con roam habilitado — permite
   * hacer zoom/pan para ubicar filiales con precisión dentro de un mismo país
   * (varias filiales en Chile, en Perú, etc.), no solo a nivel mundial. */
  private actualizarMapaPlantas(): void {
    if (!this.mapaListo) return;

    const puntos = this.puntosPlanta();
    const data = puntos.map((p) => ({
      name: p.nombre,
      value: [p.longitud, p.latitud, p.valorKgCo2e ?? 0],
      ubicacionId: p.ubicacionId,
      pais: p.pais,
      valorKgCo2e: p.valorKgCo2e,
    }));

    if (this.puntoPendiente) {
      data.push({
        name: 'Nueva filial (sin guardar)',
        value: [this.puntoPendiente.longitud, this.puntoPendiente.latitud, 0],
        ubicacionId: undefined as unknown as number,
        pais: '',
        valorKgCo2e: null,
      });
    }

    const tema = this.chartTheme;
    this.mapaPlantasOption = {
      tooltip: {
        formatter: (params: any) => {
          if (params.componentType === 'series') {
            const p = params.data;
            if (!p.ubicacionId) return p.name;
            const co2 = p.valorKgCo2e != null ? `${p.valorKgCo2e} kg CO2e` : 'Sin actividad registrada aún';
            return `${p.name}${p.pais ? ' · ' + p.pais : ''}<br/>${co2}`;
          }
          return params.name;
        },
        backgroundColor: tema.tooltipBg,
        textStyle: { color: tema.tooltipText },
      },
      geo: {
        map: 'world',
        roam: true,
        zoom: 1.15,
        itemStyle: { areaColor: tema.gridLine, borderColor: tema.axisText },
        emphasis: { itemStyle: { areaColor: tema.accent }, label: { show: false } },
      },
      series: [{
        type: 'scatter',
        coordinateSystem: 'geo',
        symbolSize: (val: number[]) => (val[2] ? Math.max(10, Math.min(42, Math.sqrt(val[2]) * 2)) : 9),
        data,
        itemStyle: {
          color: (params: any) =>
            !params.data.ubicacionId || params.data.ubicacionId === this.selectedUbicacionId
              ? PALETA[3]
              : tema.accent,
          opacity: 0.85,
          borderColor: '#fff',
          borderWidth: 1,
        },
      }],
    };
  }
}
