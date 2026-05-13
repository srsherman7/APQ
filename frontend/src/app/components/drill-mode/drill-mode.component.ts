import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  ChangeDetectionStrategy,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil, finalize } from 'rxjs/operators';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AnalyticsService, WeakArea } from '../../services/analytics.service';
import { SessionService } from '../../services/session.service';
import { environment } from '../../../environments/environment';

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface DrillActivateResponse {
  session: {
    session_id: string;
    is_drill_mode: boolean;
    drill_mode_topics: string[];
    current_difficulty_level: number;
    current_performance_score: number;
  };
  message: string;
  weak_areas: WeakArea[];
}

interface DrillDeactivateResponse {
  session: {
    session_id: string;
    is_drill_mode: boolean;
    drill_mode_topics: string[];
  };
  message: string;
}

/**
 * DrillModeComponent manages focused practice on weak areas.
 *
 * Features:
 * - Displays weak area topics being drilled (Req 6.1, 6.3)
 * - Shows proficiency progress for each weak area (Req 6.6)
 * - Displays message when no weak areas exist (Req 6.4)
 * - Provides exit option to return to normal practice (Req 6.9)
 * - Continues adaptive difficulty adjustment (Req 6.5)
 * - Calls POST /api/drill/activate and /api/drill/deactivate (Req 9.8, 9.9)
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9
 */
