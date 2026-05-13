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
 * RegisterComponent provides a form for new users to create an account.
 *
 * On successful registration a success message is displayed and the user
 * is redirected to the login page after a short delay.
 *
 * Requirements: 14.1, 14.2, 14.5
 */
@Component({
  selector: 'app-register',
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
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();

  /** Reactive form group for the registration form */
  registerForm: FormGroup = this.fb.group({
    username: [
      '',
      [Validators.required, Validators.minLength(3), Validators.maxLength(30)],
    ],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  /** Whether a registration request is in flight */
  isLoading = false;

  /** Error message to display when registration fails */
  errorMessage: string | null = null;

  /** Success message to display after successful registration */
  successMessage: string | null = null;

  /** Controls password field visibility */
  hidePassword = true;

  /**
   * Submits the registration form.
   *
   * Requirement 14.1: Registration form with username, email, and password fields.
   * Requirement 14.2: Client-side validation for all fields.
   * Requirement 14.5: Display success message and redirect to /login on success.
   */
  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.successMessage = null;

    const { username, email, password } = this.registerForm.value as {
      username: string;
      email: string;
      password: string;
    };

    this.authService
      .register(username, email, password)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isLoading = false;
          // Requirement 14.5: display success message and redirect to /login
          this.successMessage =
            'Account created successfully! Redirecting to sign in…';
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 2000);
        },
        error: (err: HttpErrorResponse) => {
          this.isLoading = false;
          if (err.status === 409) {
            this.errorMessage =
              err.error?.message ?? 'Username or email is already in use.';
          } else if (err.status === 400) {
            this.errorMessage =
              err.error?.message ?? 'Invalid registration data. Please check your inputs.';
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
