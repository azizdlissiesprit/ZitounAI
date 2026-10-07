import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AiService } from '../../core/api/ai.service';
import { Parcel } from '../../core/api/models';
import { ParcelService } from '../../core/api/parcel.service';
import { errorMessage } from '../../shared/errors';
import { MockBadge } from '../../shared/mock-badge';

interface Message {
  from: 'user' | 'bot';
  text: string;
  meta?: string;
  mock?: boolean;
}

/** M5 · Derja assistant (the backend routes questions to M2/M3/M4 when needed) */
@Component({
  selector: 'app-assistant',
  imports: [FormsModule, MockBadge],
  template: `
    <h1>Assistant</h1>
    <p class="muted">Posez votre question en derja, en arabizi ou en français.</p>

    <section class="card chat">
      @for (m of messages(); track $index) {
        <div class="bubble" [class.user]="m.from === 'user'">
          {{ m.text }}
          @if (m.meta) {
            <small class="muted"> · {{ m.meta }}</small>
          }
          @if (m.mock) {
            <app-mock-badge [mock]="true" />
          }
        </div>
      } @empty {
        <p class="muted">Exemple : « chnowa na3mel ki el war9a tsfar? »</p>
      }
    </section>

    <form class="chat-input" (ngSubmit)="send()">
      <select [(ngModel)]="parcelId" name="parcel">
        <option [ngValue]="undefined">Sans parcelle</option>
        @for (p of parcels(); track p.id) {
          <option [ngValue]="p.id">{{ p.name }}</option>
        }
      </select>
      <input [(ngModel)]="draft" name="message" placeholder="Votre question…" autocomplete="off" />
      <button class="btn" type="submit" [disabled]="!draft.trim() || loading()">Envoyer</button>
    </form>
  `,
})
export class Assistant implements OnInit {
  private readonly ai = inject(AiService);
  private readonly parcelService = inject(ParcelService);

  protected readonly messages = signal<Message[]>([]);
  protected readonly parcels = signal<Parcel[]>([]);
  protected readonly loading = signal(false);
  protected draft = '';
  protected parcelId?: number;

  ngOnInit(): void {
    this.parcelService.list().subscribe((p) => this.parcels.set(p));
  }

  send(): void {
    const text = this.draft.trim();
    if (!text) return;
    this.draft = '';
    this.push({ from: 'user', text });
    this.loading.set(true);
    this.ai.chat(text, this.parcelId).subscribe({
      next: (r) => {
        this.push({ from: 'bot', text: r.answer, meta: `${r.intent} · ${r.answeredBy}`, mock: r.mock });
        this.loading.set(false);
      },
      error: (err) => {
        this.push({ from: 'bot', text: errorMessage(err) });
        this.loading.set(false);
      },
    });
  }

  private push(message: Message): void {
    this.messages.update((list) => [...list, message]);
  }
}
