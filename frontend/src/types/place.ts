export interface Place {
  place_id: string;
  name: string;
  neighborhood?: string;
  latitude?: number;
  longitude?: number;
  tags?: string[];
  description?: string;
  reviews?: string;
  review_snippet?: string;
  emoji?: string;
  score: number;
  image_urls?: string[];
  maps_url?: string;
  reviews_url?: string;
  google_rating?: number;
  google_review_count?: number;
  phone?: string;
  website?: string;
  hours_today?: string;
  open_now?: boolean | null;
}

export interface Recommendation {
  place_id: string;
  blurb: string;
}

export interface SearchResponse {
  places: Place[];
  total_results: number;
  query: string;
  llm_response: string;
  intro?: string;
  outro?: string;
  recommendations?: Recommendation[];
}
