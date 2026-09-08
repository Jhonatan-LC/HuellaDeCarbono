import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UiService } from '../ui.service';
import { AuthService } from '../../auth/auth.service';

@Component({
  selector: 'app-welcome-popup',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="ui.welcomePopupVisible$ | async" class="overlay">
      <div class="popup-card">
        <h2>Bienvenido</h2>
        <p>Iniciaste sesión correctamente. Ya puedes registrar y analizar tus consumos.</p>
        <button (click)="close()" class="btn btn-primary" style="width: 100%;">Entendido</button>
      </div>
    </div>
  `,
  styles: [`
    .overlay {
      position: fixed;
      inset: 0;
      background-color: rgba(15, 23, 42, 0.5);
      display: grid;
      place-items: center;
      z-index: 100;
      padding: 1rem;
    }
    .popup-card {
      width: min(100%, 400px);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      padding: 1.75rem;
      text-align: center;
      box-shadow: var(--shadow-lg);
    }
    h2 {
      margin: 0 0 0.5rem;
      font-size: 1.3rem;
    }
    p {
      margin: 0 0 1.5rem;
      line-height: 1.55;
      color: var(--muted);
      font-size: 0.92rem;
    }
  `]
})
export class WelcomePopupComponent {
  constructor(public ui: UiService) {}

  close() {
    this.ui.hideWelcomePopup();
  }
}
