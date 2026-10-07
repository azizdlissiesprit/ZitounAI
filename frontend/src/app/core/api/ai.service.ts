import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';

import {
  ChatResponse,
  DiseaseResult,
  HarvestPlan,
  IrrigationResult,
  PageResponse,
  PredictionRecord,
  PredictionType,
  PriceResult,
  TreeCountResult,
  YieldResult,
} from './models';

/** All AI features go through the Spring backend, never directly to the FastAPI services. */
@Injectable({ providedIn: 'root' })
export class AiService {
  private readonly http = inject(HttpClient);

  /** M1 */
  diagnose(image: File, parcelId?: number) {
    let params = new HttpParams();
    if (parcelId) params = params.set('parcelId', parcelId);
    return this.http.post<DiseaseResult>('/api/ai/disease', imageForm(image), { params });
  }

  /** M2 */
  irrigation(parcelId: number) {
    return this.http.get<IrrigationResult>(`/api/parcels/${parcelId}/irrigation`);
  }

  /** M3 */
  yieldForecast(parcelId: number) {
    return this.http.get<YieldResult>(`/api/parcels/${parcelId}/yield`);
  }

  /** M4 */
  price(horizonWeeks = 8) {
    return this.http.get<PriceResult>('/api/ai/price', { params: { horizonWeeks } });
  }

  /** M5 (routed to M2/M3/M4 by the backend when needed) */
  chat(message: string, parcelId?: number) {
    return this.http.post<ChatResponse>('/api/ai/chat', { message, parcelId: parcelId ?? null });
  }

  /** M6 */
  countTrees(parcelId: number, image: File) {
    return this.http.post<TreeCountResult>(`/api/parcels/${parcelId}/count-trees`, imageForm(image));
  }

  /** M6 -> M3 -> M4. Without image, the parcel's saved tree count is used. */
  harvestPlan(parcelId: number, image?: File) {
    return this.http.post<HarvestPlan>(`/api/parcels/${parcelId}/harvest-plan`, image ? imageForm(image) : null);
  }

  history(type?: PredictionType, page = 0) {
    let params = new HttpParams().set('page', page);
    if (type) params = params.set('type', type);
    return this.http.get<PageResponse<PredictionRecord>>('/api/history', { params });
  }
}

function imageForm(image: File): FormData {
  const form = new FormData();
  form.append('image', image);
  return form;
}
