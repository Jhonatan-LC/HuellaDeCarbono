import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, CommonModule, RouterLink],
  template: `
    <main class="auth-page">
      <section class="auth-card card">
        <p class="eyebrow">Huella Carbono</p>
        <h1>Iniciar sesión</h1>
        <p class="subtitle">Entra para calcular, auditar y revisar tus boletas registradas.</p>

        <form (ngSubmit)="login()" class="auth-form">
          <div>
            <label for="username">Usuario</label>
            <input id="username" [(ngModel)]="username" name="username" autocomplete="username" required />
          </div>

          <div>
            <label for="password">Contraseña</label>
            <input id="password" [(ngModel)]="password" name="password" type="password" autocomplete="current-password" required />
          </div>

          <button type="submit" class="btn btn-primary">Entrar</button>
        </form>

        <p class="message" *ngIf="message">{{ message }}</p>
        <a routerLink="/registro" class="auth-link">¿No tienes cuenta? Crea una</a>
      </section>
    </main>
  `,
})
export class LoginComponent {
  username = '';
  password = '';
  message = '';

  constructor(private auth: AuthService, private router: Router) {}

  login() {
    this.auth.login({ username: this.username, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.message = 'Credenciales inválidas.';
      }
    });
  }
}
