import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  // Default route
  {
    path: '',
    redirectTo: '/modules',
    pathMatch: 'full'
  },

  // ── Public routes ─────────────────────────────────────────────────────────
  {
    path: 'login',
    loadComponent: () =>
      import('./components/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./components/register/register.component').then(m => m.RegisterComponent)
  },

  // ── Module selection (after login, before entering a module) ───────────────
  {
    path: 'modules',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/module-select/module-select.component').then(m => m.ModuleSelectComponent)
  },

  // ── Protected routes (inside a module) ────────────────────────────────────
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./components/nav-shell/nav-shell.component').then(m => m.NavShellComponent),
    children: [
      {
        path: 'questions',
        loadComponent: () =>
          import('./components/practice-session/practice-session.component').then(
            m => m.PracticeSessionComponent
          )
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./components/analytics-dashboard/analytics-dashboard.component').then(
            m => m.AnalyticsDashboardComponent
          )
      },
      {
        path: 'drill-mode',
        loadComponent: () =>
          import('./components/drill-mode/drill-mode.component').then(
            m => m.DrillModeComponent
          )
      },
      {
        path: 'exam',
        loadComponent: () =>
          import('./components/exam-mode/exam-mode.component').then(
            m => m.ExamModeComponent
          )
      },
      {
        path: 'study-materials',
        loadComponent: () =>
          import('./components/study-materials/study-materials.component').then(
            m => m.StudyMaterialsComponent
          )
      },
      {
        path: 'admin',
        loadComponent: () =>
          import('./components/admin-panel/admin-panel.component').then(
            m => m.AdminPanelComponent
          )
      },
    ]
  },

  // Wildcard
  {
    path: '**',
    redirectTo: '/modules'
  }
];
