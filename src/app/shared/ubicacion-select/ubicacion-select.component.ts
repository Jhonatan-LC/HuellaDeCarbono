import { Component, ElementRef, HostListener, inject, input, output, signal } from '@angular/core';

export interface UbicacionOpcion {
  id: number;
  nombre: string;
}

/** Reemplazo del <select> nativo para elegir planta/filial: el nativo rompe el diseño (usa el
 * estilo del SO). Listbox propio, mismo comportamiento (una opción, o "Sin especificar"). */
@Component({
  selector: 'app-ubicacion-select',
  standalone: true,
  template: `
    <div class="ubicacion-select" [class.open]="abierto()">
      <button type="button" class="ubicacion-select-trigger" (click)="toggle()">
        <span>{{ etiquetaSeleccionada() }}</span>
        <span class="ubicacion-select-caret" aria-hidden="true">▾</span>
      </button>
      @if (abierto()) {
        <ul class="ubicacion-select-panel" role="listbox">
          <li role="option" [class.selected]="value() === null" (click)="elegir(null)">
            {{ placeholder() }}
          </li>
          @for (u of ubicaciones(); track u.id) {
            <li role="option" [class.selected]="value() === u.id" (click)="elegir(u.id)">
              {{ u.nombre }}
            </li>
          }
        </ul>
      }
    </div>
  `,
  styles: [`
    .ubicacion-select {
      position: relative;
    }
    .ubicacion-select-trigger {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: var(--radius-md);
      padding: 0.7rem 0.85rem;
      background: var(--surface);
      color: var(--text);
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .ubicacion-select.open .ubicacion-select-trigger {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-soft);
    }
    .ubicacion-select-caret {
      color: var(--muted);
      font-size: 0.7rem;
    }
    .ubicacion-select-panel {
      position: absolute;
      z-index: 10;
      top: calc(100% + 0.35rem);
      left: 0;
      right: 0;
      max-height: 220px;
      overflow-y: auto;
      margin: 0;
      padding: 0.35rem;
      list-style: none;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-lg);
    }
    .ubicacion-select-panel li {
      padding: 0.55rem 0.65rem;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      cursor: pointer;
    }
    .ubicacion-select-panel li:hover {
      background: var(--surface-soft);
    }
    .ubicacion-select-panel li.selected {
      background: var(--accent-soft);
      color: var(--primary-strong);
      font-weight: 600;
    }
  `],
})
export class UbicacionSelectComponent {
  private el = inject(ElementRef<HTMLElement>);

  ubicaciones = input<UbicacionOpcion[]>([]);
  value = input<number | null>(null);
  placeholder = input('Sin especificar');
  valueChange = output<number | null>();

  abierto = signal(false);

  etiquetaSeleccionada(): string {
    const id = this.value();
    if (id === null) return this.placeholder();
    return this.ubicaciones().find((u) => u.id === id)?.nombre ?? this.placeholder();
  }

  toggle(): void {
    this.abierto.update((v) => !v);
  }

  elegir(id: number | null): void {
    this.abierto.set(false);
    this.valueChange.emit(id);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.abierto() && !this.el.nativeElement.contains(event.target as Node)) {
      this.abierto.set(false);
    }
  }
}
