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

// Angular Material
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatDividerModule } from '@angular/material/divider';

import { QuestionComponent } from '../question/question.component';
import { FeedbackComponent } from '../feedback/feedback.component';
import { QuestionService, QuestionData, FeedbackData, SubmitAnswerResponse } from '../../services/question.service';
import { SessionService, SessionState } from '../../services/session.service';
import { AnalyticsService } from '../../services/analytics.service';

type ViewState = 'loading' | 'question' | 'feedback' | 'session-complete' | 'error';

/**
 * PracticeSessionComponent orchestrates the main question → feedback loop.
 *
 * Flow:
 * 1. On init: restore existing session or create a new one
 * 2. Load the first question
 * 3. User answers → show feedback (with preloaded next question)
 * 4. User clicks "Next Question" → show next question
 * 5. When no more questions → show session-complete screen
 *
 * Requirements: 1.1–1.9, 2.1–2.8, 3.1–3.7, 4.1–4.10, 15.4–15.6
 */
@Component({
  selector: 'app-practice-session',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatDividerModule,
    QuestionComponent,
    FeedbackComponent,
  ],
  templateUrl: './practice-session.component.html',
  styleUrl: './practice-session.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PracticeSessionComponent implements OnInit, OnDestroy {
  private readonly sessionService = inject(SessionService);
  private readonly questionService = inject(QuestionService);
  private readonly analyticsService = inject(AnalyticsService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  // ── View state ─────────────────────────────────────────────────────────────

  viewState: ViewState = 'loading';
  errorMessage: string | null = null;

  // ── Session state ──────────────────────────────────────────────────────────

  currentSession: SessionState | null = null;
  questionNumber = 1;

  // ── Question / feedback data ───────────────────────────────────────────────

  currentQuestion: QuestionData | null = null;
  currentFeedback: FeedbackData | null = null;

  /** Next question preloaded by the answer API response (Req 15.6) */
  preloadedNextQuestion: QuestionData | null = null;

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  ngOnInit(): void {
    this.initSession();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Public handlers ────────────────────────────────────────────────────────

  /**
   * Called by QuestionComponent when an answer is successfully submitted.
   * Transitions to the feedback view.
   */
  onAnswerSubmitted(response: SubmitAnswerResponse): void {
    this.currentFeedback = response.feedback;
    this.preloadedNextQuestion = response.next_question;

    // Invalidate analytics cache so dashboard reflects new attempt
    this.analyticsService.invalidateCache();

    this.viewState = 'feedback';
    this.cdr.markForCheck();
  }

  /**
   * Called by FeedbackComponent when the user clicks "Next Question".
   * Transitions back to the question view with the preloaded question,
   * or fetches a new one if preloading failed.
   */
  onNextQuestion(preloaded: QuestionData | null): void {
    if (preloaded) {
      this.currentQuestion = preloaded;
      this.questionNumber++;
      this.currentFeedback = null;
      this.preloadedNextQuestion = null;
      this.viewState = 'question';
      this.cdr.markForCheck();
    } else {
      // No preloaded question — either session complete or need to fetch
      this.fetchNextQuestion();
    }
  }

  /**
   * Starts a brand-new session, discarding the current one.
   * Requirement 4.6, 4.7
   */
  startNewSession(): void {
    this.viewState = 'loading';
    this.errorMessage = null;
    this.questionNumber = 1;
    this.currentQuestion = null;
    this.currentFeedback = null;
    this.preloadedNextQuestion = null;
    this.cdr.markForCheck();

    this.sessionService
      .createSession()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (session) => {
          this.currentSession = session;
          this.fetchNextQuestion();
        },
        error: (err: Error) => {
          this.errorMessage = err.message ?? 'Failed to create a new session. Please try again.';
          this.viewState = 'error';
          this.cdr.markForCheck();
        },
      });
  }

  /**
   * Navigates to the analytics dashboard.
   */
  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  /**
   * Retries after an error.
   */
  retry(): void {
    this.errorMessage = null;
    this.initSession();
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  /**
   * Initialises the session: tries to restore an existing one, falls back to
   * creating a new one.
   */
  private initSession(): void {
    this.viewState = 'loading';
    this.cdr.markForCheck();

    this.sessionService
      .restoreSession()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (session) => {
          this.currentSession = session;
          this.questionNumber = (session.answered_question_ids?.length ?? 0) + 1;
          this.fetchNextQuestion();
        },
        error: () => {
          // No existing session — create a new one
          this.sessionService
            .createSession()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (session) => {
                this.currentSession = session;
                this.questionNumber = 1;
                this.fetchNextQuestion();
              },
              error: (err: Error) => {
                this.errorMessage = err.message ?? 'Failed to start a session. Please try again.';
                this.viewState = 'error';
                this.cdr.markForCheck();
              },
            });
        },
      });
  }

  /**
   * Fetches the next question from the backend.
   * If no question is available, transitions to the session-complete view.
   */
  private fetchNextQuestion(): void {
    const session = this.currentSession ?? this.sessionService.currentSession;
    if (!session) {
      this.errorMessage = 'No active session. Please refresh the page.';
      this.viewState = 'error';
      this.cdr.markForCheck();
      return;
    }

    this.viewState = 'loading';
    this.cdr.markForCheck();

    this.questionService
      .getNextQuestion(session.session_id, session.current_difficulty_level)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response.question) {
            this.currentQuestion = response.question;
            this.currentFeedback = null;
            this.preloadedNextQuestion = null;
            this.viewState = 'question';
          } else {
            // No more questions
            this.viewState = 'session-complete';
          }
          this.cdr.markForCheck();
        },
        error: (err) => {
          // 404 means no questions available → session complete
          if (err?.code === 'HTTP_404' || err?.code === 'NO_QUESTIONS_AVAILABLE') {
            this.viewState = 'session-complete';
          } else {
            this.errorMessage = err?.message ?? 'Failed to load the next question. Please try again.';
            this.viewState = 'error';
          }
          this.cdr.markForCheck();
        },
      });
  }
}
