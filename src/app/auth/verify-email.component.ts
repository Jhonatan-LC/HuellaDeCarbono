import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink],
  template: `
    <main class="auth-page">
      <section class="auth-card card">
        <p class="eyebrow">Huella Carbono</p>
        <h1>Verifica tu correo</h1>
        <p class="subtitle">
          Enviamos un código de 6 dígitos a la casilla asociada a <strong>{{ username }}</strong>.
          Ingrésalo para activar tu cuenta.
        </p>

        <form (ngSubmit)="verify()" class="auth-form">
          <div>
            <label for="codigo">Código de verificación</label>
            <input
              id="codigo"
              [(ngModel)]="codigo"
              name="codigo"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              required
            />
          </div>

          <button type="submit" class="btn btn-primary" [disabled]="submitting || !username">
            {{ submitting ? 'Verificando...' : 'Verificar' }}
          </button>
        </form>

        <button type="button" class="auth-link resend-btn" (click)="resend()" [disabled]="resending || !username">
          {{ resending ? 'Enviando...' : '¿No llegó? Reenviar código' }}
        </button>

        <p class="message" *ngIf="message">{{ message }}</p>
        <a routerLink="/login" class="auth-link">Volver a inicio de sesión</a>
      </section>
    </main>
  `,
  styles: [`
    .resend-btn {
      background: none;
      border: none;
      cursor: pointer;
      display: block;
      margin: 0.5rem 0;
      padding: 0;
      text-decoration: underline;
    }
    .resend-btn:disabled { cursor: default; opacity: 0.6; }
  `],
})
export class VerifyEmailComponent {
  username = '';
  codigo = '';
  submitting = false;
  resending = false;
  message = '';

  constructor(private auth: AuthService, private router: Router, private route: ActivatedRoute) {
    this.username = this.route.snapshot.queryParamMap.get('username') || '';
  }

  verify() {
    this.submitting = true;
    this.message = '';
    this.auth.verifyEmail({ username: this.username, codigo: this.codigo }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.submitting = false;
        this.message = err?.error?.detail || 'No se pudo verificar el código.';
      },
    });
  }

  resend() {
    this.resending = true;
    this.message = '';
    this.auth.resendVerification({ username: this.username }).subscribe({
      next: (res) => {
        this.resending = false;
        this.message = res.detail;
      },
      error: (err) => {
        this.resending = false;
        this.message = err?.error?.detail || 'No se pudo reenviar el código.';
      },
    });
  }
}
