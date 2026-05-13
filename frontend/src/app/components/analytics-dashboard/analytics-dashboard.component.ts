import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTableModule } from '@angular/material/table';
import { MatBadgeModule } from '@angular/material/badge';

import {
  AnalyticsService,
  AnalyticsChartData,
  TopicChartData,
  SessionChartData,
} from '../../services/analytics.service';

/**
 * AnalyticsDashboardComponent visualises user performance metrics.
 *
 * Features:
 * - Current session / overall performance score — Requirement 5.1
 * - Topic-level performance breakdown — Requirement 5.4, 5.5
 * - Weak area highlighting — Requirement 5.6, 5.9
 * - Recent session history (20 most recent) — Requirement 5.8
 * - "No data" message when no sessions exist — Requirement 5.9
 * - Drill mode activation button — Requirement 6.1
 *
 * Requirements: 5.1, 5.4, 5.5, 5.6, 5.8, 5.9
 */
@Component({
  selector: 'app-analytics-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatChipsModule,
    MatDividerModule,
    MatTooltipModule,
    MatTableModule,
    MatBadgeModule,
  ],
  templateUrl: './analytics-dashboard.component.html',
  styleUrl: './analytics-dashboard.component.scss',
})
export class AnalyticsDashboardComponent implements OnInit, OnDestroy {
  private readonly analyticsService = inject(AnalyticsService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();

  // ── Component state ──────────────────────────────────────────────────────

  /** Whether the initial data load is in progress. */
  isLoading = true;

  /** Error message when data fetch fails. */
  errorMessage: string | null = null;

  /** Transformed analytics data ready for display. */
  chartData: AnalyticsChartData | null = null;

  /** Columns shown in the session history table. */
  readonly sessionHistoryColumns: string[] = [
    'date',
    'score',
    'questionsAnswered',
    'mode',
  ];

  // ── Lifecycle ────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.loadAnalytics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Public helpers ───────────────────────────────────────────────────────

  /**
   * Returns true when there is no session history to display.
   * Requirement 5.9: display "no data" message when no sessions exist.
   */
  get hasNoData(): boolean {
    return (
      this.chartData !== null &&
      this.chartData.sessionTrend.length === 0 &&
      this.chartData.totalQuestionsAnswered === 0
    );
  }

  /** Sorted topic performance list — weak areas first, then by score ascending. */
  get sortedTopics(): TopicChartData[] {
    if (!this.chartData) return [];
    return [...this.chartData.topicPerformance].sort((a, b) => {
      if (a.isWeakArea !== b.isWeakArea) return a.isWeakArea ? -1 : 1;
      return a.score - b.score;
    });
  }

  /** Returns a colour class based on score value. */
  scoreClass(score: number): string {
    if (score >= 80) return 'score-good';
    if (score >= 60) return 'score-average';
    return 'score-poor';
  }

  /** Returns a Material colour string for the progress bar. */
  progressBarColor(score: number): 'primary' | 'accent' | 'warn' {
    if (score >= 80) return 'primary';
    if (score >= 60) return 'accent';
    return 'warn';
  }

  /**
   * Navigates to the drill mode route.
   * Requirement 6.1: provide a button to enter Drill_Mode.
   */
  activateDrillMode(): void {
    this.router.navigate(['/drill-mode']);
  }

  /**
   * Navigates back to the main practice session.
   */
  goToPractice(): void {
    this.router.navigate(['/questions']);
  }

  /**
   * Retries the analytics data fetch after an error.
   */
  retry(): void {
    this.errorMessage = null;
    this.loadAnalytics();
  }

  // ── Private helpers ──────────────────────────────────────────────────────

  private loadAnalytics(): void {
    this.isLoading = true;

    this.analyticsService
      .getAnalyticsChartData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.chartData = data;
          this.isLoading = false;
        },
        error: (err: Error) => {
          this.errorMessage =
            err.message ?? 'Failed to load analytics. Please try again.';
          this.isLoading = false;
        },
      });
  }
}
