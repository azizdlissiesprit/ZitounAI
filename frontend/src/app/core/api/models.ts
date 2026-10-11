// TypeScript mirror of the backend API. Keep in sync with docs/api-contract.md.

export interface User {
  id: number;
  fullName: string;
  email: string;
  role: 'FARMER' | 'ADMIN';
}

export interface AuthResponse {
  token: string;
  expiresAt: string;
  user: User;
}

export interface Parcel {
  id: number;
  name: string;
  governorate: string;
  latitude: number;
  longitude: number;
  areaHa: number | null;
  treeCount: number | null;
  /** Last M6 count (null if unknown); densityEstimated: from an assumed crown size. */
  densityPerHa: number | null;
  densityEstimated: boolean | null;
  treeCountedAt: string | null;
  treeCountSource: TreeCountSource | null;
  variety: string | null;
  irrigated: boolean;
  createdAt: string;
}

export type TreeCountSource = 'MODEL' | 'CORRECTED' | 'MANUAL';

export type ParcelRequest = Omit<
  Parcel,
  'id' | 'createdAt' | 'densityPerHa' | 'densityEstimated' | 'treeCountedAt' | 'treeCountSource'
>;

/** Every AI result has `mock: true` while the module has no trained model yet. */
interface AiResult {
  mock: boolean;
}

// M1
export interface DiseaseResult extends AiResult {
  label: 'healthy' | 'peacock_spot' | 'aculus_olearius' | 'olive_knot';
  labelFr: string;
  confidence: number;
  probabilities: Record<string, number>;
  advice: string;
  heatmapBase64: string | null;
  modelVersion: string;
}

// M2
export interface IrrigationResult extends AiResult {
  days: {
    date: string;
    et0Mm: number;
    rainMm: number;
    waterNeedMm: number;
    litersPerTree: number | null;
    irrigate: boolean;
  }[];
  alerts: { date: string; type: 'FROST' | 'HEATWAVE'; severity: string; message: string }[];
  modelVersion: string;
}

// M3
export interface YieldResult extends AiResult {
  governorate: string;
  season: number;
  regionalProductionTonnes: number;
  kgPerTree: number | null;
  parcelEstimateKg: number | null;
  parcelLowKg: number | null;
  parcelHighKg: number | null;
  modelVersion: string;
}

// M4
export interface PricePoint {
  date: string;
  price: number;
  low: number | null;
  high: number | null;
}

export interface PriceResult extends AiResult {
  currency: string;
  unit: string;
  history: PricePoint[];
  forecast: PricePoint[];
  recommendation: 'SELL_NOW' | 'STORE';
  reason: string;
  expectedGainTnd: number | null;
  modelVersion: string;
}

// M5 (through the backend's ChatService)
export type Intent =
  | 'maladie'
  | 'irrigation'
  | 'meteo_alerte'
  | 'recolte'
  | 'prix_vente'
  | 'comptage'
  | 'conseil_general'
  | 'salutation'
  | 'hors_sujet';

export interface ChatRequest {
  text: string;
  parcelId?: number | null;
  /** Set when the farmer clicks a suggestion: the backend skips the classification. */
  forcedIntent?: Intent | null;
}

export interface ChatResponse extends AiResult {
  reply: string;
  intent: Intent;
  /** true: `reply` is a question and `suggestions` should be shown as buttons. */
  clarify: boolean;
  suggestions: Intent[];
  /** Raw result of the module that answered (IrrigationResult, PriceResult...), or null. */
  data: unknown;
  /** "gemini/gemini-3.5-flash" when an LLM wrote the reply, "template" otherwise. */
  generatedBy: string;
  /** Button opening a page of the app (e.g. tree counting), or null. */
  link: { label: string; url: string } | null;
}

// M6 · boxes in pixels of the uploaded image
export interface TreeBox {
  id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  score: number;
}

export interface TreeCountResult extends AiResult {
  count: number;
  boxes: TreeBox[];
  zoomUsed: number | null;
  zoomTrials: { zoom: number; n: number; score: number; crownPx: number }[];
  densityPerHa: number | null;
  /** true: no scale given, density from an assumed 5 m crown. */
  densityEstimated: boolean;
  areaHa: number | null;
  gsdM: number | null;
  meanCrownM2: number | null;
  imageSize: { width: number; height: number };
  warnings: string[];
  annotatedImage: string | null;
  processingMs: number;
  modelVersion: string;
}

export interface TreeCountOptions {
  /** Parcel outline [[x, y], ...] in image pixels; none = whole image. */
  polygon?: [number, number][];
  gsdM?: number;
  areaHa?: number;
  zoom?: number;
}

export interface TreeCountSave {
  count: number;
  densityPerHa: number | null;
  densityEstimated: boolean;
  /** true if the farmer removed or added boxes. */
  corrected: boolean;
}

// M6 -> M3 -> M4
export interface HarvestPlan extends AiResult {
  treeCount: number;
  treeCountSource: 'M6' | 'PARCEL';
  yield: YieldResult;
  estimatedOilKg: number | null;
  price: PriceResult;
  summary: string;
}

export type PredictionType =
  | 'DISEASE'
  | 'IRRIGATION'
  | 'YIELD'
  | 'PRICE'
  | 'CHAT'
  | 'TREE_COUNT'
  | 'HARVEST_PLAN';

export interface PredictionRecord {
  id: number;
  type: PredictionType;
  parcelId: number | null;
  parcelName: string | null;
  request: unknown;
  response: unknown;
  mock: boolean;
  createdAt: string;
}

export interface PageResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
}
