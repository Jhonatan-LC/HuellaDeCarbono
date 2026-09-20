import { Pipe, PipeTransform } from '@angular/core';

/** "39,0 M kg CO2e" en vez de "39.002.511,6 kg CO2e": las cifras de huella de carbono
 * crecen rápido (org con muchas filiales/meses) y una cifra compacta se lee al instante. */
@Pipe({ name: 'compactoKgCo2e', standalone: true })
export class CompactoKgCo2ePipe implements PipeTransform {
  transform(valor: number | null | undefined): string {
    if (valor === null || valor === undefined || Number.isNaN(valor)) {
      return '—';
    }

    const abs = Math.abs(valor);
    if (abs >= 1_000_000) {
      return `${this.formatear(valor / 1_000_000)} M kg CO2e`;
    }
    if (abs >= 1_000) {
      return `${this.formatear(valor / 1_000)} k kg CO2e`;
    }
    return `${this.formatear(valor)} kg CO2e`;
  }

  private formatear(valor: number): string {
    return valor.toLocaleString('es', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }
}
