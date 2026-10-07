import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { errorMessage } from '../../shared/errors';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-page">
      <form class="card" [formGroup]="form" (ngSubmit)="submit()">
        <h1>🫒 Zitouna AI</h1>
        <p class="muted">Connectez-vous pour suivre vos oliviers.</p>
        <label>E-mail <input type="email" formControlName="email" autocomplete="email" /></label>
        <label>Mot de passe <input type="password" formControlName="password" autocomplete="current-password" /></label>
        @if (error()) {
          <p class="error">{{ error() }}</p>
        }
        <button class="btn" type="submit" [disabled]="form.invalid || loading()">Se connecter</button>
        <p class="muted">Pas de compte ? <a routerLink="/register">Créer un compte</a></p>
      </form>
    </div>
  `,
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  submit(): void {
    this.loading.set(true);
    this.error.set(null);
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigate(['/']),
      error: (err) => {
        this.error.set(errorMessage(err));
        this.loading.set(false);
      },
    });
  }
}
