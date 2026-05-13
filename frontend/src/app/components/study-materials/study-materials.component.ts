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

// Angular Material imports
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatListModule } from '@angular/material/list';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatBadgeModule } from '@angular/material/badge';

import {
  StudyService,
  Cheatsheet,
  ApiError
} from '../../services/study.service';

// ─── Local interfaces matching the backend's format_study_content response ───

export interface ServiceDefinition {
  name: string;
  description: string;
  key_features: string[];
}

export interface UseCase {
  title: string;
  description: string;
  services: string[];
}

export interface ExamScenario {
  scenario: string;
  correct_approach: string;
  why_it_works: string;
}

export interface ComparisonRow {
  it_concept: string;
  aws_service: string;
  key_difference: string;
}

export interface StudyGuideSection<T> {
  heading: string;
  content: T[];
}

export interface FormattedStudyGuide {
  topic_area: string;
  sections: {
    service_definitions: StudyGuideSection<ServiceDefinition>;
    use_cases: StudyGuideSection<UseCase>;
    exam_scenarios: StudyGuideSection<ExamScenario>;
    comparison_table: StudyGuideSection<ComparisonRow>;
  };
}

/**
 * StudyMaterialsComponent displays pre-generated cheatsheets and allows
 * users to generate on-demand study guides for AWS exam topic areas.
 *
 * Features:
 * - Lists at least 5 pre-generated cheatsheets (Req 7.1, 7.6)
 * - Generates on-demand study guides for selected topics (Req 7.2, 7.3, 7.4)
 * - Organizes content with section headings (Req 7.7, 7.8)
 * - Handles 30-second timeout with error message (Req 7.5)
 * - Provides navigation back to practice (Req 7.9)
 *
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9
 */
@Component({
  selector: 'app-study-materials',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatChipsModule,
    MatExpansionModule,
    MatListModule,
    MatTableModule,
    MatTooltipModule,
    MatBadgeModule,
  ],
  templateUrl: './study-materials.component.html',
  styleUrl: './study-materials.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StudyMaterialsComponent implements OnInit, OnDestroy {
  private readonly studyService = inject(StudyService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  // ── Cheatsheet state ──────────────────────────────────────────────────────

  /** List of available pre-generated cheatsheets (Req 7.6) */
  cheatsheets: Cheatsheet[] = [];

  /** True while cheatsheets are loading */
  cheatsheetsLoading = false;

  /** Error message when cheatsheets fail to load */
  cheatsheetsError: string | null = null;

  // ── Study guide state ─────────────────────────────────────────────────────

  /** The currently displayed study guide (Req 7.3, 7.4, 7.7, 7.8) */
  studyGuide: FormattedStudyGuide | null = null;

  /** True while a study guide is being generated (Req 7.2) */
  studyGuideLoading = false;

  /** Error message when study guide generation fails or times out (Req 7.5) */
  studyGuideError: string | null = null;

  /** The topic currently selected for study guide generation */
  selectedTopic: string | null = null;

  /** Available topic areas for on-demand study guide generation */
  readonly topicAreas: string[] = [
    'Cloud Concepts',
    'Security and Compliance',
    'Technology',
    'Billing and Pricing',
  ];

  /** Column definitions for the comparison table */
  readonly comparisonColumns: string[] = ['it_concept', 'aws_service', 'key_difference'];

  ngOnInit(): void {
    this.loadCheatsheets();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Data loading ──────────────────────────────────────────────────────────

  /**
   * Loads the list of pre-generated cheatsheets from the backend.
   * Requirements: 7.1, 7.6
   */
  loadCheatsheets(): void {
    this.cheatsheetsLoading = true;
    this.cheatsheetsError = null;

    this.studyService
      .getCheatsheets()
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.cheatsheetsLoading = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (response) => {
          this.cheatsheets = response.cheatsheets ?? [];
        },
        error: (err: ApiError) => {
          this.cheatsheetsError =
            err?.message ?? 'Failed to load cheatsheets. Please try again.';
        },
      });
  }

  /**
   * Generates an on-demand study guide for the specified topic.
   * Handles the 30-second timeout with a user-friendly error message.
   *
   * Requirements: 7.2, 7.3, 7.4, 7.5
   *
   * @param topic  The AWS exam topic area to generate a guide for
   */
  generateStudyGuide(topic: string): void {
    if (this.studyGuideLoading) {
      return;
    }

    this.selectedTopic = topic;
    this.studyGuideLoading = true;
    this.studyGuideError = null;
    this.studyGuide = null;

    this.studyService
      .getStudyGuide(topic)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.studyGuideLoading = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: (response) => {
          // The backend wraps the formatted guide in { study_guide: ... }
          // Cast to our local interface since the backend returns the
          // format_study_content shape (sections with headings)
          this.studyGuide = (response as unknown as { study_guide: FormattedStudyGuide }).study_guide;
        },
        error: (err: ApiError) => {
          this.studyGuideError =
            err?.message ?? 'Study guide generation failed. Please try again.';
        },
      });
  }

  /**
   * Clears the currently displayed study guide so the user can select
   * a different topic.
   */
  clearStudyGuide(): void {
    this.studyGuide = null;
    this.studyGuideError = null;
    this.selectedTopic = null;
  }

  // ── Navigation ────────────────────────────────────────────────────────────

  /**
   * Navigates back to the practice questions view.
   * Requirement 7.9
   */
  navigateToPractice(): void {
    this.router.navigate(['/questions']);
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  /**
   * Returns a Material icon name for a given topic area.
   */
  topicIcon(topic: string): string {
    const icons: Record<string, string> = {
      'Cloud Concepts': 'cloud',
      'Security and Compliance': 'security',
      'Technology': 'memory',
      'Billing and Pricing': 'attach_money',
    };
    return icons[topic] ?? 'school';
  }

  /**
   * Returns a CSS colour class for a given topic area chip.
   */
  topicColorClass(topic: string): string {
    const classes: Record<string, string> = {
      'Cloud Concepts': 'chip-cloud',
      'Security and Compliance': 'chip-security',
      'Technology': 'chip-tech',
      'Billing and Pricing': 'chip-billing',
    };
    return classes[topic] ?? '';
  }
}
