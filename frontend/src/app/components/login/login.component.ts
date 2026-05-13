import { Component, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { HttpErrorResponse } from '@angular/common/http';

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../services/auth.service';

/**
 * LoginComponent provides a form for users to authenticate with their
 * username/email and password.
 *
 * On successful login the session token is stored by AuthService and the
 * user is redirected to the main application dashboard.
 *
 * Requirements: 14.7, 14.9, 14.13
 */
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();

  /** Reactive form group for the login form */
  loginForm: FormGroup = this.fb.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]],
  });

  /** Whether a login request is in flight */
  isLoading = false;

  /** Error message to display when login fails */
  errorMessage: string | null = null;

  /** Controls password field visibility */
  hidePassword = true;

  /**
   * Submits the login form.
   *
   * Requirement 14.7: Login form with username/email and password fields.
   * Requirement 14.9: Display error message on failed login.
   * Requirement 14.13: Redirect to main application on successful login.
   */
  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const { username, password } = this.loginForm.value as { username: string; password: string };

    this.authService
      .login(username, password)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          // Token is stored by AuthService.login() via tap()
          // Requirement 14.13: redirect to main application on successful login
          this.router.navigate(['/questions']);
        },
        error: (err: HttpErrorResponse) => {
          this.isLoading = false;
          // Requirement 14.9: display error message on failed login
          if (err.status === 401 || err.status === 400) {
            this.errorMessage =
              err.error?.message ?? 'Invalid credentials. Please check your username and password.';
          } else if (err.status === 429) {
            this.errorMessage =
              'Too many failed login attempts. Please wait 15 minutes before trying again.';
          } else {
            this.errorMessage = 'An unexpected error occurred. Please try again later.';
          }
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
