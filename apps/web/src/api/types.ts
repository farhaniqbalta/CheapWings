// Hand-written from contracts/openapi.yaml (CheapWings API v1.0.0).
// Keep in sync manually; there is no generator in this toolchain (openapi-typescript's
// peer range doesn't support this project's TypeScript version yet).

export type JobStatus = "queued" | "running" | "completed" | "partial" | "failed" | "cancelled";
export type JobPhase = "searching" | "verifying" | "done";
export type SortMode = "best_checked" | "lowest_advertised";
export type IdentityConfidence = "exact_segments" | "insufficient_identity";
export type ThreeValued = "yes" | "no" | "unknown";
export type PriceStatus = "repriced_exact" | "recent_search" | "indicative" | "changed_or_unavailable";
export type ComparisonStatus =
  | "eligible_total_known"
  | "extra_cost_unknown"
  | "missing_required_baggage"
  | "ineligible"
  | "currency_unresolved";
export type LinkScope = "exact_offer" | "itinerary" | "generic_search" | "unavailable";
export type WorkStatus =
  | "pending"
  | "running"
  | "retry_wait"
  | "succeeded_results"
  | "succeeded_empty"
  | "failed_terminal"
  | "skipped_unsupported"
  | "cancelled";
export type ProviderErrorCode =
  | "network_timeout"
  | "http_rate_limited"
  | "auth_denied"
  | "provider_unavailable"
  | "schema_changed"
  | "partial_payload"
  | "invalid_currency"
  | "invalid_price"
  | "missing_segments"
  | "unsafe_fare"
  | "unsupported_query"
  | "terms_not_approved"
  | "unknown";

export const SUPPORTED_CURRENCIES = ["IDR", "USD", "AUD", "JPY"] as const;
export type Currency = (typeof SUPPORTED_CURRENCIES)[number];

export interface SearchRequest {
  provider_ids?: string[] | null;
  cache_mode?: "prefer_cache" | "refresh";
  trip_type?: "one_way";
  origins: string[];
  destinations: string[];
  departure_date_from: string; // YYYY-MM-DD
  departure_date_through: string;
  passengers?: { adults?: 1 };
  cabin?: "economy";
  include_basic_economy?: boolean;
  max_stops?: 0 | 1 | 2 | null;
  checked_bags_required?: boolean;
  display_currency?: Currency;
  point_of_sale_country?: string | null;
  include_hidden_city?: boolean;
}

export interface Created {
  job_id: string;
  status: JobStatus;
  created_at: string;
  total_route_date_combinations: number;
  enabled_detailed_providers: string[];
  job_status_url: string;
}

export interface ProviderProgress {
  provider_id: string;
  succeeded: number;
  failed: number;
  cancelled: number;
  skipped_unsupported: number;
  disabled_reason: string | null;
}

export interface Coverage {
  result_origin?: "live" | "cache" | "shared_inflight";
  observation_retrieved_at?: string | null;
  reused_at?: string | null;
  cache_fresh_until?: string | null;
  operation_attempts?: number;
  work_item_id: string;
  work_type: string;
  unpriced_candidate_count: number;
  provider_id: string;
  origin: string;
  destination: string;
  departure_date: string;
  status: WorkStatus;
  attempts: number;
  error_code: ProviderErrorCode | null;
  error_detail_sanitized: string | null;
  result_count: number | null;
  provider_complete: boolean | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Job {
  provider_ids?: string[];
  cache_mode?: "prefer_cache" | "refresh";
  job_id: string;
  query: SearchRequest;
  status: JobStatus;
  phase: JobPhase;
  cancel_requested: boolean;
  created_at: string;
  updated_at: string;
  total_route_date_combinations: number;
  covered_route_date_combinations: number;
  total_provider_work_items: number;
  succeeded_provider_work_items: number;
  succeeded_empty: number;
  failed_provider_work_items: number;
  skipped_unsupported: number;
  cancelled_provider_work_items: number;
  inventory_completeness: "unknown";
  exact_reprice_attempted: number;
  exact_reprice_succeeded: number;
  data_expires_at: string | null;
  provider_status: ProviderProgress[];
  coverage: Coverage[];
  warnings: string[];
}

export interface Segment {
  ordinal: number;
  marketing_carrier: string;
  operating_carrier: string;
  flight_number: string;
  origin: string;
  destination: string;
  depart_at: string;
  arrive_at: string;
  marketing_carrier_name?: string | null;
  operating_carrier_name?: string | null;
}

export interface PublicOffer {
  result_origin?: "live" | "cache" | "shared_inflight";
  reused_at?: string | null;
  quote_id: string;
  provider_id: string;
  seller: string | null;
  fare_family: string | null;
  cabin: string;
  basic_economy: boolean | null;
  amount_original: string; // decimal string, never a JSON number
  currency_original: string;
  comparable_amount: string | null;
  comparable_currency: string | null;
  comparison_status: ComparisonStatus;
  checked_bag: ThreeValued;
  hidden_city: ThreeValued;
  self_transfer: ThreeValued;
  price_status: PriceStatus;
  is_estimate: boolean;
  retrieved_at: string;
  repriced_at: string | null;
  link: string | null;
  link_scope: LinkScope;
  fee_completeness?: string;
  source_checked_at?: string | null;
  point_of_sale_country?: string | null;
  attribution?: string | null;
  fx_rate?: string | null;
  fx_as_of?: string | null;
  warnings: string[];
}

export interface AirportTransfer {
  after_segment: number;
  from_airport: string;
  to_airport: string;
}

export interface PublicItinerary {
  itinerary_id: string;
  identity_confidence: IdentityConfidence;
  origin: string;
  destination: string;
  departure_local: string;
  arrival_local: string;
  duration_minutes: number;
  stops: number;
  segments: Segment[];
  carrier_names?: string[];
  airport_transfers?: AirportTransfer[];
  offers: PublicOffer[];
  ranked_quote_id: string;
  warnings?: string[];
}

export interface Results {
  job_id: string;
  status: JobStatus;
  sort: SortMode;
  as_of: string;
  next_cursor: string | null;
  itineraries: PublicItinerary[];
  warnings: string[];
}

export interface ProviderCapability {
  provider_id: string;
  enabled: boolean;
  disabled_reason: string | null;
  detailed_search: boolean;
  calendar: boolean;
  exact_reprice: boolean;
  has_booking_link: boolean;
  has_hidden_city_flag: boolean;
  has_baggage_details: boolean;
  permitted_to_aggregate?: boolean;
  can_cache?: boolean;
  attribution_required?: boolean;
  retention_seconds?: number | null;
  usage_policy_reviewed_on?: string | null;
}

export interface Capabilities {
  search_cache_enabled?: boolean;
  search_cache_ttl_seconds?: number;
  max_hourly_requests?: number;
  providers: ProviderCapability[];
  supported_currencies: string[];
  max_route_date_combinations: number;
  max_active_jobs: number;
  max_hourly_jobs: number;
  synthetic_mode: boolean;
  inventory_completeness: "unknown";
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}
