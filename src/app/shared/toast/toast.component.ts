import { Component } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { UiService } from '../ui.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [AsyncPipe],
  template: `
    <div class="toast-stack">
      @for (toast of ui.toasts$ | async; track toast.id) {
        <div class="toast" [class.toast-error]="toast.tipo === 'error'">
          <span class="toast-icon">{{ toast.tipo === 'error' ? '✕' : '✓' }}</span>
          <span>{{ toast.mensaje }}</span>
          <button type="button" class="toast-close" (click)="ui.dismissToast(toast.id)" aria-label="Cerrar">×</button>
        </div>
      }
    </div>
  `,
  styles: [`
    .toast-stack {
      position: fixed;
      right: 1rem;
      bottom: 1rem;
      z-index: 200;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      max-width: min(360px, calc(100vw - 2rem));
    }
    .toast {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.85rem 1rem;
      border-radius: var(--radius-md);
      background: var(--primary-strong);
      color: #fff;
      box-shadow: var(--shadow-lg);
      font-size: 0.88rem;
      font-weight: 600;
      animation: toast-in 0.2s ease;
    }
    .toast-error {
      background: var(--danger);
    }
    .toast-icon {
      display: grid;
      place-items: center;
      width: 1.4rem;
      height: 1.4rem;
      flex-shrink: 0;
      border-radius: var(--radius-full);
      background: rgba(255, 255, 255, 0.2);
      font-size: 0.78rem;
    }
    .toast span:nth-child(2) {
      flex: 1;
    }
    .toast-close {
      background: none;
      border: none;
      color: inherit;
      opacity: 0.8;
      cursor: pointer;
      font-size: 1.1rem;
      line-height: 1;
      padding: 0.1rem;
    }
    .toast-close:hover {
      opacity: 1;
    }
    @keyframes toast-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `],
})
export class ToastComponent {
  constructor(public ui: UiService) {}
}
