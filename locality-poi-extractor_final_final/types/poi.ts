export interface POIExtraction {
  id?: number
  locality_id: string
  locality_name: string
  city: string
  poi_type: string
  output_type: "unfiltered" | "unfiltered2" | "surrounding" | "filtered"
  name?: string
  place_id?: string
  primary_type?: string
  types?: string[]
  api_primary_type?: string
  address?: string
  rating?: number
  rating_count?: number
  lat?: number
  lng?: number
  google_map_url?: string
  containing_place?: string
  containment_within?: string[]
  business_status?: string
  parking_options?: any
  wheelchair_accessible?: boolean
  website?: string
  summary?: string
  photos_reference?: string[]
  reviews?: any[]
  extraction_date?: Date
}

export interface POIExtractionJob {
  id: number
  locality_id: string
  status: "pending" | "processing" | "completed" | "failed"
  total_pois: number
  processed_pois: number
  error_message?: string
  started_at: Date
  completed_at?: Date
}

export interface POIConfig {
  text_query_template: string
  poi_names: {
    uf1: string
    uf2: string
    surrounding: string
    filtered: string
  }
  apply_within_logic: boolean
  required_types_api: string[]
  rating_count_threshold: number
  name_filter_exclude: string[]
  use_selenium: boolean
  selenium_xpath?: string
  primary_type_filter_mode: "include" | "exclude" | "none"
  primary_type_filter_list: string[]
}
