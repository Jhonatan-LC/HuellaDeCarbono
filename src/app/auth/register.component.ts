import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink],
  template: `
    <main class="auth-page">
      <section class="auth-card card">
        <p class="eyebrow">Huella Carbono</p>
        <h1>Crear cuenta</h1>
        <p class="subtitle">Guarda tus mediciones mensuales y mantén un historial auditable.</p>

        <form (ngSubmit)="register()" class="auth-form">
          <div>
            <label for="username">Usuario</label>
            <input id="username" [(ngModel)]="username" name="username" autocomplete="username" required />
          </div>

          <div>
            <label for="email">Email</label>
            <input id="email" [(ngModel)]="email" name="email" type="email" autocomplete="email" required />
          </div>

          <div>
            <label for="password">Contraseña</label>
            <div class="password-field">
              <input
                id="password"
                [(ngModel)]="password"
                name="password"
                [type]="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                minlength="8"
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

          <div>
            <label for="passwordConfirm">Confirmar contraseña</label>
            <div class="password-field">
              <input
                id="passwordConfirm"
                [(ngModel)]="passwordConfirm"
                name="passwordConfirm"
                [type]="showPasswordConfirm ? 'text' : 'password'"
                autocomplete="new-password"
                required
              />
              <button
                type="button"
                class="password-toggle"
                (click)="showPasswordConfirm = !showPasswordConfirm"
                [attr.aria-label]="showPasswordConfirm ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              >
                {{ showPasswordConfirm ? '🙈' : '👁️' }}
              </button>
            </div>
            <p class="field-error" *ngIf="passwordConfirm && password !== passwordConfirm">
              Las contraseñas no coinciden.
            </p>
          </div>

          <button type="submit" class="btn btn-primary" [disabled]="submitting">
            {{ submitting ? 'Creando cuenta...' : 'Registrarme' }}
          </button>
        </form>

        <p class="message" *ngIf="message">{{ message }}</p>
        <a routerLink="/login" class="auth-link">¿Ya tienes cuenta? Inicia sesión</a>
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
    .field-error { color: #c0392b; font-size: 0.85rem; margin: 0.25rem 0 0; }
  `],
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  passwordConfirm = '';
  showPassword = false;
  showPasswordConfirm = false;
  submitting = false;
  message = '';

  constructor(private auth: AuthService, private router: Router) {}

  register() {
    if (this.password !== this.passwordConfirm) {
      this.message = 'Las contraseñas no coinciden.';
      return;
    }

    this.submitting = true;
    this.message = '';
    this.auth
      .register({
        username: this.username,
        email: this.email,
        password: this.password,
        password_confirm: this.passwordConfirm,
      })
      .subscribe({
        next: () => {
          this.router.navigate(['/verificar-correo'], { queryParams: { username: this.username } });
        },
        error: (err) => {
          this.submitting = false;
          this.message = err?.error?.detail || 'No se pudo crear la cuenta.';
        },
      });
  }
}
