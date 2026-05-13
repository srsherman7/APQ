import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

/** Shape of the login response from the backend */
export interface LoginResponse {
  session_token: string;
  expires_at: string;
}

/** Shape of the register response from the backend */
export interface RegisterResponse {
  user_id: number;
  message: string;
}

/** Shape of the logout response from the backend */
export interface LogoutResponse {
  message: string;
}

/** Key used to store the session token in sessionStorage */
const TOKEN_KEY = 'session_token';

/**
 * AuthService handles user authentication: registration, login, logout,
 * and session token management in sessionStorage.
 *
 * Requirements: 14.1, 14.7, 14.12, 14.14
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly apiUrl = environment.apiBaseUrl;

  /**
   * Registers a new user account.
   *
   * @param username - 3–30 character username
   * @param email    - Valid email address
   * @param password - Minimum 8 character password
   * @returns Observable emitting the registration response
   */
  register(username: string, email: string, password: string): Observable<RegisterResponse> {
    return this.http
      .post<RegisterResponse>(`${this.apiUrl}/register`, { username, email, password })
      .pipe(catchError(this.handleError));
  }

  /**
   * Authenticates a user and stores the returned session token in sessionStorage.
   *
   * @param username - Username or email address
   * @param password - User password
   * @returns Observable emitting the login response (includes session_token)
   */
  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.apiUrl}/login`, { username, password })
      .pipe(
        tap((response) => {
          this.storeToken(response.session_token);
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Logs out the current user by invalidating the session token on the backend
   * and removing it from sessionStorage.
   *
   * @returns Observable emitting the logout response
   */
  logout(): Observable<LogoutResponse> {
    return this.http
      .post<LogoutResponse>(`${this.apiUrl}/logout`, {})
      .pipe(
        tap(() => {
          this.clearToken();
        }),
        catchError((error) => {
          // Always clear the local token even if the backend call fails
          this.clearToken();
          return this.handleError(error);
        })
      );
  }

  /**
   * Returns the session token currently stored in sessionStorage, or null if
   * the user is not authenticated.
   */
  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  /**
   * Returns true when a session token is present in sessionStorage.
   */
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Redirects the user to the login page. Called by the HTTP interceptor when
   * a 401 response is received.
   *
   * Requirement 14.14: When the Frontend receives a 401 response, it SHALL
   * redirect to the login page.
   */
  redirectToLogin(): void {
    this.clearToken();
    this.router.navigate(['/login']);
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private storeToken(token: string): void {
    sessionStorage.setItem(TOKEN_KEY, token);
  }

  private clearToken(): void {
    sessionStorage.removeItem(TOKEN_KEY);
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    return throwError(() => error);
  }
}
