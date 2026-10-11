import { DecimalPipe } from '@angular/common';
import {
  afterRenderEffect,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  OnDestroy,
  OnInit,
  signal,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AiService } from '../../core/api/ai.service';
import { Parcel, TreeCountResult } from '../../core/api/models';
import { ParcelService } from '../../core/api/parcel.service';
import { errorMessage, fileFrom } from '../../shared/errors';
import { MockBadge } from '../../shared/mock-badge';
import { boxAround, boxAt, EditableBox, medianSide } from './geometry';

const MAX_IMAGE_BYTES = 15 * 1024 * 1024;

/**
 * M6 · Olive tree counting: image -> optional parcel outline -> count -> manual correction -> save.
 * Everything drawn on the canvas is in pixels of the original image (like the boxes sent by M6).
 */
@Component({
  selector: 'app-tree-count',
  imports: [FormsModule, DecimalPipe, RouterLink, MockBadge],
  template: `
    <h1>Comptage des oliviers</h1>
    <p class="muted">Image vue du dessus de la parcelle : photo de drone, capture satellite ou Google Earth.</p>

    <div class="grid tc-layout">
      <section class="card">
        <div class="form-row">
          <label>
            Parcelle
            <select [(ngModel)]="parcelId" name="parcel">
              <option [ngValue]="undefined" disabled>Choisir une parcelle…</option>
              @for (p of parcels(); track p.id) {
                <option [ngValue]="p.id">{{ p.name }}</option>
              }
            </select>
          </label>
          <label>
            Image (JPEG ou PNG, 15 Mo max)
            <input type="file" accept="image/jpeg,image/png" (change)="onFile($event)" />
          </label>
        </div>

        @if (imageUrl()) {
          <p class="muted">
            @if (!result()) {
              Cliquez sur l'image pour tracer le contour de la parcelle. Optionnel : sans contour, toute l'image compte.
            } @else {
              Cliquez sur une boîte pour la supprimer, sur une zone vide pour ajouter un arbre.
            }
          </p>
          <div class="tc-stage">
            <img #img [src]="imageUrl()" alt="Parcelle vue du dessus" (load)="onImageLoad(img)" />
            <canvas #canvas (click)="onCanvasClick($event)"></canvas>
          </div>
          @if (!result()) {
            <div class="tc-actions">
              <button type="button" class="btn btn-ghost" (click)="undoPoint()" [disabled]="!polygon().length">
                Annuler le dernier point
              </button>
              <button type="button" class="btn btn-ghost" (click)="clearOutline()" [disabled]="!polygon().length">
                Effacer le contour
              </button>
              <span class="muted">{{ polygon().length }} point(s)</span>
            </div>
          }
        }
      </section>

      <section class="card">
        @if (result(); as r) {
          <h2>Résultat <app-mock-badge [mock]="r.mock" /></h2>
          <p class="tc-count">{{ count() }} <small>oliviers</small></p>
          @if (edited()) {
            <p class="muted">Corrigé à la main (détectés par le modèle : {{ r.count }}).</p>
          }
          @if (density() !== null) {
            <p>
              Densité : <strong>{{ density() | number: '1.0-1' }} arbres/ha</strong>
              @if (r.densityEstimated) {
                <span class="badge badge-mock" title="Aucune échelle donnée : taille de couronne supposée (5 m)">estimée</span>
              }
            </p>
          }
          @if (r.areaHa !== null) {
            <p class="muted">Surface : {{ r.areaHa | number: '1.0-2' }} ha{{ r.densityEstimated ? ' (estimée)' : '' }}</p>
          }
          @if (r.meanCrownM2 !== null) {
            <p class="muted">Couronne moyenne : {{ r.meanCrownM2 | number: '1.0-1' }} m²</p>
          }
          <p class="muted">Zoom utilisé : ×{{ r.zoomUsed }} · {{ r.processingMs / 1000 | number: '1.0-1' }} s</p>
          @for (w of r.warnings; track w) {
            <p class="alert">⚠️ {{ w }}</p>
          }
          <div class="tc-actions">
            <button class="btn" (click)="save()" [disabled]="saving()">Enregistrer</button>
            <button class="btn btn-ghost" (click)="restart()">Recommencer</button>
          </div>
          @if (saved()) {
            <p>✅ {{ saved() }} · <a [routerLink]="['/parcels', parcelId]">voir la parcelle</a></p>
          }
        } @else {
          <h2>Échelle <small>optionnel</small></h2>
          <p class="muted">Si vous ne savez pas, laissez vide : la densité sera estimée.</p>
          <div class="form-row">
            <label>
              Mètres par pixel
              <input type="number" step="any" min="0" [(ngModel)]="gsdM" name="gsdM" placeholder="ex. 0.1" />
            </label>
            <label>
              ou surface de la parcelle (ha)
              <input type="number" step="any" min="0" [(ngModel)]="areaHa" name="areaHa" placeholder="ex. 2.5" />
            </label>
          </div>
          <button class="btn" (click)="runCount()" [disabled]="!file || !parcelId || loading()">Compter</button>
          @if (!parcelId) {
            <p class="muted">Choisissez une parcelle.</p>
          }
          @if (loading()) {
            <p class="muted"><span class="spinner"></span> Comptage en cours… jusqu'à une minute pour une grande image.</p>
          }
        }
        @if (error()) {
          <p class="error">{{ error() }}</p>
        }
      </section>
    </div>
  `,
})
export class TreeCount implements OnInit, OnDestroy {
  private readonly ai = inject(AiService);
  private readonly parcelService = inject(ParcelService);

