/** Anima un número de 0 al valor final en `duracionMs` (requestAnimationFrame). Se usa en los
 * KPI de Dashboard/Analítica para dar un "momento" a la carga de datos en vez de aparecer de
 * golpe. Solo tiene sentido en el navegador (no hay requestAnimationFrame en SSR); quien la
 * llama debe guardar dentro de un `if (isBrowser)`. */
export function animateCountUp(valorFinal: number, onTick: (valor: number) => void, duracionMs = 600): void {
  // SSR no tiene requestAnimationFrame: se entrega el valor final de una, sin animar.
  if (typeof requestAnimationFrame === 'undefined' || !Number.isFinite(valorFinal)) {
    onTick(valorFinal);
    return;
  }

  const inicio = performance.now();

  const paso = (ahora: number) => {
    const progreso = Math.min(1, (ahora - inicio) / duracionMs);
    // ease-out cúbico: rápido al principio, se asienta suave al final.
    const avance = 1 - Math.pow(1 - progreso, 3);
    onTick(valorFinal * avance);
    if (progreso < 1) {
      requestAnimationFrame(paso);
    } else {
      onTick(valorFinal);
    }
  };

  requestAnimationFrame(paso);
}
