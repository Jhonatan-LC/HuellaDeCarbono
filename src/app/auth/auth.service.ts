import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, catchError, map, Observable, of, tap } from 'rxjs';

interface AuthResponse {
  user: { id: number; username: string; email: string };
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = 'http://localhost:8000/api/auth';
  private readonly authState = new BehaviorSubject<boolean>(false);
  public readonly isAuthenticated$ = this.authState.asObservable();

  constructor(private http: HttpClient) {}

  register(payload: { username: string; email: string; password: string }) {
    return this.http.post<AuthResponse>(`${this.baseUrl}/register/`, payload, { withCredentials: true }).pipe(
      tap(() => this.authState.next(true))
    );
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
