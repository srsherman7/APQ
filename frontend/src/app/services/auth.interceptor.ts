import { Injectable, inject } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';

/**
 * AuthInterceptor automatically attaches the session token to every outgoing
 * HTTP request and redirects to the login page when a 401 response is received.
 *
 * Requirements:
 *   14.12 – Automatic token inclusion in HTTP headers
 *   14.14 – 401 response handling with redirect to login
 */
@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private readonly authService = inject(AuthService);

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const token = this.authService.getToken();

    // Clone the request and attach the Authorization header when a token exists
    const authenticatedRequest = token
      ? request.clone({
          setHeaders: {
            Authorization: `Bearer ${token}`
          }
        })
      : request;

    return next.handle(authenticatedRequest).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          // Requirement 14.14: redirect to login on 401
          this.authService.redirectToLogin();
        }
        return throwError(() => error);
      })
    );
  }
}
