import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { catchError, retry, timeout, switchMap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ─── Response interfaces ────────────────────────────────────────────────────

export interface QuestionData {
  question_id: number;
  question_text: string;
  options: string[];
  topic_area: string;
  difficulty_level: number;
}

export interface FeedbackData {
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  incorrect_explanation: string | null;
  memory_technique: string;
  it_context_mapping: string | null;
}

export interface NextQuestionResponse {
  question: QuestionData;
  _response_time_ms?: number;
}

export interface SubmitAnswerResponse {
  feedback: FeedbackData;
  next_question: QuestionData | null;
  _response_time_ms?: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ─── Service ─────────────────────────────────────────────────────────────────

/**
 * QuestionService handles all question-related HTTP communication with the backend.
 *
 * Features:
 * - getNextQuestion: GET /api/question/next
 * - submitAnswer:    POST /api/question/answer
 * - 10-second request timeout (Requirement 12.3)
 * - Automatic retry up to 3 attempts on transient errors (Requirement 12.2)
 * - Consistent error normalisation
 */
@Injectable({
  providedIn: 'root'
})
export class QuestionService {
  private readonly baseUrl = environment.apiBaseUrl;

  /** Maximum number of retry attempts for failed requests (Req 12.2) */
  private readonly MAX_RETRIES = 3;

  /** Request timeout in milliseconds (Req 12.3) */
  private readonly REQUEST_TIMEOUT_MS = 10_000;

  constructor(private http: HttpClient) {}

  /**
   * Retrieves the next question for the given session and difficulty level.
   *
   * Calls GET /api/question/next?session_id=<id>&difficulty=<level>
   *
   * Requirements: 1.1, 1.3, 1.4, 2.4, 9.2, 12.2, 12.3
   *
   * @param sessionId  UUID of the active session
   * @param difficulty Target difficulty level (1–5). Optional – backend uses
   *                   the session's current difficulty when omitted.
   */
  getNextQuestion(sessionId: string, difficulty?: number): Observable<NextQuestionResponse> {
    let params = new HttpParams().set('session_id', sessionId);
    if (difficulty !== undefined && difficulty !== null) {
      params = params.set('difficulty', difficulty.toString());
    }

    return this.http
      .get<NextQuestionResponse>(`${this.baseUrl}/question/next`, { params })
      .pipe(
        timeout(this.REQUEST_TIMEOUT_MS),
        retry({
          count: this.MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * Submits the user's answer for a question and returns feedback plus the
   * next question (if any).
   *
   * Calls POST /api/question/answer with body { session_id, question_id, answer }
   *
   * Requirements: 3.1–3.7, 9.3, 12.2, 12.3
   *
   * @param sessionId  UUID of the active session
   * @param questionId ID of the question being answered
   * @param answer     The answer string selected by the user
   */
  submitAnswer(
    sessionId: string,
    questionId: number,
    answer: string
  ): Observable<SubmitAnswerResponse> {
    const body = {
      session_id: sessionId,
      question_id: questionId,
      answer
    };

    return this.http
      .post<SubmitAnswerResponse>(`${this.baseUrl}/question/answer`, body)
      .pipe(
        timeout(this.REQUEST_TIMEOUT_MS),
        retry({
          count: this.MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        catchError((error) => this.handleError(error))
      );
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Normalises HTTP and timeout errors into a consistent ApiError shape and
   * re-throws as an Observable error so callers can handle them uniformly.
   *
   * Requirements: 12.1, 12.3
   */
  private handleError(error: unknown): Observable<never> {
    let apiError: ApiError;

    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        // Network-level failure (no response received)
        apiError = {
          code: 'NETWORK_ERROR',
          message: 'Unable to reach the server. Please check your connection and try again.'
        };
      } else {
        // Server returned an error response
        const serverError = error.error?.error;
        apiError = {
          code: serverError?.code ?? `HTTP_${error.status}`,
          message: serverError?.message ?? error.message ?? 'An unexpected error occurred.',
          details: serverError?.details
        };
      }
    } else if (
      error instanceof Error &&
      error.name === 'TimeoutError'
    ) {
      // RxJS timeout() operator throws a TimeoutError
      apiError = {
        code: 'TIMEOUT',
        message: 'The request timed out after 10 seconds. Please try again.'
      };
    } else {
      apiError = {
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred. Please try again.'
      };
    }

    return throwError(() => apiError);
  }
}
