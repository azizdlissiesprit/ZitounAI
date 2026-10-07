import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../core/auth/auth.service';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="topbar">
      <a routerLink="/" class="brand">🫒 Zitouna AI</a>
      <nav>
        <a routerLink="/parcels" routerLinkActive="active">Parcelles</a>
        <a routerLink="/diagnosis" routerLinkActive="active">Diagnostic</a>
        <a routerLink="/price" routerLinkActive="active">Prix</a>
        <a routerLink="/assistant" routerLinkActive="active">Assistant</a>
        <a routerLink="/history" routerLinkActive="active">Historique</a>
      </nav>
      <span class="spacer"></span>
      <span class="muted">{{ auth.user()?.fullName }}</span>
      <button class="btn btn-ghost" (click)="auth.logout()">Déconnexion</button>
    </header>
    <main class="container">
      <router-outlet />
    </main>
  `,
})
export class Shell {
  protected readonly auth = inject(AuthService);
}