  /** ?parcel=ID (withComponentInputBinding), e.g. from the chat or the parcel page. */
  readonly parcel = input<number | undefined, string | undefined>(undefined, {
    transform: (v) => (v ? Number(v) : undefined),
  });

  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly img = viewChild<ElementRef<HTMLImageElement>>('img');
  private resizeObserver?: ResizeObserver;

  protected readonly parcels = signal<Parcel[]>([]);
  protected parcelId?: number;
  protected gsdM: number | null = null;
  protected areaHa: number | null = null;
  protected file?: File;

  protected readonly imageUrl = signal<string | null>(null);
  /** Size of the original image: the coordinate system of the polygon and of the boxes. */
  private readonly natural = signal<{ w: number; h: number } | null>(null);
  protected readonly polygon = signal<[number, number][]>([]);
  protected readonly result = signal<TreeCountResult | null>(null);
  protected readonly boxes = signal<EditableBox[]>([]);
  protected readonly edited = signal(false);
  protected readonly loading = signal(false);
  protected readonly saving = signal(false);
  protected readonly saved = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly count = computed(() => this.boxes().length);
  /** Live density while correcting: count / surface counted by M6 (polygon or whole image). */
  protected readonly density = computed(() => {
    const r = this.result();
    if (!r) return null;
    return r.areaHa ? Math.round((this.count() / r.areaHa) * 10) / 10 : r.densityPerHa;
  });

  constructor() {
    afterRenderEffect(() => {
      this.boxes();
      this.polygon();
      this.natural();
      this.draw();
    });
  }

  ngOnInit(): void {
    this.parcelId = this.parcel();
    this.parcelService.list().subscribe((p) => this.parcels.set(p));
  }

  onFile(event: Event): void {
    const file = fileFrom(event);
    if (!file) return;
    if (file.size > MAX_IMAGE_BYTES) {
      this.error.set('Image trop lourde (15 Mo maximum).');
      return;
    }
    this.revokeImage();
    this.file = file;
    this.imageUrl.set(URL.createObjectURL(file));
    this.natural.set(null);
    this.polygon.set([]);
    this.restart();
  }

