import { Routes } from '@angular/router';
import { Calculator } from './calculator/calculator';
import { LoginComponent } from './auth/login.component';
import { RegisterComponent } from './auth/register.component';
import { HistorialComponent } from './historial/historial.component';
import { authGuard } from './auth/auth.guard';
import { DashboardComponent } from './dashboard/dashboard.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'registro', component: RegisterComponent },
  { path: 'calculadora', component: Calculator, canActivate: [authGuard] },
  { path: 'historial', component: HistorialComponent, canActivate: [authGuard] },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
];
