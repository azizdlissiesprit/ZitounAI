import { DecimalPipe } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';

import { AiService } from '../../core/api/ai.service';
import { PriceResult } from '../../core/api/models';
import { errorMessage } from '../../shared/errors';
import { MockBadge } from '../../shared/mock-badge';

/** M4 · Price forecast and selling advice */
@Component({
  selector: 'app-price',
  imports: [DecimalPipe, MockBadge],
  template: `
    <h1>Prix de l'huile d'olive</h1>
    @if (error()) {
      <p class="error">{{ error() }}</p>
    }

    @if (result(); as r) {
      <section class="card">
        <h2>
          {{ r.recommendation === 'SELL_NOW' ? 'Conseil : vendre maintenant' : 'Conseil : stocker et attendre' }}
          <app-mock-badge [mock]="r.mock" />
        </h2>
        <p>{{ r.reason }}</p>
        @if (r.expectedGainTnd) {
          <p>Gain estimé : <strong>{{ r.expectedGainTnd | number: '1.0-0' }} {{ r.currency }}</strong></p>
        }
      </section>

      <section class="card">
        <h2>Prévision ({{ r.currency }}/{{ r.unit }})</h2>
        <!-- TODO(M4): replace with a real chart (e.g. Chart.js) showing history + forecast band. -->
        <div class="bars">
          @for (p of chart(); track p.date) {
            <div class="bar" [class.forecast]="p.forecast" [style.height.%]="p.height" [title]="p.date + ' : ' + p.price"></div>
          }
        </div>
        <p class="muted">Gris : historique · Vert : prévision</p>
      </section>
    }
  `,
})
export class Price implements OnInit {
  private readonly ai = inject(AiService);

  protected readonly result = signal<PriceResult | null>(null);
  protected readonly error = signal<string | null>(null);

  /** Bars scaled between the min and max price, for a dependency-free preview. */
  protected readonly chart = computed(() => {
    const r = this.result();
    if (!r) return [];
    const points = [
      ...r.history.map((p) => ({ ...p, forecast: false })),
      ...r.forecast.map((p) => ({ ...p, forecast: true })),
    ];
    const prices = points.map((p) => p.price);
    const min = Math.min(...prices) * 0.95;
    const max = Math.max(...prices);
    return points.map((p) => ({ ...p, height: ((p.price - min) / (max - min || 1)) * 100 }));
  });

  ngOnInit(): void {
    this.ai.price().subscribe({
      next: (r) => this.result.set(r),
      error: (err) => this.error.set(errorMessage(err)),
    });
  }
}
