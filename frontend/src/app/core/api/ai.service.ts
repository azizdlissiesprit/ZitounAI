import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';

import {
  ChatRequest,
  ChatResponse,
  DiseaseResult,
  HarvestPlan,
  IrrigationResult,
  PageResponse,
  PredictionRecord,
  PredictionType,
  Parcel,
  PriceResult,
  TreeCountOptions,
  TreeCountResult,
  TreeCountSave,
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

  /** M5 detects the intent, the backend routes the question to the right module. */
  chat(request: ChatRequest) {
    return this.http.post<ChatResponse>('/api/ai/chat', request);
  }

  /** M6 step 1: count the trees on the image. Nothing is saved (the farmer reviews the boxes first). */
  countTrees(parcelId: number, image: File, options: TreeCountOptions = {}) {
    const form = imageForm(image);
    if (options.polygon?.length) form.append('polygon', JSON.stringify(options.polygon));
    if (options.gsdM) form.append('gsdM', String(options.gsdM));
    if (options.areaHa) form.append('areaHa', String(options.areaHa));
    if (options.zoom) form.append('zoom', String(options.zoom));
    return this.http.post<TreeCountResult>(`/api/parcels/${parcelId}/tree-count`, form);
  }

  /** M6 step 2: save the final (possibly corrected) count on the parcel. */
  saveTreeCount(parcelId: number, body: TreeCountSave) {
    return this.http.put<Parcel>(`/api/parcels/${parcelId}/tree-count`, body);
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
