import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, catchError, map, Observable, of, tap } from 'rxjs';
import { environment } from '../../environments/environment';

interface AuthResponse {
  user: {
    id: number;
    username: string;
    email: string;
    organizacion_id: number;
    organizacion_nombre: string;
    rol: 'admin' | 'miembro' | null;
  };
}

interface RegisterResponse {
  detail: string;
  username: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = `${environment.apiBaseUrl}/api/auth`;
  private readonly authState = new BehaviorSubject<boolean>(false);
  public readonly isAuthenticated$ = this.authState.asObservable();

  constructor(private http: HttpClient) {
    // Ensures the csrftoken cookie exists before any state-changing request
    // (register/login/logout), which the csrfInterceptor then attaches
    // as the X-CSRFToken header.
    this.http.get(`${this.baseUrl}/csrf/`, { withCredentials: true }).subscribe();
  }

  register(payload: { username: string; email: string; password: string; password_confirm: string }) {
    // Account starts inactive until the emailed code is verified — no session yet.
    return this.http.post<RegisterResponse>(`${this.baseUrl}/register/`, payload, { withCredentials: true });
  }

  verifyEmail(payload: { username: string; codigo: string }) {
    return this.http.post<AuthResponse>(`${this.baseUrl}/verify-email/`, payload, { withCredentials: true }).pipe(
      tap(() => this.authState.next(true))
    );
  }

  resendVerification(payload: { username: string }) {
    return this.http.post<{ detail: string }>(`${this.baseUrl}/resend-verification/`, payload, { withCredentials: true });
  }

  login(payload: { username: string; password: string }) {
    return this.http.post<AuthResponse>(`${this.baseUrl}/login/`, payload, { withCredentials: true }).pipe(
      tap(() => this.authState.next(true))
    );
  }

  logout() {
    return this.http.post(`${this.baseUrl}/logout/`, {}, { withCredentials: true }).pipe(
      tap(() => this.authState.next(false))
    );
  }

  me(): Observable<boolean> {
    return this.http.get<AuthResponse>(`${this.baseUrl}/me/`, { withCredentials: true }).pipe(
      map(() => true),
      catchError(() => of(false))
    );
  }

  checkSession(): Observable<boolean> {
    return this.me().pipe(
      tap((loggedIn) => this.authState.next(loggedIn))
    );
  }
}
