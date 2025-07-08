import pool from "@/lib/database"
import type { Locality, DatabaseResponse } from "@/types/locality"
import type { RowDataPacket, ResultSetHeader } from "mysql2"
import { GooglePlacesService } from "./google-places-service"

interface LocalityRow extends RowDataPacket {
  id: number
  locality_id: string
  locality_name: string
  city: string
  lat: number
  lng: number
  synonyms?: string
  child_locality?: string
  mp_list?: string
  created_at: Date
  updated_at: Date
}

export class LocalityService {
  // Find locality by ID and auto-generate MP list if missing
  static async findByLocalityId(localityId: string, autoGenerateMp = true): Promise<DatabaseResponse<Locality>> {
    try {
      const [rows] = await pool.execute<LocalityRow[]>("SELECT * FROM localities WHERE locality_id = ?", [localityId])

      if (rows.length === 0) {
        return {
          success: false,
          error: "Locality not found",
        }
      }

      const locality = rows[0]

      // Auto-generate MP list if missing and autoGenerateMp is true
      if (autoGenerateMp && (!locality.mp_list || locality.mp_list.trim() === "")) {
        console.log(`Generating MP list for ${localityId}...`)
        const mpList = await GooglePlacesService.getMpList(locality.locality_name, locality.city)

        if (mpList !== "error") {
          // Update the database with the new MP list
          await pool.execute("UPDATE localities SET mp_list = ? WHERE locality_id = ?", [mpList, localityId])
          locality.mp_list = mpList
        }
      }

      return {
        success: true,
        data: locality,
      }
    } catch (error) {
      console.error("Error finding locality:", error)
      return {
        success: false,
        error: "Database error occurred",
      }
    }
  }

  // Find multiple localities by IDs
  static async findByLocalityIds(localityIds: string[]): Promise<DatabaseResponse<Locality[]>> {
    try {
      if (localityIds.length === 0) {
        return { success: true, data: [] }
      }

      const placeholders = localityIds.map(() => "?").join(",")
      const [rows] = await pool.execute<LocalityRow[]>(
        `SELECT * FROM localities WHERE locality_id IN (${placeholders})`,
        localityIds,
      )

      return {
        success: true,
        data: rows,
      }
    } catch (error) {
      console.error("Error finding localities:", error)
      return {
        success: false,
        error: "Database error occurred",
      }
    }
  }

