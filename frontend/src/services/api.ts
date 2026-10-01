// Typed client for the read-only API (contract: specs/001-binder-hit-rate-dashboard/contracts).
const BASE = import.meta.env.VITE_API_BASE ?? '/api';

export interface Meta {
  snapshot_date: string;
  licence: string;
  credit: string;
  source_file?: string | null;
}
export interface Target {
  slug: string;
  name: string;
  designs: number;
}
export interface HitRate {
  method: string;
  binders: number;
  non_binders: number;
  no_result: number;
  labelled: number;
  hit_rate: number | null;
  small_sample: boolean;
}
export interface ScoreInfo {
  name: string;
  designs_with_value: number;
}
export interface Group {
  n: number;
  counts: number[];
}
export interface Distribution {
  score: string;
  bin_edges: number[];
  binder: Group;
  non_binder: Group;
  missing_count: number;
  conflicting_excluded: number;
  no_result_excluded: number;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function get<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`);
  } catch {
    throw new ApiError('Could not reach the server. Please try again later.', 0);
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

const enc = encodeURIComponent;

export const api = {
  meta: () => get<Meta>('/meta'),
  targets: () => get<Target[]>('/targets'),
  hitRates: (target: string) => get<HitRate[]>(`/targets/${enc(target)}/hit-rates`),
  scores: (target: string) => get<ScoreInfo[]>(`/targets/${enc(target)}/scores`),
  distribution: (target: string, score: string, bins = 20) =>
    get<Distribution>(`/targets/${enc(target)}/scores/${enc(score)}/distribution?bins=${bins}`),
};
