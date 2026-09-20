import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../auth/auth.service';
import { ThemeService } from './theme.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav class="topbar" aria-label="Navegación principal">
      <div class="topbar-inner">
        <a class="brand" routerLink="/dashboard">
          <span class="brand-mark">HC</span>
          <span>Huella Carbono</span>
        </a>
        <div class="nav-links">
          <a class="nav-link" routerLink="/dashboard" routerLinkActive="active">Dashboard</a>
          <a class="nav-link" routerLink="/calculadora" routerLinkActive="active">Calculadora</a>
          <a class="nav-link" routerLink="/historial" routerLinkActive="active">Historial</a>
          <a class="nav-link" routerLink="/analitica" routerLinkActive="active">Analítica</a>
          <button
            type="button"
            class="nav-link theme-toggle"
            (click)="theme.toggle()"
            [attr.aria-label]="theme.current() === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
          >
            {{ theme.current() === 'dark' ? '☀️' : '🌙' }}
          </button>
          <button type="button" class="nav-link nav-link-logout" (click)="logout()">Salir</button>
        </div>
      </div>
    </nav>
  `,
  styles: [`
    :host {
      display: block;
    }
    button.nav-link {
      border: 1px solid var(--line-strong);
      background: transparent;
      cursor: pointer;
      font: inherit;
    }
    .theme-toggle {
      padding: 0.5rem 0.65rem;
      line-height: 1;
    }
  `]
})
export class TopbarComponent {
  constructor(private auth: AuthService, private router: Router, public theme: ThemeService) {}

  logout() {
    this.auth.logout().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => this.router.navigate(['/login']),
    });
  }
}
