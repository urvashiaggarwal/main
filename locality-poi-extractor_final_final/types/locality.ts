export interface Locality {
  id?: number
  locality_id: string
  locality_name: string
  city: string
  lat: number
  lng: number
  synonyms?: string
  child_locality?: string
  mp_list?: string
  created_at?: Date
  updated_at?: Date
}

export interface DatabaseResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}