@Component({
  selector: 'app-drill-mode',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatChipsModule,
    MatSnackBarModule,
    MatTooltipModule
  ],
  templateUrl: './drill-mode.component.html',
  styleUrl: './drill-mode.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DrillModeComponent implements OnInit, OnDestroy {
  private readonly analyticsService = inject(AnalyticsService);
  private readonly sessionService = inject(SessionService);
  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);
  private readonly snackBar = inject(MatSnackBar);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  private readonly drillApiUrl = `${environment.apiBaseUrl}/drill`;

  // ── State ──────────────────────────────────────────────────────────────────

  /** Whether the component is loading initial data. */
  isLoading = true;

  /** Whether a drill activate/deactivate request is in flight. */
  isActivating = false;

  /** Whether drill mode is currently active. */
  isDrillActive = false;

  /** Weak areas identified for the current user. */
  weakAreas: WeakArea[] = [];

  /** Topics currently being drilled (from session state). */
  drillTopics: string[] = [];

  /** Current difficulty level from session. */
  currentDifficultyLevel = 2;

  /** Error message to display to the user. */
  errorMessage: string | null = null;

  /** Whether all weak areas have been mastered (Req 6.8). */
  allAreasMastered = false;

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.loadInitialState();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Activates drill mode by calling POST /api/drill/activate.
   * On success, updates the component state with weak areas and drill topics.
   *
   * Requirements: 6.1, 6.3, 9.8
   */
  activateDrillMode(): void {
    this.isActivating = true;
    this.errorMessage = null;

    this.http
      .post<DrillActivateResponse>(`${this.drillApiUrl}/activate`, {})
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isActivating = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (response) => {
          this.isDrillActive = true;
          this.weakAreas = response.weak_areas ?? [];
          this.drillTopics = response.session.drill_mode_topics ?? [];
          this.currentDifficultyLevel = response.session.current_difficulty_level;
          this.allAreasMastered = false;

          // Sync session service state
          this.sessionService['mergeMemoryState']?.({
            is_drill_mode: true,
            drill_mode_topics: this.drillTopics,
            current_difficulty_level: this.currentDifficultyLevel
          });

          // Invalidate analytics cache so fresh data is fetched next time
          this.analyticsService.invalidateCache();

          this.snackBar.open(response.message, 'Dismiss', { duration: 4000 });
          this.cdr.markForCheck();
        },
        error: (err: HttpErrorResponse) => {
          if (err.status === 404 && err.error?.error?.code === 'NO_WEAK_AREAS') {
            // No weak areas – show the "all proficient" message (Req 6.4)
            this.weakAreas = [];
            this.isDrillActive = false;
          } else {
            this.errorMessage = this.extractErrorMessage(err);
          }
          this.cdr.markForCheck();
        }
      });
  }

  /**
   * Deactivates drill mode by calling POST /api/drill/deactivate.
   * Returns the user to normal practice mode.
   *
   * Requirements: 6.9, 9.9
   */
  deactivateDrillMode(): void {
    this.isActivating = true;
    this.errorMessage = null;

    this.http
      .post<DrillDeactivateResponse>(`${this.drillApiUrl}/deactivate`, {})
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isActivating = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (response) => {
          this.isDrillActive = false;
          this.drillTopics = [];
          this.allAreasMastered = false;

          // Sync session service state
          this.sessionService['mergeMemoryState']?.({
            is_drill_mode: false,
            drill_mode_topics: []
          });

          this.analyticsService.invalidateCache();

          this.snackBar.open(response.message, 'Dismiss', { duration: 4000 });
          this.cdr.markForCheck();
        },
        error: (err: HttpErrorResponse) => {
          this.errorMessage = this.extractErrorMessage(err);
          this.cdr.markForCheck();
        }
      });
  }

  /**
   * Navigates back to the main practice/question view.
   *
   * Requirement 6.9
   */
  exitToNormalPractice(): void {
    if (this.isDrillActive) {
      this.deactivateDrillMode();
    }
    this.router.navigate(['/questions']);
  }

  /**
   * Returns the proficiency percentage for a given weak area topic.
   * Used to drive the progress bar display.
   *
   * Requirement 6.6
   */
  getProficiencyPercent(topic: string): number {
    const area = this.weakAreas.find(w => w.topic === topic);
    return area ? Math.round(area.score) : 0;
  }

  /**
   * Returns the attempt count for a given weak area topic.
   */
  getAttemptCount(topic: string): number {
    const area = this.weakAreas.find(w => w.topic === topic);
    return area ? area.attempt_count : 0;
  }

  /**
   * Returns the correct answer count for a given weak area topic.
   */
  getCorrectCount(topic: string): number {
    const area = this.weakAreas.find(w => w.topic === topic);
    return area ? area.correct_count : 0;
  }

  /**
   * Returns a colour class for the progress bar based on proficiency score.
   * - < 40%: warn (red)
   * - 40–59%: accent (amber)
   * - ≥ 60%: primary (blue)
   */
  getProgressColor(score: number): 'primary' | 'accent' | 'warn' {
    if (score < 40) return 'warn';
    if (score < 60) return 'accent';
    return 'primary';
  }

  /**
   * Dismisses the current error message.
   */
  dismissError(): void {
    this.errorMessage = null;
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  /**
   * Loads the initial state: checks session for existing drill mode status
   * and fetches the analytics profile to populate weak areas.
   *
   * Exposed as public so the template retry button can call it.
   */
  loadInitialState(): void {
    this.isLoading = true;
    this.errorMessage = null;

    // Check if drill mode is already active from session state
    const session = this.sessionService.currentSession;
    if (session) {
      this.isDrillActive = session.is_drill_mode;
      this.drillTopics = session.drill_mode_topics ?? [];
      this.currentDifficultyLevel = session.current_difficulty_level;
    }

    // Fetch analytics profile to get weak areas with proficiency data
    this.analyticsService
      .getPerformanceProfile()
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isLoading = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (profile) => {
          this.weakAreas = profile.weak_areas ?? [];

          // Check if all weak areas have been mastered (Req 6.8)
          if (this.isDrillActive && this.weakAreas.length === 0) {
            this.allAreasMastered = true;
            this.isDrillActive = false;
          }

          this.cdr.markForCheck();
        },
        error: (err: unknown) => {
          const message =
            err instanceof Error
              ? err.message
              : 'Failed to load performance data. Please try again.';
          this.errorMessage = message;
          this.cdr.markForCheck();
        }
      });
  }

  /**
   * Extracts a human-readable error message from an HttpErrorResponse.
   */
  private extractErrorMessage(err: HttpErrorResponse): string {
    if (err.status === 0) {
      return 'Unable to reach the server. Please check your connection and try again.';
    }
    return (
      err.error?.error?.message ??
      err.message ??
      'An unexpected error occurred. Please try again.'
    );
  }
}