  onImageLoad(img: HTMLImageElement): void {
    this.natural.set({ w: img.naturalWidth, h: img.naturalHeight });
    if (!this.resizeObserver && typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => this.draw());
    }
    this.resizeObserver?.observe(img);
  }

  /** Before counting: adds a point to the outline. After: removes the box under the click, or adds a tree. */
  onCanvasClick(event: MouseEvent): void {
    const n = this.natural();
    const canvas = event.target as HTMLCanvasElement;
    if (!n || !canvas.clientWidth) return;
    const x = (event.offsetX / canvas.clientWidth) * n.w;
    const y = (event.offsetY / canvas.clientHeight) * n.h;
    if (!this.result()) {
      this.polygon.update((p) => [...p, [Math.round(x), Math.round(y)]]);
      return;
    }
    const list = this.boxes();
    const hit = boxAt(list, x, y);
    this.boxes.set(
      hit >= 0 ? list.filter((_, i) => i !== hit) : [...list, boxAround(x, y, medianSide(list, n.w, n.h), n.w, n.h)],
    );
    this.edited.set(true);
    this.saved.set(null);
  }

  undoPoint(): void {
    this.polygon.update((p) => p.slice(0, -1));
  }

  clearOutline(): void {
    this.polygon.set([]);
  }

  runCount(): void {
    const poly = this.polygon();
    if (!this.file || !this.parcelId) return;
    if (poly.length > 0 && poly.length < 3) {
      this.error.set('Le contour doit avoir au moins 3 points (ou effacez-le pour compter toute l’image).');
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.saved.set(null);
    this.ai
      .countTrees(this.parcelId, this.file, {
        polygon: poly.length >= 3 ? poly : undefined,
        gsdM: positive(this.gsdM),
        areaHa: positive(this.areaHa),
      })
      .subscribe({
        next: (r) => {
          this.result.set(r);
          this.boxes.set(r.boxes.map(({ x1, y1, x2, y2 }) => ({ x1, y1, x2, y2 })));
          this.edited.set(false);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(errorMessage(err));
          this.loading.set(false);
        },
      });
  }

  /** Back to the outline step, keeping the image and the outline. */
  restart(): void {
    this.result.set(null);
    this.boxes.set([]);
    this.edited.set(false);
    this.saved.set(null);
    this.error.set(null);
  }

  save(): void {
    const r = this.result();
    if (!r || !this.parcelId) return;
    this.saving.set(true);
    this.error.set(null);
    this.ai
      .saveTreeCount(this.parcelId, {
        count: this.count(),
        densityPerHa: this.density(),
        densityEstimated: r.densityEstimated,
        corrected: this.edited(),
      })
      .subscribe({
        next: (p) => {
          this.saved.set(`${p.treeCount} oliviers enregistrés sur « ${p.name} »`);
          this.saving.set(false);
        },
        error: (err) => {
          this.error.set(errorMessage(err));
          this.saving.set(false);
        },
      });
  }

  ngOnDestroy(): void {
    this.resizeObserver?.disconnect();
    this.revokeImage();
  }

  private draw(): void {
    const canvas = this.canvas()?.nativeElement;
    const img = this.img()?.nativeElement;
    const n = this.natural();
    if (!canvas || !img || !n || !img.clientWidth) return;
    const w = img.clientWidth;
    const h = img.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform((dpr * w) / n.w, 0, 0, (dpr * h) / n.h, 0, 0); // draw in pixels of the original image
    ctx.clearRect(0, 0, n.w, n.h);
    const px = n.w / w; // one screen pixel, in image pixels

    const poly = this.polygon();
    if (poly.length) {
      ctx.strokeStyle = '#1e5bd8';
      ctx.fillStyle = 'rgba(30, 91, 216, 0.12)';
      ctx.lineWidth = 2 * px;
      ctx.beginPath();
      poly.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      if (poly.length >= 3) {
        ctx.closePath();
        ctx.fill();
      }
      ctx.stroke();
      ctx.fillStyle = '#1e5bd8';
      for (const [x, y] of poly) {
        ctx.beginPath();
        ctx.arc(x, y, 4 * px, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    ctx.lineWidth = 2 * px;
    for (const b of this.boxes()) {
      ctx.strokeStyle = b.added ? '#f29900' : '#d93025'; // added by hand: orange
      ctx.strokeRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1);
    }
  }

  private revokeImage(): void {
    const url = this.imageUrl();
    if (url) URL.revokeObjectURL(url);
  }
}

function positive(value: number | null): number | undefined {
  return value !== null && value > 0 ? value : undefined;
}
