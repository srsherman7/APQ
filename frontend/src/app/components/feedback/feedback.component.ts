import { Component, Input, Output, EventEmitter, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { QuestionService, FeedbackData, QuestionData } from '../../services/question.service';

/**
 * FeedbackComponent displays the result of an answer submission.
 *
 * Features:
 * - Correctness indicator (correct / incorrect) — Requirement 3.1
 * - Correct answer display — Requirement 3.2
 * - Explanation of the correct answer — Requirement 3.3
 * - Explanation of why the selected answer was wrong (when applicable) — Requirement 3.4
 * - Memory technique / mnemonic device — Requirement 3.5
 * - IT context mapping (traditional on-premises equivalent) — Requirements 8.1, 8.2
 * - "Next Question" button — Requirement 3.6
 * - Preloads the next question while the user reviews feedback — Requirement 15.6
 *
 * Usage:
 * ```html
 * <app-feedback
 *   [feedback]="feedbackData"
 *   [sessionId]="currentSessionId"
 *   [preloadedNextQuestion]="nextQuestion"
 *   (nextQuestion)="onNextQuestion($event)"
 * ></app-feedback>
 * ```
 */
@Component({
  selector: 'app-feedback',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  templateUrl: './feedback.component.html',
  styleUrl: './feedback.component.scss',
})
export class FeedbackComponent implements OnInit, OnDestroy {
  private readonly questionService = inject(QuestionService);
  private readonly destroy$ = new Subject<void>();

  // ── Inputs ──────────────────────────────────────────────────────────────────

  /** Feedback data returned from the answer submission API. */
  @Input({ required: true }) feedback!: FeedbackData;

  /**
   * The active session ID, used to preload the next question.
   * Requirement 15.6: preload next question while user reviews feedback.
   */
  @Input({ required: true }) sessionId!: string;

  /**
   * Optional: next question already preloaded by the parent component.
   * When provided, the component skips its own preload request.
   */
  @Input() preloadedNextQuestion: QuestionData | null = null;

  /**
   * Current difficulty level, forwarded to the preload request so the
   * backend selects an appropriately-levelled question.
   */
  @Input() currentDifficulty: number | undefined = undefined;

  // ── Outputs ─────────────────────────────────────────────────────────────────

  /**
   * Emitted when the user clicks "Next Question".
   * Carries the preloaded QuestionData (or null if preloading failed /
   * no more questions remain).
   *
   * Requirement 3.6: provide a button to proceed to the next question.
   */
  @Output() nextQuestion = new EventEmitter<QuestionData | null>();

  // ── Component state ─────────────────────────────────────────────────────────

  /** Preloaded next question (may arrive asynchronously). */
  preloadedQuestion: QuestionData | null = null;

  /** Whether the preload request is still in flight. */
  isPreloading = false;

  /** Error message shown when preloading fails. */
  preloadError: string | null = null;

  // ── Lifecycle ────────────────────────────────────────────────────────────────

  ngOnInit(): void {
    if (this.preloadedNextQuestion !== null) {
      // Parent already supplied the next question (e.g. from the answer API response)
      this.preloadedQuestion = this.preloadedNextQuestion;
    } else {
      // Requirement 15.6: preload next question in the background
      this.preloadNextQuestion();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Public methods ───────────────────────────────────────────────────────────

  /**
   * Handles the "Next Question" button click.
   *
   * Emits the preloaded question (or null when none is available) so the
   * parent component can transition to the question view.
   *
   * Requirement 3.6
   */
  onNextQuestion(): void {
    this.nextQuestion.emit(this.preloadedQuestion);
  }

  // ── Private helpers ──────────────────────────────────────────────────────────

  /**
   * Preloads the next question from the backend while the user reads the
   * feedback, so the transition to the next question feels instant.
   *
   * Requirement 15.6
   */
  private preloadNextQuestion(): void {
    this.isPreloading = true;
    this.preloadError = null;

    this.questionService
      .getNextQuestion(this.sessionId, this.currentDifficulty)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.preloadedQuestion = response.question;
          this.isPreloading = false;
        },
        error: () => {
          // Preload failure is non-fatal; the user can still proceed and the
          // parent will fetch the question on demand.
          this.preloadedQuestion = null;
          this.isPreloading = false;
          this.preloadError =
            'Could not preload the next question. It will be fetched when you continue.';
        },
      });
  }
}
