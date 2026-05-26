import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Module {
  module_id: number;
  slug: string;
  name: string;
  description: string;
  icon: string;
  exam_question_count: number;
  exam_time_limit_seconds: number;
  exam_passing_score: number;
  topic_areas: string[];
  is_active: boolean;
  question_count: number;
}

interface ModulesResponse {
  modules: Module[];
}

interface ModuleResponse {
  module: Module;
}

const STORAGE_KEY = 'apq_active_module';

/**
 * ModuleService manages the active learning module.
 * Persists the selected module in sessionStorage so it survives page refreshes.
 */
@Injectable({
  providedIn: 'root'
})
export class ModuleService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiBaseUrl}/modules`;

  /** The currently active module */
  readonly activeModule = signal<Module | null>(this.loadFromStorage());

  /** Get all available modules */
  getModules(): Observable<ModulesResponse> {
    return this.http.get<ModulesResponse>(`${this.apiUrl}/`);
  }

  /** Get a single module by slug */
  getModule(slug: string): Observable<ModuleResponse> {
    return this.http.get<ModuleResponse>(`${this.apiUrl}/${slug}`);
  }

  /** Set the active module (called when user selects one) */
  setActiveModule(module: Module): void {
    this.activeModule.set(module);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(module));
  }

  /** Clear the active module (go back to module selection) */
  clearActiveModule(): void {
    this.activeModule.set(null);
    localStorage.removeItem(STORAGE_KEY);
  }

  /** Get the active module_id for API calls */
  getActiveModuleId(): number | null {
    return this.activeModule()?.module_id ?? null;
  }

  private loadFromStorage(): Module | null {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }
}
