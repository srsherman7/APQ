import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import {
  Observable,
  BehaviorSubject,
  throwError,
  timer,
  from,
  EMPTY
} from 'rxjs';
import {
  catchError,
  retry,
  timeout,
  tap,
  switchMap,
  filter,
  take
} from 'rxjs/operators';
import { environment } from '../../environments/environment';

// ─── Interfaces ──────────────────────────────────────────────────────────────

export interface SessionState {
  session_id: string;
  user_id: number;
  answered_question_ids: number[];
  current_difficulty_level: number;
  current_performance_score: number;
  current_question_id: number | null;
  is_drill_mode: boolean;
  drill_mode_topics: string[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface SaveSessionPayload {
  answered_question_ids?: number[];
  current_difficulty_level?: number;
  current_performance_score?: number;
  current_question_id?: number | null;
  is_drill_mode?: boolean;
  drill_mode_topics?: string[];
}

interface CreateSessionResponse {
  session: SessionState;
  message: string;
}

interface SaveSessionResponse {
  success: boolean;
  message: string;
}

interface RestoreSessionResponse {
  session: SessionState;
  message: string;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const LOCAL_STORAGE_KEY = 'apq_session_state';
const LOCAL_STORAGE_TIMESTAMP_KEY = 'apq_session_timestamp';
const LOCAL_STORAGE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const REQUEST_TIMEOUT_MS = 10_000;
const MAX_RETRY_ATTEMPTS = 3;
const SYNC_INTERVAL_MS = 30_000; // 30 seconds

// ─── Service ─────────────────────────────────────────────────────────────────

/**
 * SessionService manages the lifecycle of a user's practice session.
 *
 * Responsibilities:
 * - Create / restore / save sessions via the backend API
 * - Keep an in-memory copy of the current session state for components
 * - Fall back to localStorage when the network is unavailable (Req 12.4)
 * - Automatically sync the locally-preserved state back to the backend
 *   once connectivity is restored (Req 12.8)
 */
@Injectable({
  providedIn: 'root'
})
export class SessionService {
  private readonly apiUrl = `${environment.apiBaseUrl}/session`;

  /** In-memory session state exposed to components via an Observable. */
  private readonly sessionStateSubject = new BehaviorSubject<SessionState | null>(null);
  readonly sessionState$ = this.sessionStateSubject.asObservable();

  /** Tracks whether a pending local-state sync is in progress. */
  private syncInProgress = false;

  /** Number of consecutive sync failures (reset on success). */
  private syncFailureCount = 0;

  constructor(private readonly http: HttpClient) {}

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Returns the current in-memory session state snapshot.
   * Useful for synchronous access inside components.
   */
  get currentSession(): SessionState | null {
    return this.sessionStateSubject.getValue();
  }

  /**
   * Creates a new practice session (POST /api/session/new).
   *
   * On success the new session is stored in memory and any stale
   * localStorage entry is cleared.
   *
   * Requirements: 4.5, 4.7
   */
  createSession(): Observable<SessionState> {
    return this.http
      .post<CreateSessionResponse>(`${this.apiUrl}/new`, {})
      .pipe(
        timeout(REQUEST_TIMEOUT_MS),
        retry({ count: MAX_RETRY_ATTEMPTS, delay: 1000 }),
        tap(response => {
          this.updateMemoryState(response.session);
          this.clearLocalStorage();
        }),
        switchMap(response => from([response.session])),
        catchError(err => this.handleError(err))
      );
  }

  /**
   * Saves the current session state to the backend (POST /api/session/save).
   *
   * If the request fails after retries the state is preserved in
   * localStorage as a fallback (Req 12.4) and auto-sync is scheduled
   * (Req 12.8).
   *
   * Requirements: 4.1, 4.2, 4.9, 4.10
   */
  saveSession(state: SaveSessionPayload): Observable<SaveSessionResponse> {
    const sessionId = this.currentSession?.session_id;
    if (!sessionId) {
      return throwError(() => new Error('No active session to save'));
    }

    // Optimistically update in-memory state
    this.mergeMemoryState(state);

    return this.http
      .post<SaveSessionResponse>(`${this.apiUrl}/save`, {
        session_id: sessionId,
        state
      })
      .pipe(
        timeout(REQUEST_TIMEOUT_MS),
        retry({ count: MAX_RETRY_ATTEMPTS, delay: 1000 }),
        tap(() => {
          // Successful save – clear any stale local copy
          this.clearLocalStorage();
          this.syncFailureCount = 0;
        }),
        catchError(err => {
          // Network / server failure: persist locally and schedule sync
          this.saveToLocalStorage(this.currentSession);
          this.scheduleAutoSync();
          return this.handleError(err);
        })
      );
  }

  /**
   * Restores the most recent active session from the backend
   * (GET /api/session/restore).
   *
   * If the backend is unreachable and a valid local copy exists it is
   * returned instead (Req 12.4).
   *
   * Requirements: 4.4, 12.4
   */
  restoreSession(): Observable<SessionState> {
    return this.http
      .get<RestoreSessionResponse>(`${this.apiUrl}/restore`)
      .pipe(
        timeout(REQUEST_TIMEOUT_MS),
        tap(response => {
          this.updateMemoryState(response.session);
          this.clearLocalStorage();
        }),
        switchMap(response => from([response.session])),
        catchError(err => {
          // Try local storage fallback on network failure
          const local = this.loadFromLocalStorage();
          if (local) {
            this.updateMemoryState(local);
            this.scheduleAutoSync();
            return from([local]);
          }
          return this.handleError(err);
        })
      );
  }

  /**
   * Clears the in-memory state and localStorage.
   * Called when the user explicitly starts a new session.
   *
   * Requirements: 4.7
   */
  clearSession(): void {
    this.sessionStateSubject.next(null);
    this.clearLocalStorage();
  }

  // ── Local Storage Helpers ──────────────────────────────────────────────────

  /**
   * Persists the session state to localStorage with a timestamp.
   * The entry expires after 24 hours (Req 12.5).
   */
  private saveToLocalStorage(state: SessionState | null): void {
    if (!state) return;
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(state));
      localStorage.setItem(LOCAL_STORAGE_TIMESTAMP_KEY, Date.now().toString());
    } catch {
      // localStorage may be unavailable (private browsing, quota exceeded)
    }
  }

  /**
   * Loads the session state from localStorage if it is still within the
   * 24-hour TTL window (Req 12.5).
   */
  private loadFromLocalStorage(): SessionState | null {
    try {
      const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
      const ts = localStorage.getItem(LOCAL_STORAGE_TIMESTAMP_KEY);
      if (!raw || !ts) return null;

      const age = Date.now() - parseInt(ts, 10);
      if (age > LOCAL_STORAGE_TTL_MS) {
        this.clearLocalStorage();
        return null;
      }

      return JSON.parse(raw) as SessionState;
    } catch {
      return null;
    }
  }

  private clearLocalStorage(): void {
    try {
      localStorage.removeItem(LOCAL_STORAGE_KEY);
      localStorage.removeItem(LOCAL_STORAGE_TIMESTAMP_KEY);
    } catch {
      // Ignore
    }
  }

  // ── In-Memory State Helpers ────────────────────────────────────────────────

  private updateMemoryState(state: SessionState): void {
    this.sessionStateSubject.next(state);
  }

  /**
   * Merges a partial state update into the current in-memory session.
   */
  private mergeMemoryState(partial: SaveSessionPayload): void {
    const current = this.currentSession;
    if (!current) return;
    this.sessionStateSubject.next({ ...current, ...partial });
  }

  // ── Auto-Sync ──────────────────────────────────────────────────────────────

  /**
   * Schedules a one-shot attempt to synchronise the locally-preserved
   * session state with the backend after SYNC_INTERVAL_MS (Req 12.8).
   *
   * If the sync fails it is retried up to MAX_RETRY_ATTEMPTS times total
   * before the state is considered unrestorable (Req 12.9).
   */
  private scheduleAutoSync(): void {
    if (this.syncInProgress) return;
    if (this.syncFailureCount >= MAX_RETRY_ATTEMPTS) {
      // Give up – state is unrestorable (Req 12.9)
      return;
    }

    this.syncInProgress = true;

    timer(SYNC_INTERVAL_MS)
      .pipe(
        switchMap(() => {
          const local = this.loadFromLocalStorage();
          if (!local) {
            this.syncInProgress = false;
            return EMPTY;
          }

          const sessionId = local.session_id;
          const statePayload: SaveSessionPayload = {
            answered_question_ids: local.answered_question_ids,
            current_difficulty_level: local.current_difficulty_level,
            current_performance_score: local.current_performance_score,
            current_question_id: local.current_question_id,
            is_drill_mode: local.is_drill_mode,
            drill_mode_topics: local.drill_mode_topics
          };

          return this.http
            .post<SaveSessionResponse>(`${this.apiUrl}/save`, {
              session_id: sessionId,
              state: statePayload
            })
            .pipe(
              timeout(REQUEST_TIMEOUT_MS),
              catchError(() => {
                this.syncFailureCount++;
                this.syncInProgress = false;
                // Retry if under the limit
                if (this.syncFailureCount < MAX_RETRY_ATTEMPTS) {
                  this.scheduleAutoSync();
                }
                return EMPTY;
              })
            );
        }),
        take(1)
      )
      .subscribe({
        next: () => {
          this.clearLocalStorage();
          this.syncFailureCount = 0;
          this.syncInProgress = false;
        },
        error: () => {
          this.syncInProgress = false;
        }
      });
  }

  // ── Error Handling ─────────────────────────────────────────────────────────

  private handleError(err: unknown): Observable<never> {
    if (err instanceof HttpErrorResponse) {
      const message =
        err.error?.error?.message ??
        (err.status === 0
          ? 'Unable to reach the server. Please try again later.'
          : `Server error (${err.status}): ${err.statusText}`);
      return throwError(() => new Error(message));
    }
    if (err instanceof Error && err.name === 'TimeoutError') {
      return throwError(
        () => new Error('Request timed out. Please check your connection.')
      );
    }
    return throwError(() => err);
  }
}
