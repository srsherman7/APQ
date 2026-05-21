import { Component, OnInit, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatBadgeModule } from '@angular/material/badge';

import { ModuleService, Module } from '../../services/module.service';

@Component({
  selector: 'app-module-select',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatBadgeModule,
  ],
  templateUrl: './module-select.component.html',
  styleUrl: './module-select.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModuleSelectComponent implements OnInit {
  private readonly moduleService = inject(ModuleService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  modules: Module[] = [];
  isLoading = true;
  errorMessage: string | null = null;

  ngOnInit(): void {
    this.loadModules();
  }

  selectModule(module: Module): void {
    this.moduleService.setActiveModule(module);
    this.router.navigate(['/questions']);
  }

  private loadModules(): void {
    this.isLoading = true;
    this.moduleService.getModules().subscribe({
      next: (res) => {
        this.modules = res.modules;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorMessage = 'Failed to load modules. Please try again.';
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  formatTime(seconds: number): string {
    return `${Math.floor(seconds / 60)} min`;
  }
}
