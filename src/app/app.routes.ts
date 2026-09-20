import { Routes } from '@angular/router';
import { Calculator } from './calculator/calculator';
import { LoginComponent } from './auth/login.component';
import { RegisterComponent } from './auth/register.component';
import { VerifyEmailComponent } from './auth/verify-email.component';
import { HistorialComponent } from './historial/historial.component';
import { authGuard } from './auth/auth.guard';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AnaliticaComponent } from './analitica/analitica.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'registro', component: RegisterComponent },
  { path: 'verificar-correo', component: VerifyEmailComponent },
  { path: 'calculadora', component: Calculator, canActivate: [authGuard] },
  { path: 'historial', component: HistorialComponent, canActivate: [authGuard] },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'analitica', component: AnaliticaComponent, canActivate: [authGuard] },
  { path: '', redirectTo: '/login', pathMatch: 'full' },
];
