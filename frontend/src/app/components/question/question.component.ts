import { Component, OnInit, OnDestroy, inject, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatRadioModule } from '@angular/material/radio';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

import {
  QuestionService,
  QuestionData,
  SubmitAnswerResponse,
  ApiError
} from '../../services/question.service';
import { SessionService } from '../../services/session.service';

/**
 * QuestionComponent displays a single exam question with radio-button answer
 * options and handles answer submission.
 *
 * Features:
 * - Renders question text, all answer options, and question number (Req 1.2)
 * - Radio buttons for single-answer selection (Req 1.5)
 * - Visual feedback for the currently selected option (Req 1.6)
 * - Submit button to confirm the selected answer (Req 1.7)
 * - Error message when submit is clicked with no answer selected (Req 1.8)
 * - Loading and error states during submission
 *
 * Requirements: 1.2, 1.5, 1.6, 1.7, 1.8
 */
@Component({
  selector: 'app-question',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatRadioModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
  ],
  templateUrl: './question.component.html',
  styleUrl: './question.component.scss',
})
export class QuestionComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly questionService = inject(QuestionService);
  private readonly sessionService = inject(SessionService);
  private readonly destroy$ = new Subject<void>();

  /** The question data to display. When null the component shows a loading state. */
  @Input() question: QuestionData | null = null;

  /** 1-based question number shown in the header (e.g. "Question 3"). */
  @Input() questionNumber = 1;

  /** Emitted when the answer is successfully submitted. Carries the full response. */
  @Output() answerSubmitted = new EventEmitter<SubmitAnswerResponse>();

  /** Emitted when a submission error occurs that the parent should handle. */
  @Output() submissionError = new EventEmitter<ApiError>();

  /** Reactive form group containing the single "answer" control. */
  answerForm: FormGroup = this.fb.group({
    answer: [null, Validators.required],
  });

  /** True while a submit request is in flight. */
  isSubmitting = false;

  /**
   * Inline error message shown when the user clicks Submit without selecting
   * an answer (Req 1.8).
   */
  noAnswerError: string | null = null;

  /**
   * Network / server error message shown when the submission request fails.
   */
  submissionErrorMessage: string | null = null;

  ngOnInit(): void {
    // Reset form and error state whenever a new question is loaded
    this.answerForm.reset({ answer: null });
    this.noAnswerError = null;
    this.submissionErrorMessage = null;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Getters ────────────────────────────────────────────────────────────────

  /** The currently selected answer value, or null if nothing is selected. */
  get selectedAnswer(): string | null {
    return this.answerForm.get('answer')?.value ?? null;
  }

  // ── Event Handlers ─────────────────────────────────────────────────────────

  /**
   * Called when the user clicks the Submit button.
   *
   * Validates that an answer has been selected (Req 1.8), then calls
   * QuestionService.submitAnswer() with the active session ID, question ID,
   * and selected answer.
   *
   * Requirements: 1.7, 1.8
   */
  onSubmit(): void {
    // Clear previous errors
    this.noAnswerError = null;
    this.submissionErrorMessage = null;

    // Validate answer selection (Requirement 1.8)
    if (!this.selectedAnswer) {
      this.noAnswerError = 'Please select an answer before submitting.';
      this.answerForm.markAllAsTouched();
      return;
    }

    if (!this.question) {
      return;
    }

    const sessionId = this.sessionService.currentSession?.session_id;
    if (!sessionId) {
      this.submissionErrorMessage = 'No active session. Please refresh the page.';
      return;
    }

    this.isSubmitting = true;

    this.questionService
      .submitAnswer(sessionId, this.question.question_id, this.selectedAnswer)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response: SubmitAnswerResponse) => {
          this.isSubmitting = false;
          this.answerSubmitted.emit(response);
        },
        error: (err: ApiError) => {
          this.isSubmitting = false;
          this.submissionErrorMessage =
            err?.message ?? 'An error occurred while submitting your answer. Please try again.';
          this.submissionError.emit(err);
        },
      });
  }

  /**
   * Called when the user selects a radio option.
   * Clears the "no answer selected" error so it doesn't linger after selection.
   *
   * Requirement 1.6
   */
  onOptionSelected(): void {
    this.noAnswerError = null;
  }
}
