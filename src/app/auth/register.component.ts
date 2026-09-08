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
            <input id="password" [(ngModel)]="password" name="password" type="password" autocomplete="new-password" required />
          </div>

          <button type="submit" class="btn btn-primary">Registrarme</button>
        </form>

        <p class="message" *ngIf="message">{{ message }}</p>
        <a routerLink="/login" class="auth-link">¿Ya tienes cuenta? Inicia sesión</a>
      </section>
    </main>
  `,
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  message = '';

  constructor(private auth: AuthService, private router: Router) {}

  register() {
    this.auth.register({ username: this.username, email: this.email, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.message = 'No se pudo crear la cuenta.';
      }
    });
  }
}
