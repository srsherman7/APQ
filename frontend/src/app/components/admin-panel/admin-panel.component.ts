import { Component, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { environment } from '../../../environments/environment';
import { AnalyticsService } from '../../services/analytics.service';
import { SessionService } from '../../services/session.service';

interface ResetResponse {
  message: string;
}

/**
 * AdminPanelComponent provides a "Reset Progress" button that clears
 * all sessions, attempts, and analytics for the current user.
 */
@Component({
  selector: 'app-admin-panel',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
  ],
  templateUrl: './admin-panel.component.html',
  styleUrl: './admin-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AdminPanelComponent {
  private readonly http = inject(HttpClient);
  private readonly analyticsService = inject(AnalyticsService);
  private readonly sessionService = inject(SessionService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  isResetting = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;
  confirmed = false;

  /** First click arms the button; second click fires the reset. */
  onResetClick(): void {
    if (!this.confirmed) {
      this.confirmed = true;
      this.cdr.markForCheck();
      return;
    }
    this.resetProgress();
  }

  cancel(): void {
    this.confirmed = false;
    this.errorMessage = null;
    this.successMessage = null;
    this.cdr.markForCheck();
  }

  goToPractice(): void {
    this.router.navigate(['/questions']);
  }

  private resetProgress(): void {
    this.isResetting = true;
    this.successMessage = null;
    this.errorMessage = null;
    this.confirmed = false;
    this.cdr.markForCheck();

    this.http.post<ResetResponse>(`${environment.apiBaseUrl}/session/reset`, {})
      .subscribe({
        next: (res) => {
          this.successMessage = res.message;
          this.isResetting = false;
          // Clear local state
          this.analyticsService.invalidateCache();
          this.sessionService.clearSession();
          this.cdr.markForCheck();
        },
        error: (err: HttpErrorResponse) => {
          this.errorMessage = err.error?.error?.message
            ?? err.message
            ?? 'Reset failed. Please try again.';
          this.isResetting = false;
          this.cdr.markForCheck();
        }
      });
  }
}