  // Create new locality
  static async create(
    locality: Omit<Locality, "id" | "created_at" | "updated_at">,
  ): Promise<DatabaseResponse<Locality>> {
    try {
      // Check if locality_id already exists
      const existing = await this.findByLocalityId(locality.locality_id)
      if (existing.success) {
        return {
          success: false,
          error: "Locality ID already exists",
        }
      }

      const [result] = await pool.execute<ResultSetHeader>(
        `INSERT INTO localities (locality_id, locality_name, city, lat, lng, synonyms, child_locality, mp_list) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          locality.locality_id,
          locality.locality_name,
          locality.city,
          locality.lat,
          locality.lng,
          locality.synonyms || null,
          locality.child_locality || null,
          locality.mp_list || null,
        ],
      )

      // Fetch the created locality
      const created = await this.findByLocalityId(locality.locality_id)

      return {
        success: true,
        data: created.data,
        message: "Locality created successfully",
      }
    } catch (error) {
      console.error("Error creating locality:", error)
      return {
        success: false,
        error: "Failed to create locality",
      }
    }
  }

  // Create multiple localities
  static async createBulk(
    localities: Omit<Locality, "id" | "created_at" | "updated_at">[],
  ): Promise<DatabaseResponse<{ created: number; skipped: number; errors: string[]; duplicates: string[] }>> {
    try {
      let created = 0
      let skipped = 0
      const errors: string[] = []
      const duplicates: string[] = []

      console.log(` Processing ${localities.length} localities for bulk creation...`)

      for (let i = 0; i < localities.length; i++) {
        const locality = localities[i]
        try {
          const result = await this.create(locality)
          if (result.success) {
            created++
            if (created % 100 === 0) {
              console.log(` Created ${created} localities so far...`)
            }
          } else {
            skipped++
            if (result.error?.includes("already exists")) {
              duplicates.push(locality.locality_id)
            } else {
              errors.push(`${locality.locality_id}: ${result.error}`)
            }
          }
        } catch (error) {
          skipped++
          errors.push(`${locality.locality_id}: ${error instanceof Error ? error.message : "Unknown error"}`)
        }
      }

      console.log(`📊 Bulk creation completed:`)
      console.log(`   ✅ Created: ${created}`)
      console.log(`   ⏭️ Skipped: ${skipped}`)
      console.log(`   🔄 Duplicates: ${duplicates.length}`)
      console.log(`   ❌ Errors: ${errors.length}`)

      return {
        success: true,
        data: { created, skipped, errors, duplicates },
        message: `Created ${created} localities, skipped ${skipped} (${duplicates.length} duplicates, ${errors.length} errors)`,
      }
    } catch (error) {
      console.error("Error in bulk create:", error)
      return {
        success: false,
        error: "Bulk creation failed",
      }
    }
  }

  // Get all localities with pagination
  static async getAll(page = 1, limit = 50): Promise<DatabaseResponse<{ localities: Locality[]; total: number }>> {
    try {
      const offset = (page - 1) * limit

      // Get total count
      const [countRows] = await pool.execute<RowDataPacket[]>("SELECT COUNT(*) as total FROM localities")
      const total = countRows[0].total

      // Get paginated data
      const [rows] = await pool.execute<LocalityRow[]>(
        "SELECT * FROM localities ORDER BY created_at DESC LIMIT ? OFFSET ?",
        [limit, offset],
      )

      return {
        success: true,
        data: { localities: rows, total },
      }
    } catch (error) {
      console.error("Error getting all localities:", error)
      return {
        success: false,
        error: "Failed to fetch localities",
      }
    }
  }

  // Search localities by name or city
  static async search(query: string): Promise<DatabaseResponse<Locality[]>> {
    try {
      const searchTerm = `%${query}%`
      const [rows] = await pool.execute<LocalityRow[]>(
        `SELECT * FROM localities 
         WHERE locality_name LIKE ? OR city LIKE ? OR synonyms LIKE ?
         ORDER BY locality_name`,
        [searchTerm, searchTerm, searchTerm],
      )

      return {
        success: true,
        data: rows,
      }
    } catch (error) {
      console.error("Error searching localities:", error)
      return {
        success: false,
        error: "Search failed",
      }
    }
  }

  // Find locality by ID with POIs included
  static async findByLocalityIdWithPOIs(localityId: string, autoGenerateMp = true): Promise<DatabaseResponse<any>> {
    try {
      // First get the locality
      const localityResult = await this.findByLocalityId(localityId, autoGenerateMp)

      if (!localityResult.success || !localityResult.data) {
        return localityResult
      }

      // Get POIs for this locality
      const { POIService } = await import("./poi-service")
      const poiData = await POIService.getLocalityWithPOIs(localityId)

      return {
        success: true,
        data: {
          ...localityResult.data,
          pois: poiData.pois,
          poi_extraction_info: {
            from_cache: poiData.fromCache,
            extraction_date: poiData.extractionDate,
            total_pois: poiData.pois.length,
          },
        },
      }
    } catch (error) {
      console.error("Error finding locality with POIs:", error)
      return {
        success: false,
        error: "Database error occurred",
      }
    }
  }

  // Find multiple localities with POIs
  static async findByLocalityIdsWithPOIs(localityIds: string[]): Promise<DatabaseResponse<any[]>> {
    try {
      if (localityIds.length === 0) {
        return { success: true, data: [] }
      }

      const results = []

      for (const localityId of localityIds) {
        const result = await this.findByLocalityIdWithPOIs(localityId, true)

        if (result.success && result.data) {
          results.push(result.data)
        } else {
          results.push({
            locality_id: localityId,
            status: "not_found",
            error: result.error,
          })
        }
      }

      return {
        success: true,
        data: results,
      }
    } catch (error) {
      console.error("Error finding localities with POIs:", error)
      return {
        success: false,
        error: "Database error occurred",
      }
    }
  }
}
