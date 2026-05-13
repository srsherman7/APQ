import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { catchError, retry, timeout } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface ServiceDefinition {
  service_name: string;
  description: string;
}

export interface UseCase {
  title: string;
  description: string;
}

export interface ExamScenario {
  scenario: string;
  answer: string;
}

export interface ComparisonTable {
  traditional_concept: string;
  aws_service: string;
  notes: string;
}

export interface StudyGuide {
  topic: string;
  service_definitions: ServiceDefinition[];
  use_cases: UseCase[];
  exam_scenarios: ExamScenario[];
  comparison_tables: ComparisonTable[];
  generated_at?: string;
}

export interface Cheatsheet {
  id: number | string;
  title: string;
  topic_area: string;
  description: string;
  summary?: string;
  content?: string;
}

export interface StudyGuideResponse {
  study_guide: StudyGuide;
}

export interface CheatsheetsResponse {
  cheatsheets: Cheatsheet[];
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * StudyService handles all study-materials HTTP communication with the backend.
 *
 * Features:
 * - getStudyGuide:    GET /api/study/guide/:topic
 * - getCheatsheets:   GET /api/study/cheatsheets
 * - 30-second request timeout for study guide generation (Requirement 7.2, 7.5)
 * - Automatic retry up to 3 attempts on transient errors
 * - Consistent error normalisation with user-friendly messages
 *
 * Requirements: 7.1–7.9
 */
@Injectable({
  providedIn: 'root'
})
export class StudyService {
  private readonly baseUrl = environment.apiBaseUrl;

  /** Maximum number of retry attempts for failed requests */
  private readonly MAX_RETRIES = 3;

  /**
   * Timeout for study guide generation requests (Req 7.2, 7.5).
   * Study guide generation may take up to 30 seconds.
   */
  private readonly STUDY_GUIDE_TIMEOUT_MS = 30_000;

  /**
   * Timeout for cheatsheet listing requests.
   * Cheatsheets are pre-generated so a shorter timeout is appropriate.
   */
  private readonly CHEATSHEETS_TIMEOUT_MS = 10_000;

  constructor(private http: HttpClient) {}

  /**
   * Retrieves a generated study guide for the specified topic.
   *
   * Calls GET /api/study/guide/:topic
   *
   * The backend may take up to 30 seconds to generate the guide (Req 7.2).
   * If generation exceeds 30 seconds or fails, an error is returned with a
   * user-friendly message (Req 7.5).
   *
   * Requirements: 7.2, 7.3, 7.4, 7.5, 7.7, 7.8, 9.7
   *
   * @param topic  The exam topic area to generate a study guide for
   */
  getStudyGuide(topic: string): Observable<StudyGuideResponse> {
    const encodedTopic = encodeURIComponent(topic);

    return this.http
      .get<StudyGuideResponse>(`${this.baseUrl}/study/guide/${encodedTopic}`)
      .pipe(
        timeout(this.STUDY_GUIDE_TIMEOUT_MS),
        retry({
          count: this.MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        catchError((error) => this.handleError(error, 'study guide'))
      );
  }

  /**
   * Retrieves the list of pre-generated cheatsheets.
   *
   * Calls GET /api/study/cheatsheets
   *
   * The backend returns at least 5 cheatsheets covering exam topic areas (Req 7.6).
   *
   * Requirements: 7.1, 7.6, 7.9, 9.7
   */
  getCheatsheets(): Observable<CheatsheetsResponse> {
    return this.http
      .get<CheatsheetsResponse>(`${this.baseUrl}/study/cheatsheets`)
      .pipe(
        timeout(this.CHEATSHEETS_TIMEOUT_MS),
        retry({
          count: this.MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        catchError((error) => this.handleError(error, 'cheatsheets'))
      );
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Normalises HTTP and timeout errors into a consistent ApiError shape and
   * re-throws as an Observable error so callers can handle them uniformly.
   *
   * For timeout errors a specific message is shown indicating generation failure
   * (Req 7.5). For network/server errors a user-friendly message is provided.
   *
   * Requirements: 7.5, 12.1, 12.3
   *
   * @param error       The raw error from the HTTP pipeline
   * @param resourceName  Human-readable name of the resource being fetched
   */
  private handleError(error: unknown, resourceName: string): Observable<never> {
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
          message:
            serverError?.message ??
            error.message ??
            `Failed to load ${resourceName}. Please try again.`,
          details: serverError?.details
        };
      }
    } else if (error instanceof Error && error.name === 'TimeoutError') {
      // RxJS timeout() operator throws a TimeoutError (Req 7.5)
      apiError = {
        code: 'TIMEOUT',
        message: `Study ${resourceName} generation failed: the request exceeded the 30-second time limit. Please try again.`
      };
    } else {
      apiError = {
        code: 'UNKNOWN_ERROR',
        message: `An unexpected error occurred while loading ${resourceName}. Please try again.`
      };
    }

    return throwError(() => apiError);
  }
}
