import { DecimalPipe } from '@angular/common';
import { Component, effect, inject, input, numberAttribute, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';

import { AiService } from '../../core/api/ai.service';
import { HarvestPlan, IrrigationResult, Parcel, TreeCountResult, YieldResult } from '../../core/api/models';
import { ParcelService } from '../../core/api/parcel.service';
import { errorMessage, fileFrom } from '../../shared/errors';
import { MockBadge } from '../../shared/mock-badge';

@Component({
  selector: 'app-parcel-detail',
  imports: [DecimalPipe, MockBadge],
  template: `
    @if (parcel(); as p) {
      <div class="page-header">
        <h1>{{ p.name }}</h1>
        <button class="btn btn-danger" (click)="remove(p)">Supprimer</button>
      </div>
      <p class="muted">
        {{ p.governorate }} · {{ p.latitude }}, {{ p.longitude }} · {{ p.areaHa ?? '?' }} ha ·
        {{ p.treeCount ?? '?' }} arbres · {{ p.variety ?? 'variété inconnue' }}
      </p>
    }
    @if (error()) {
      <p class="error">{{ error() }}</p>
    }

    <div class="grid">
      <!-- M2 -->
      <section class="card">
        <h2>Irrigation & alertes <small>M2</small></h2>
        <button class="btn" (click)="run(ai.irrigation(id()), irrigation)">Conseil sur 7 jours</button>
        @if (irrigation(); as r) {
          <app-mock-badge [mock]="r.mock" />
          @for (a of r.alerts; track a.date + a.type) {
            <p class="alert">⚠️ {{ a.date }} — {{ a.message }}</p>
          }
          <table>
            <tr><th>Jour</th><th>ET₀</th><th>Pluie</th><th>Besoin</th><th>L/arbre</th></tr>
            @for (d of r.days; track d.date) {
              <tr [class.highlight]="d.irrigate">
                <td>{{ d.date }}</td><td>{{ d.et0Mm }}</td><td>{{ d.rainMm }}</td>
                <td>{{ d.waterNeedMm }} mm</td><td>{{ d.litersPerTree ?? '—' }}</td>
              </tr>
            }
          </table>
        }
      </section>

      <!-- M3 -->
      <section class="card">
        <h2>Récolte estimée <small>M3</small></h2>
        <button class="btn" (click)="run(ai.yieldForecast(id()), yieldResult)">Estimer la récolte</button>
        @if (yieldResult(); as y) {
          <app-mock-badge [mock]="y.mock" />
          <p>Région {{ y.governorate }}, saison {{ y.season }}/{{ y.season + 1 }} :
            <strong>{{ y.regionalProductionTonnes | number: '1.0-0' }} t</strong></p>
          @if (y.parcelEstimateKg !== null) {
            <p>Votre parcelle : <strong>{{ y.parcelEstimateKg | number: '1.0-0' }} kg</strong>
              ({{ y.parcelLowKg | number: '1.0-0' }} – {{ y.parcelHighKg | number: '1.0-0' }})</p>
          } @else {
            <p class="muted">Renseignez le nombre d'arbres pour une estimation de la parcelle.</p>
          }
        }
      </section>

      <!-- M6 -->
      <section class="card">
        <h2>Compter les oliviers <small>M6</small></h2>
        <p class="muted">Image drone ou capture satellite de la parcelle.</p>
        <input type="file" accept="image/*" (change)="countTrees($event)" />
        @if (trees(); as t) {
          <app-mock-badge [mock]="t.mock" />
          <p><strong>{{ t.treeCount }}</strong> arbres détectés</p>
          @if (t.annotatedImageBase64) {
            <img class="preview" [src]="'data:image/png;base64,' + t.annotatedImageBase64" alt="Arbres détectés" />
          }
        }
      </section>

      <!-- M6 -> M3 -> M4 -->
      <section class="card">
        <h2>Plan de récolte <small>M6 → M3 → M4</small></h2>
        <p class="muted">Image optionnelle : sans image, le nombre d'arbres enregistré est utilisé.</p>
        <input type="file" accept="image/*" (change)="planImage = fileFrom($event)" />
        <button class="btn" (click)="run(ai.harvestPlan(id(), planImage), plan)">Calculer le plan</button>
        @if (plan(); as h) {
          <app-mock-badge [mock]="h.mock" />
          <p>{{ h.summary }}</p>
          <p class="muted">{{ h.price.reason }}</p>
        }
      </section>
    </div>
  `,
})
export class ParcelDetail {
  protected readonly ai = inject(AiService);
  private readonly parcelService = inject(ParcelService);
  private readonly router = inject(Router);

  /** Bound from the route parameter :id (withComponentInputBinding). */
  readonly id = input.required({ transform: numberAttribute });

  protected readonly parcel = signal<Parcel | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly irrigation = signal<IrrigationResult | null>(null);
  protected readonly yieldResult = signal<YieldResult | null>(null);
  protected readonly trees = signal<TreeCountResult | null>(null);
  protected readonly plan = signal<HarvestPlan | null>(null);
  protected planImage?: File;
  protected readonly fileFrom = fileFrom;

  constructor() {
    effect(() => this.loadParcel(this.id()));
  }

  private loadParcel(id: number): void {
    this.parcelService.get(id).subscribe({
      next: (p) => this.parcel.set(p),
      error: (err) => this.error.set(errorMessage(err)),
    });
  }

  run<T>(call: Observable<T>, target: { set(value: T): void }): void {
    this.error.set(null);
    call.subscribe({
      next: (result) => target.set(result),
      error: (err) => this.error.set(errorMessage(err)),
    });
  }

  countTrees(event: Event): void {
    const file = fileFrom(event);
    if (!file) return;
    this.error.set(null);
    this.ai.countTrees(this.id(), file).subscribe({
      next: (result) => {
        this.trees.set(result);
        this.loadParcel(this.id());
      },
      error: (err) => this.error.set(errorMessage(err)),
    });
  }

  remove(p: Parcel): void {
    if (!confirm(`Supprimer la parcelle « ${p.name} » ?`)) return;
    this.parcelService.delete(p.id).subscribe(() => this.router.navigate(['/parcels']));
  }
}
