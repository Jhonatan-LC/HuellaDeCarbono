/** Colores para las opciones de ECharts/Chart.js que hoy van hardcodeadas en
 * dashboard.component.ts y analitica.component.ts. Los componentes de Angular ya cambian de
 * tema solo (consumen var(--token) en su CSS), pero las opciones de los charts son objetos JS
 * planos que arma cada componente — este helper les da los mismos colores según el tema activo,
 * leyendo las variables CSS ya resueltas en <html> (fuente única de verdad: styles.css). */
export interface ChartTheme {
  axisText: string;
  gridLine: string;
  tooltipBg: string;
  tooltipText: string;
  scope1: string;
  scope2: string;
  scope3: string;
  accent: string;
  muted: string;
}

const FALLBACK: ChartTheme = {
  axisText: '#64748b',
  gridLine: '#e2e8f0',
  tooltipBg: '#0f172a',
  tooltipText: '#fff',
  scope1: '#0f766e',
  scope2: '#f59e0b',
  scope3: '#6366f1',
  accent: '#10b981',
  muted: '#64748b',
};

export function leerChartTheme(): ChartTheme {
  if (typeof document === 'undefined') {
    // SSR: nunca se renderiza un chart en el servidor (ver isBrowser en cada componente),
    // pero el tipo debe poder construirse igual sin document.
    return FALLBACK;
  }

  const estilos = getComputedStyle(document.documentElement);
  const leer = (token: string, fallback: string) => estilos.getPropertyValue(token).trim() || fallback;

  const esOscuro = document.documentElement.getAttribute('data-theme') === 'dark'
    || (!document.documentElement.hasAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);

  return {
    axisText: leer('--muted', FALLBACK.axisText),
    gridLine: leer('--line', FALLBACK.gridLine),
    tooltipBg: esOscuro ? leer('--surface-soft', '#14332a') : '#0f172a',
    tooltipText: esOscuro ? leer('--text', '#ecfdf5') : '#fff',
    scope1: leer('--scope-1', FALLBACK.scope1),
    scope2: leer('--scope-2', FALLBACK.scope2),
    scope3: leer('--scope-3', FALLBACK.scope3),
    accent: leer('--accent', FALLBACK.accent),
    muted: leer('--muted', FALLBACK.muted),
  };
}

/** Color por número de alcance (1/2/3) — mismo color en toda la app (donut, barras, chips). */
export function colorPorAlcance(alcance: number, tema: ChartTheme): string {
  if (alcance === 1) return tema.scope1;
  if (alcance === 2) return tema.scope2;
  if (alcance === 3) return tema.scope3;
  return tema.muted;
}
