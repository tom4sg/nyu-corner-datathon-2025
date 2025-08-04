export interface Place {
  place_id: string;
  name: string;
  neighborhood?: string;
  latitude?: number;
  longitude?: number;
  tags?: string[];
  description?: string;
  reviews?: string;
  emoji?: string;
  score: number;
}

export interface SearchResponse {
  places: Place[];
  total_results: number;
  query: string;
  llm_response: string;
} 