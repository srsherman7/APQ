import { Component, OnInit, OnDestroy, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Subject, interval } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatRadioModule } from '@angular/material/radio';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { FormsModule } from '@angular/forms';

import { environment } from '../../../environments/environment';
import { ModuleService } from '../../services/module.service';

interface ExamQuestion {
  question_id: number;
  question_text: string;
  options: string[];
  topic_area: string;
  difficulty_level: number;
}

interface ExamData {
  exam_id: number;
  started_at: string;
  time_limit_seconds: number;
  total_questions: number;
  is_completed: boolean;
  score: number | null;
  total_correct: number | null;
  passed: boolean | null;
}

interface ExamStartResponse {
  exam: ExamData;
  questions: ExamQuestion[];
  message: string;
}

interface ExamSubmitResponse {
  exam: ExamData;
  message: string;
}

type ViewState = 'loading' | 'intro' | 'exam' | 'results';

@Component({
  selector: 'app-exam-mode',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatRadioModule,
    MatDividerModule,
    MatChipsModule,
  ],
  templateUrl: './exam-mode.component.html',
  styleUrl: './exam-mode.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExamModeComponent implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private readonly moduleService = inject(ModuleService);
  private get moduleId(): number { return this.moduleService.getActiveModuleId() || 1; }
  get activeModule() { return this.moduleService.activeModule(); }

  viewState: ViewState = 'intro';
  errorMessage: string | null = null;

  // Exam state
  exam: ExamData | null = null;
  questions: ExamQuestion[] = [];
  answers: Record<string, string> = {};
  currentIndex = 0;

  // Timer
  timeRemaining = 5400; // seconds
  timerDisplay = '90:00';

  // Results
  isSubmitting = false;

  ngOnInit(): void {
    // Check for in-progress exam
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Intro actions ──────────────────────────────────────────────────────────

  startExam(): void {
    this.viewState = 'loading';
    this.errorMessage = null;
    this.cdr.markForCheck();

    this.http.post<ExamStartResponse>(`${environment.apiBaseUrl}/exam/start`, { module_id: this.moduleId })
      .subscribe({
        next: (res) => {
          this.exam = res.exam;
          this.questions = res.questions;
          this.answers = {};
          this.currentIndex = 0;
          this.startTimer();
          this.viewState = 'exam';
          this.cdr.markForCheck();
        },
        error: (err: HttpErrorResponse) => {
          this.errorMessage = err.error?.error?.message ?? 'Failed to start exam';
          this.viewState = 'intro';
          this.cdr.markForCheck();
        }
      });
  }

  // ── Exam navigation ────────────────────────────────────────────────────────

  get currentQuestion(): ExamQuestion | null {
    return this.questions[this.currentIndex] ?? null;
  }

  get answeredCount(): number {
    return Object.keys(this.answers).length;
  }

  get progressPercent(): number {
    return (this.answeredCount / this.questions.length) * 100;
  }

  selectAnswer(answer: string): void {
    if (!this.currentQuestion || !this.exam) return;
    const qid = this.currentQuestion.question_id.toString();
    this.answers[qid] = answer;
    this.cdr.markForCheck();

    // Save to backend
    this.http.post(`${environment.apiBaseUrl}/exam/answer`, {
      exam_id: this.exam.exam_id,
      question_id: this.currentQuestion.question_id,
      answer
    }).subscribe();
  }

  getCurrentAnswer(): string | null {
    if (!this.currentQuestion) return null;
    return this.answers[this.currentQuestion.question_id.toString()] ?? null;
  }

  goToQuestion(index: number): void {
    if (index >= 0 && index < this.questions.length) {
      this.currentIndex = index;
      this.cdr.markForCheck();
    }
  }

  nextQuestion(): void {
    this.goToQuestion(this.currentIndex + 1);
  }

  prevQuestion(): void {
    this.goToQuestion(this.currentIndex - 1);
  }

  // ── Submit ─────────────────────────────────────────────────────────────────

  submitExam(): void {
    if (!this.exam) return;
    this.isSubmitting = true;
    this.cdr.markForCheck();

    this.http.post<ExamSubmitResponse>(`${environment.apiBaseUrl}/exam/submit`, {
      exam_id: this.exam.exam_id
    }).subscribe({
      next: (res) => {
        this.exam = res.exam;
        this.isSubmitting = false;
        this.viewState = 'results';
        this.destroy$.next(); // Stop timer
        this.cdr.markForCheck();
      },
      error: (err: HttpErrorResponse) => {
        this.errorMessage = err.error?.error?.message ?? 'Failed to submit exam';
        this.isSubmitting = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ── Timer ──────────────────────────────────────────────────────────────────

  private startTimer(): void {
    if (!this.exam) return;

    // Calculate remaining time from server start time
    const started = new Date(this.exam.started_at).getTime();
    const now = Date.now();
    const elapsed = Math.floor((now - started) / 1000);
    this.timeRemaining = Math.max(0, this.exam.time_limit_seconds - elapsed);
    this.updateTimerDisplay();

    interval(1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.timeRemaining--;
        this.updateTimerDisplay();
        if (this.timeRemaining <= 0) {
          this.submitExam(); // Auto-submit when time runs out
        }
        this.cdr.markForCheck();
      });
  }

  private updateTimerDisplay(): void {
    const mins = Math.floor(this.timeRemaining / 60);
    const secs = this.timeRemaining % 60;
    this.timerDisplay = `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  // ── Results ────────────────────────────────────────────────────────────────

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  retakeExam(): void {
    this.viewState = 'intro';
    this.exam = null;
    this.questions = [];
    this.answers = {};
    this.currentIndex = 0;
    this.cdr.markForCheck();
  }
}
