import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink],
  template: `
    <main class="auth-page">
      <section class="auth-card card">
        <p class="eyebrow">Huella Carbono</p>
        <h1>Iniciar sesión</h1>
        <p class="subtitle">Entra para calcular, auditar y revisar tus boletas registradas.</p>

        <form (ngSubmit)="login()" class="auth-form">
          <div>
            <label for="username">Usuario o email</label>
            <input id="username" [(ngModel)]="username" name="username" autocomplete="username" required />
          </div>

          <div>
            <label for="password">Contraseña</label>
            <div class="password-field">
              <input
                id="password"
                [(ngModel)]="password"
                name="password"
                [type]="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
              />
              <button
                type="button"
                class="password-toggle"
                (click)="showPassword = !showPassword"
                [attr.aria-label]="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              >
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" [disabled]="submitting">
            {{ submitting ? 'Entrando...' : 'Entrar' }}
          </button>
        </form>

        @if (message) {
          <p class="message">
            {{ message }}
            @if (requiresVerification) {
              <a [routerLink]="['/verificar-correo']" [queryParams]="{ username }">
                Verificar ahora
              </a>
            }
          </p>
        }
        <a routerLink="/registro" class="auth-link">¿No tienes cuenta? Crea una</a>
      </section>
    </main>
  `,
  styles: [`
    .password-field { display: flex; align-items: center; gap: 0.5rem; }
    .password-field input { flex: 1; }
    .password-toggle {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 1.1rem;
      line-height: 1;
      padding: 0.25rem;
    }
  `],
})
export class LoginComponent {
  username = '';
  password = '';
  showPassword = false;
  submitting = false;
  message = '';
  requiresVerification = false;

  constructor(private auth: AuthService, private router: Router, private cdr: ChangeDetectorRef) {}

  login() {
    this.submitting = true;
    this.message = '';
    this.requiresVerification = false;
    this.auth.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.submitting = false;
        this.message = err?.error?.detail || 'Credenciales inválidas.';
        this.requiresVerification = !!err?.error?.requires_verification;
        this.cdr.markForCheck();
      },
    });
  }
}
