import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, timer, of } from 'rxjs';
import { catchError, retry, timeout, tap, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ─── Interfaces ──────────────────────────────────────────────────────────────

/** Raw topic score entry returned by the backend. */
export interface TopicScore {
  correct: number;
  total: number;
  score: number;
}

/** Weak area entry returned by the backend. */
export interface WeakArea {
  topic: string;
  score: number;
  attempt_count: number;
  correct_count: number;
}

/** Single session entry in the history list. */
export interface SessionHistoryEntry {
  session_id: string;
  date: string;
  score: number;
  questions_answered: number;
  is_drill_mode: boolean;
  is_active: boolean;
}

/** Full performance profile returned by GET /api/analytics/profile. */
export interface PerformanceProfile {
  overall_performance_score: number;
  total_questions_answered: number;
  topic_scores: Record<string, TopicScore>;
  weak_areas: WeakArea[];
  session_history: SessionHistoryEntry[];
  last_updated: string | null;
}

/** Response shape for GET /api/analytics/history. */
export interface SessionHistoryResponse {
  sessions: SessionHistoryEntry[];
}

// ─── Chart-ready DTOs ─────────────────────────────────────────────────────────

/** Topic performance data shaped for bar/radar chart display. */
export interface TopicChartData {
  topic: string;
  score: number;
  correct: number;
  total: number;
  isWeakArea: boolean;
}

/** Session history data shaped for line/bar chart display. */
export interface SessionChartData {
  label: string;       // e.g. "Session 1" or formatted date
  date: string;        // ISO 8601 date string
  score: number;
  questionsAnswered: number;
  isDrillMode: boolean;
}

/** Transformed analytics data ready for chart components. */
export interface AnalyticsChartData {
  topicPerformance: TopicChartData[];
  sessionTrend: SessionChartData[];
  overallScore: number;
  totalQuestionsAnswered: number;
  weakAreaCount: number;
}

// ─── Cache entry ──────────────────────────────────────────────────────────────

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const CACHE_TTL_MS = 60_000;          // 60-second TTL (Req 15.4)
const REQUEST_TIMEOUT_MS = 10_000;    // 10-second timeout (Req 12.3)
const MAX_RETRIES = 3;                // Up to 3 retry attempts (Req 12.2)

// ─── Service ─────────────────────────────────────────────────────────────────

/**
 * AnalyticsService provides access to user performance data and session history.
 *
 * Responsibilities:
 * - Fetch performance profile via GET /api/analytics/profile
 * - Fetch session history via GET /api/analytics/history
 * - Transform raw API data into chart-ready DTOs
 * - Cache responses for 60 seconds to reduce redundant network calls (Req 15.4)
 *
 * Requirements: 5.1–5.10
 */
@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private readonly apiUrl = `${environment.apiBaseUrl}/analytics`;

  /** In-memory cache keyed by cache key string. */
  private readonly cache = new Map<string, CacheEntry<unknown>>();

  constructor(private readonly http: HttpClient) {}

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Retrieves the full performance profile for the authenticated user.
   *
   * Calls GET /api/analytics/profile.
   * Results are cached for 60 seconds.
   *
   * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.9, 5.10
   */
  getPerformanceProfile(): Observable<PerformanceProfile> {
    const cacheKey = 'profile';
    const cached = this.getFromCache<PerformanceProfile>(cacheKey);
    if (cached !== null) {
      return of(cached);
    }

    return this.http
      .get<PerformanceProfile>(`${this.apiUrl}/profile`)
      .pipe(
        timeout(REQUEST_TIMEOUT_MS),
        retry({
          count: MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        tap(data => this.setCache(cacheKey, data)),
        catchError(err => this.handleError(err))
      );
  }

  /**
   * Retrieves session history for the authenticated user.
   *
   * Calls GET /api/analytics/history?limit=<limit>.
   * Results are cached for 60 seconds per unique limit value.
   *
   * @param limit Maximum number of sessions to return (1–100, default 20).
   *
   * Requirements: 5.8
   */
  getSessionHistory(limit: number = 20): Observable<SessionHistoryEntry[]> {
    const cacheKey = `history:${limit}`;
    const cached = this.getFromCache<SessionHistoryEntry[]>(cacheKey);
    if (cached !== null) {
      return of(cached);
    }

    const params = new HttpParams().set('limit', limit.toString());

    return this.http
      .get<SessionHistoryResponse>(`${this.apiUrl}/history`, { params })
      .pipe(
        timeout(REQUEST_TIMEOUT_MS),
        retry({
          count: MAX_RETRIES,
          delay: (_error, retryCount) => timer(retryCount * 500)
        }),
        map(response => response.sessions),
        tap(sessions => this.setCache(cacheKey, sessions)),
        catchError(err => this.handleError(err))
      );
  }

  /**
   * Fetches the performance profile and transforms it into chart-ready data.
   *
   * Combines topic performance and session trend data into a single DTO
   * suitable for passing directly to chart components.
   *
   * Requirements: 5.1, 5.4, 5.5, 5.6, 5.8, 5.9
   */
  getAnalyticsChartData(): Observable<AnalyticsChartData> {
    return this.getPerformanceProfile().pipe(
      map(profile => this.transformToChartData(profile)),
      catchError(err => this.handleError(err))
    );
  }

  /**
   * Transforms a raw PerformanceProfile into TopicChartData array.
   *
   * Marks each topic as a weak area when it appears in the weak_areas list.
   *
   * Requirements: 5.4, 5.5, 5.6
   */
  transformTopicScores(profile: PerformanceProfile): TopicChartData[] {
    const weakTopics = new Set(profile.weak_areas.map(w => w.topic));

    return Object.entries(profile.topic_scores).map(([topic, ts]) => ({
      topic,
      score: ts.score,
      correct: ts.correct,
      total: ts.total,
      isWeakArea: weakTopics.has(topic)
    }));
  }

  /**
   * Transforms a session history array into SessionChartData array.
   *
   * Labels each entry with a human-readable date string.
   *
   * Requirements: 5.8
   */
  transformSessionHistory(sessions: SessionHistoryEntry[]): SessionChartData[] {
    return sessions.map((session, index) => ({
      label: session.date
        ? new Date(session.date).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric'
          })
        : `Session ${index + 1}`,
      date: session.date,
      score: session.score,
      questionsAnswered: session.questions_answered,
      isDrillMode: session.is_drill_mode
    }));
  }

  /**
   * Invalidates all cached analytics data.
   *
   * Should be called when the user starts a new session or submits an answer
   * so that stale data is not displayed.
   *
   * Requirements: 15.5
   */
  invalidateCache(): void {
    this.cache.clear();
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  /**
   * Combines topic and session data from a PerformanceProfile into a single
   * AnalyticsChartData object.
   */
  private transformToChartData(profile: PerformanceProfile): AnalyticsChartData {
    return {
      topicPerformance: this.transformTopicScores(profile),
      sessionTrend: this.transformSessionHistory(profile.session_history),
      overallScore: profile.overall_performance_score,
      totalQuestionsAnswered: profile.total_questions_answered,
      weakAreaCount: profile.weak_areas.length
    };
  }

  // ── Cache helpers ──────────────────────────────────────────────────────────

  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    return entry.data;
  }

  private setCache<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      expiresAt: Date.now() + CACHE_TTL_MS
    });
  }

  // ── Error handling ─────────────────────────────────────────────────────────

  /**
   * Normalises HTTP and timeout errors into a consistent shape and re-throws
   * as an Observable error so callers can handle them uniformly.
   *
   * Requirements: 12.1, 12.3
   */
  private handleError(error: unknown): Observable<never> {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 0) {
        return throwError(() => new Error(
          'Unable to reach the server. Please check your connection and try again.'
        ));
      }
      const serverError = error.error?.error;
      const message = serverError?.message ?? error.message ?? 'An unexpected error occurred.';
      return throwError(() => new Error(message));
    }

    if (error instanceof Error && error.name === 'TimeoutError') {
      return throwError(() => new Error(
        'The request timed out after 10 seconds. Please try again.'
      ));
    }

    return throwError(() => error);
  }
}
