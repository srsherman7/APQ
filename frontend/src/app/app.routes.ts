import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  // Default route
  {
    path: '',
    redirectTo: '/questions',
    pathMatch: 'full'
  },

  // ── Public routes (no auth required) ──────────────────────────────────────

  // Login (Requirement 14.7, 14.9, 14.13)
  {
    path: 'login',
    loadComponent: () =>
      import('./components/login/login.component').then(m => m.LoginComponent)
  },

  // Register (Requirements 14.1, 14.2, 14.5)
  {
    path: 'register',
    loadComponent: () =>
      import('./components/register/register.component').then(m => m.RegisterComponent)
  },

  // ── Protected routes (auth required) ──────────────────────────────────────
  // All wrapped in the NavShellComponent for the persistent navigation bar.
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/nav-shell/nav-shell.component').then(m => m.NavShellComponent),
    children: [
      // Main practice session (Requirements 1.1–1.9, 2.1–2.8, 3.1–3.7, 4.1–4.10)
      {
        path: 'questions',
        loadComponent: () =>
          import('./components/practice-session/practice-session.component').then(
            m => m.PracticeSessionComponent
          )
      },

      // Analytics dashboard (Requirements 5.1, 5.4, 5.5, 5.6, 5.8, 5.9)
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./components/analytics-dashboard/analytics-dashboard.component').then(
            m => m.AnalyticsDashboardComponent
          )
      },

      // Drill mode (Requirements 6.1–6.9)
      {
        path: 'drill-mode',
        loadComponent: () =>
          import('./components/drill-mode/drill-mode.component').then(
            m => m.DrillModeComponent
          )
      },

      // Study materials (Requirements 7.1–7.9)
      {
        path: 'study-materials',
        loadComponent: () =>
          import('./components/study-materials/study-materials.component').then(
            m => m.StudyMaterialsComponent
          )
      },
    ]
  },

  // Wildcard – redirect to login
  {
    path: '**',
    redirectTo: '/login'
  }
];
