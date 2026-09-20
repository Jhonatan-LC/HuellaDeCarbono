import { Injectable, PLATFORM_ID, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'huella-carbono-theme';

/** Preferencia de tema explícita del usuario (botón sol/luna en el topbar). Sin preferencia
 * guardada, se respeta `prefers-color-scheme` del SO vía CSS (ver styles.css) y este servicio
 * no fuerza ningún atributo — por eso `current` puede quedar en null. SSR-safe: todo acceso a
 * document/localStorage está detrás de `isBrowser` (no existen durante el renderizado en el
 * servidor), mismo patrón que `analitica.component.ts::isBrowser`. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  public current = signal<Theme | null>(null);

  init(): void {
    if (!this.isBrowser) return;
    const guardado = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (guardado === 'light' || guardado === 'dark') {
      this.aplicar(guardado);
    }
  }

  toggle(): void {
    if (!this.isBrowser) return;
    const efectivoActual = this.current() ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const siguiente: Theme = efectivoActual === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, siguiente);
    this.aplicar(siguiente);
  }

  private aplicar(tema: Theme): void {
    document.documentElement.setAttribute('data-theme', tema);
    this.current.set(tema);
  }
}
