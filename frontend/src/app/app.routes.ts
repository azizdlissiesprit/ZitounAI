import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { Shell } from './layout/shell';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./features/auth/login').then((m) => m.Login) },
  { path: 'register', loadComponent: () => import('./features/auth/register').then((m) => m.Register) },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'parcels' },
      {
        path: 'parcels',
        loadComponent: () => import('./features/parcels/parcel-list').then((m) => m.ParcelList),
      },
      {
        path: 'parcels/:id',
        loadComponent: () => import('./features/parcels/parcel-detail').then((m) => m.ParcelDetail),
      },
      {
        path: 'diagnosis',
        loadComponent: () => import('./features/diagnosis/diagnosis').then((m) => m.Diagnosis),
      },
      { path: 'price', loadComponent: () => import('./features/price/price').then((m) => m.Price) },
      {
        path: 'assistant',
        loadComponent: () => import('./features/assistant/assistant').then((m) => m.Assistant),
      },
      { path: 'history', loadComponent: () => import('./features/history/history').then((m) => m.History) },
    ],
  },
  { path: '**', redirectTo: '' },
];
