import pool from "../lib/database"
import type { POIExtraction, POIExtractionJob } from "../types/poi"
import type { RowDataPacket, ResultSetHeader } from "mysql2"
import { CITY_SYNONYMS, CATEGORY_CONFIGS, DEFAULT_XPATH } from "../constants/poi-config"
import type { POIConfig } from "../types/poi"
import { spawn } from "child_process"
import { writeFileSync, readFileSync, unlinkSync, existsSync } from "fs"
import { join } from "path"

// Default XPath for extracting primary type if not provided in config

interface POIRow extends RowDataPacket, POIExtraction {}
interface JobRow extends RowDataPacket, POIExtractionJob {}

export class POIService {
  // Create extraction job
  static async createExtractionJob(localityId: string): Promise<number> {
    const [result] = await pool.execute<ResultSetHeader>(
      "INSERT INTO poi_extraction_jobs (locality_id, status) VALUES (?, 'pending')",
      [localityId],
    )
    return result.insertId
  }

  // Update job status
  static async updateJobStatus(
    jobId: number,
    status: "pending" | "processing" | "completed" | "failed",
    errorMessage?: string,
  ) {
    if (status === "completed" || status === "failed") {
      await pool.execute(
        "UPDATE poi_extraction_jobs SET status = ?, error_message = ?, completed_at = NOW() WHERE id = ?",
        [status, errorMessage || null, jobId],
      )
    } else {
      await pool.execute("UPDATE poi_extraction_jobs SET status = ? WHERE id = ?", [status, jobId])
    }
  }

  // Update job progress
  static async updateJobProgress(jobId: number, processedPois: number, totalPois?: number) {
    if (totalPois !== undefined) {
      await pool.execute("UPDATE poi_extraction_jobs SET processed_pois = ?, total_pois = ? WHERE id = ?", [
        processedPois,
        totalPois,
        jobId,
      ])
    } else {
      await pool.execute("UPDATE poi_extraction_jobs SET processed_pois = ? WHERE id = ?", [processedPois, jobId])
    }
  }

  // Get job status
  static async getJobStatus(jobId: number): Promise<POIExtractionJob | null> {
    const [rows] = await pool.execute<JobRow[]>("SELECT * FROM poi_extraction_jobs WHERE id = ?", [jobId])
    return rows[0] || null
  }

  // Save filtered POI extraction results to main table
  static async saveFilteredPOIResults(pois: POIExtraction[]) {
    if (pois.length === 0) return

    try {
      // Check if table exists first
      const [tableCheck] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions'`,
      )

      if (tableCheck[0].table_exists === 0) {
        console.log("POI tables don't exist yet. Cannot save POI results.")
        return
      }

      const values = pois.map((poi) => [
        poi.locality_id,
        poi.locality_name,
        poi.city,
        poi.poi_type,
        poi.name || null,
        poi.place_id || null,
        poi.primary_type || null,
        JSON.stringify(poi.types || []),
        poi.api_primary_type || null,
        poi.address || null,
        poi.rating || null,
        poi.rating_count || null,
        poi.lat || null,
        poi.lng || null,
        poi.google_map_url || null,
        poi.containing_place || null,
        JSON.stringify(poi.containment_within || []),
        poi.business_status || null,
        JSON.stringify(poi.parking_options || null),
        poi.wheelchair_accessible || null,
        poi.website || null,
        poi.summary || null,
        JSON.stringify(poi.photos_reference || []),
        JSON.stringify(poi.reviews || []),
      ])

      const placeholders = values.map(() => "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").join(",")

      await pool.execute(
        `INSERT INTO poi_extractions (
        locality_id, locality_name, city, poi_type, name, place_id, 
        primary_type, types, api_primary_type, address, rating, rating_count, 
        lat, lng, google_map_url, containing_place, containment_within, 
        business_status, parking_options, wheelchair_accessible, website, 
        summary, photos_reference, reviews
      ) VALUES ${placeholders}`,
        values.flat(),
      )
    } catch (error) {
      console.error("Error saving filtered POI results:", error)
      throw error
    }
  }

  // Save surrounding POI extraction results to surrounding table
  static async saveSurroundingPOIResults(pois: POIExtraction[]) {
    if (pois.length === 0) return

    try {
      // Check if table exists first
      const [tableCheck] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions_surrounding'`,
      )

      if (tableCheck[0].table_exists === 0) {
        console.log("Surrounding POI table doesn't exist yet. Cannot save surrounding POI results.")
        return
      }

      const values = pois.map((poi) => [
        poi.locality_id,
        poi.locality_name,
        poi.city,
        poi.poi_type,
        poi.name || null,
        poi.place_id || null,
        poi.primary_type || null,
        JSON.stringify(poi.types || []),
        poi.api_primary_type || null,
        poi.address || null,
        poi.rating || null,
        poi.rating_count || null,
        poi.lat || null,
        poi.lng || null,
        poi.google_map_url || null,
        poi.containing_place || null,
        JSON.stringify(poi.containment_within || []),
        poi.business_status || null,
        JSON.stringify(poi.parking_options || null),
        poi.wheelchair_accessible || null,
        poi.website || null,
        poi.summary || null,
        JSON.stringify(poi.photos_reference || []),
        JSON.stringify(poi.reviews || []),
      ])

      const placeholders = values.map(() => "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)").join(",")

      await pool.execute(
        `INSERT INTO poi_extractions_surrounding (
        locality_id, locality_name, city, poi_type, name, place_id, 
        primary_type, types, api_primary_type, address, rating, rating_count, 
        lat, lng, google_map_url, containing_place, containment_within, 
        business_status, parking_options, wheelchair_accessible, website, 
        summary, photos_reference, reviews
      ) VALUES ${placeholders}`,
        values.flat(),
      )
    } catch (error) {
      console.error("Error saving surrounding POI results:", error)
      throw error
    }
  }

  // Get POI results for a locality from both tables
  static async getPOIResults(localityId: string, outputType?: string, poiType?: string) {
    const allPois: any[] = []

    try {
      // Get filtered POIs from main table
      if (!outputType || outputType === "filtered" || outputType === "all") {
        let query = "SELECT * FROM poi_extractions WHERE locality_id = ?"
        const params: any[] = [localityId]

        if (poiType) {
          query += " AND poi_type = ?"
          params.push(poiType)
        }

        query += " ORDER BY extraction_date DESC"

        const [rows] = await pool.execute<POIRow[]>(query, params)

        const filteredPois = rows.map((row) => {
          const poi = {
            ...row,
            output_type: "filtered", // Force set to filtered
            types: row.types ? this.safeJsonParse(row.types as unknown as string, []) : [],
            containment_within: row.containment_within
              ? this.safeJsonParse(row.containment_within as unknown as string, [])
              : [],
            parking_options: row.parking_options
              ? this.safeJsonParse(row.parking_options as unknown as string, null)
              : null,
            photos_reference: row.photos_reference
              ? this.safeJsonParse(row.photos_reference as unknown as string, [])
              : [],
            reviews: row.reviews ? this.safeJsonParse(row.reviews as unknown as string, []) : [],
          }
          return poi
        })

        allPois.push(...filteredPois)
      }

      // Get surrounding POIs from surrounding table
      if (!outputType || outputType === "surrounding" || outputType === "all") {
        let query = "SELECT * FROM poi_extractions_surrounding WHERE locality_id = ?"
        const params: any[] = [localityId]

        if (poiType) {
          query += " AND poi_type = ?"
          params.push(poiType)
        }

        query += " ORDER BY extraction_date DESC"

        const [rows] = await pool.execute<POIRow[]>(query, params)

        const surroundingPois = rows.map((row) => {
          const poi = {
            ...row,
            output_type: "surrounding", // Force set to surrounding
            types: row.types ? this.safeJsonParse(row.types as unknown as string, []) : [],
            containment_within: row.containment_within
              ? this.safeJsonParse(row.containment_within as unknown as string, [])
              : [],
            parking_options: row.parking_options
              ? this.safeJsonParse(row.parking_options as unknown as string, null)
              : null,
            photos_reference: row.photos_reference
              ? this.safeJsonParse(row.photos_reference as unknown as string, [])
              : [],
            reviews: row.reviews ? this.safeJsonParse(row.reviews as unknown as string, []) : [],
          }
          return poi
        })

        allPois.push(...surroundingPois)
      }

      return allPois
    } catch (error) {
      console.error("Error getting POI results:", error)
      return []
    }
  }

  // Delete old POI results for a locality from both tables
  static async deleteOldPOIResults(localityId: string) {
    try {
      // Delete from main table
      const [tableCheck1] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions'`,
      )

      if (tableCheck1[0].table_exists > 0) {
        await pool.execute("DELETE FROM poi_extractions WHERE locality_id = ?", [localityId])
      }

      // Delete from surrounding table
      const [tableCheck2] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions_surrounding'`,
      )

      if (tableCheck2[0].table_exists > 0) {
        await pool.execute("DELETE FROM poi_extractions_surrounding WHERE locality_id = ?", [localityId])
      }
    } catch (error) {
      console.error("Error deleting old POI results:", error)
      throw error
    }
  }

  // Helper functions for filtering (converted from Python)
  static filterAddressByMP(address: string, mpList: string, cityName: string): boolean {
    const cleanAddress = address
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, " ")
      .replace(/\s+/g, " ")
      .trim()

    let r1 = false // flag for micro-pocket match
    let r2 = false // flag for city match

    // Check micro-pocket match
    const mpArray = mpList.split(";").map((mp) => mp.trim())
    for (const mp of mpArray) {
      const mpClean = mp
        .toLowerCase()
        .replace(/[^a-z0-9 ]/g, " ")
        .replace(/\s+/g, " ")
        .trim()
      const regex = new RegExp(`\\b${mpClean.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`)
      if (regex.test(cleanAddress)) {
        r1 = true
        break
      }
    }

    // Check city match
    if (!cityName) {
      r2 = true
    } else {
      const cityList = CITY_SYNONYMS[cityName] || [cityName]
      for (const city of cityList) {
        const cityClean = city
          .toLowerCase()
          .replace(/[^a-z0-9 ]/g, " ")
          .replace(/\s+/g, " ")
          .trim()
        const regex = new RegExp(`\\b${cityClean.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`)
        if (regex.test(cleanAddress)) {
          r2 = true
          break
        }
      }
    }

    return r1 && r2
  }

  static filterByName(pois: any[], excludeList: string[]): any[] {
    if (!excludeList.length) return pois

    return pois.filter((poi) => {
      const nameClean = poi.name
        .toLowerCase()
        .replace(/[^a-z0-9 ]/g, " ")
        .replace(/\s+/g, " ")
        .trim()
      const pattern = new RegExp(
        `\\b(?:${excludeList.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`,
        "i",
      )
      return !pattern.test(nameClean)
    })
  }

  // Apply type filtering based on config(API)
  static filterByType(pois: any[], config: POIConfig): any[] {
    // If no required_types_api, return as is
    if (!config.required_types_api || config.required_types_api.length === 0) {
      return pois
    }

    return pois.filter((poi) => {
      let types = poi.types
      // If types is a string that looks like an array, parse it
      if (typeof types === "string" && types.trim().startsWith("[")) {
        try {
          types = JSON.parse(types)
        } catch {
          types = []
        }
      }
      // Only keep POIs where types is an array and any required type is present
      return Array.isArray(types) && config.required_types_api.some((t) => types.includes(t))
    })
  }

  // FIXED: External Selenium script for primary type extraction
  static async extractPrimaryTypesWithSelenium(pois: POIExtraction[], xpath: string): Promise<string[]> {
    return new Promise((resolve, reject) => {
      const timestamp = Date.now()
      const inputFile = join(process.cwd(), `temp_pois_${timestamp}.json`)
      const outputFile = join(process.cwd(), `temp_results_${timestamp}.json`)

      try {
        // Write POI data to temporary file
        writeFileSync(inputFile, JSON.stringify(pois, null, 2))

        console.log("🔧 Starting external Selenium script for primary type extraction...")

        // Spawn the external Selenium script
        const scriptPath = join(process.cwd(), "scripts", "selenium-primary-type-extractor.js")
        const child = spawn("node", [scriptPath, inputFile, outputFile, xpath], {
          stdio: ["pipe", "pipe", "pipe"],
        })

        let stdout = ""
        let stderr = ""

        child.stdout.on("data", (data) => {
          stdout += data.toString()
          console.log(`Selenium: ${data.toString().trim()}`)
        })

        child.stderr.on("data", (data) => {
          stderr += data.toString()
          console.error(`Selenium Error: ${data.toString().trim()}`)
        })

        child.on("close", (code) => {
          try {
            // Clean up input file
            if (existsSync(inputFile)) {
              unlinkSync(inputFile)
            }

            if (code === 0 && existsSync(outputFile)) {
              // Read results
              const results = JSON.parse(readFileSync(outputFile, "utf8"))
              unlinkSync(outputFile) // Clean up output file
              console.log(" Selenium extraction completed successfully")
              resolve(results)
            } else {
              console.log(" Selenium extraction failed, using fallback")
              // Return fallback results
              const fallbackResults = pois.map(() => "extraction failed")
              resolve(fallbackResults)
            }
          } catch (error) {
            console.error("Error processing Selenium results:", error)
            const fallbackResults = pois.map(() => "processing error")
            resolve(fallbackResults)
          }
        })

        child.on("error", (error) => {
          console.error("Failed to start Selenium script:", error)
          // Clean up files
          if (existsSync(inputFile)) unlinkSync(inputFile)
          if (existsSync(outputFile)) unlinkSync(outputFile)
          // Return fallback results
          const fallbackResults = pois.map(() => "script error")
          resolve(fallbackResults)
        })

        // Set timeout for the process
        setTimeout(() => {
          child.kill()
          console.log("Selenium extraction timed out")
          // Clean up files
          if (existsSync(inputFile)) unlinkSync(inputFile)
          if (existsSync(outputFile)) unlinkSync(outputFile)
          const fallbackResults = pois.map(() => "timeout")
          resolve(fallbackResults)
        }, 300000) // 5 minute timeout
      } catch (error) {
        console.error("Error setting up Selenium extraction:", error)
        // Clean up files
        if (existsSync(inputFile)) unlinkSync(inputFile)
        if (existsSync(outputFile)) unlinkSync(outputFile)
        const fallbackResults = pois.map(() => "setup error")
        resolve(fallbackResults)
      }
    })
  }

  // Check if POIs exist and are fresh (less than 2 months old)
  static async checkPOIFreshness(localityId: string): Promise<{ hasFreshPOIs: boolean; extractionDate?: Date }> {
    try {
      // Check both tables for freshness
      const [tableCheck1] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions'`,
      )

      const [tableCheck2] = await pool.execute<RowDataPacket[]>(
        `SELECT COUNT(*) as table_exists 
       FROM information_schema.tables 
       WHERE table_schema = DATABASE() AND table_name = 'poi_extractions_surrounding'`,
      )

      if (tableCheck1[0].table_exists === 0 && tableCheck2[0].table_exists === 0) {
        console.log("POI tables don't exist yet. Please run the POI table creation scripts.")
        return { hasFreshPOIs: false }
      }

      // Check latest extraction from both tables
      let latestExtraction: Date | null = null

      if (tableCheck1[0].table_exists > 0) {
        const [rows1] = await pool.execute<RowDataPacket[]>(
          `SELECT MAX(extraction_date) as latest_extraction 
         FROM poi_extractions 
         WHERE locality_id = ?`,
          [localityId],
        )
        if (rows1[0]?.latest_extraction) {
          latestExtraction = new Date(rows1[0].latest_extraction)
        }
      }

      if (tableCheck2[0].table_exists > 0) {
        const [rows2] = await pool.execute<RowDataPacket[]>(
          `SELECT MAX(extraction_date) as latest_extraction 
         FROM poi_extractions_surrounding 
         WHERE locality_id = ?`,
          [localityId],
        )
        if (rows2[0]?.latest_extraction) {
          const surroundingDate = new Date(rows2[0].latest_extraction)
          if (!latestExtraction || surroundingDate > latestExtraction) {
            latestExtraction = surroundingDate
          }
        }
      }

      if (!latestExtraction) {
        return { hasFreshPOIs: false }
      }

      const twoMonthsAgo = new Date()
      twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2)

      return {
        hasFreshPOIs: latestExtraction > twoMonthsAgo,
        extractionDate: latestExtraction,
      }
    } catch (error) {
      console.error("Error checking POI freshness:", error)
      return { hasFreshPOIs: false }
    }
  }

  // Get all POIs for a locality (from both tables)
  static async getAllPOIsForLocality(localityId: string) {
    return await this.getPOIResults(localityId, "all")
  }

  // NEW: Google Places API (New) - Text Search with enhanced data extraction
  static async callGooglePlacesNewAPI(query: string, location?: { lat: number; lng: number }): Promise<any[]> {
    const apiKey = process.env.GOOGLE_PLACES_API_KEY

    if (!apiKey) {
      console.error("Google Places API key not configured")
      return []
    }

    try {
      const url = "https://places.googleapis.com/v1/places:searchText"

      const requestBody: any = {
        textQuery: query,
        maxResultCount: 20,
      }

      if (location) {
        requestBody.locationBias = {
          circle: {
            center: {
              latitude: location.lat,
              longitude: location.lng,
            },
            radius: 5000,
          },
        }
      }

      const headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": apiKey,
        "X-Goog-FieldMask":
          "places.displayName,places.id,places.types,places.primaryType,places.formattedAddress,places.rating,places.userRatingCount,places.location,places.googleMapsUri,places.containingPlaces,places.addressDescriptor,places.businessStatus,places.parkingOptions,places.accessibilityOptions,places.websiteUri,places.editorialSummary,places.photos,places.reviews",
      }

      console.log(`Calling Google Places API (New): ${query}`)
      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(requestBody),
      })

      const data = await response.json()

      if (response.ok && data.places) {
        return await this.extractPlaceData(data.places, apiKey)
      } else {
        console.error("Google Places API (New) error:", data.error || "Unknown error")
        return []
      }
    } catch (error) {
      console.error("Error calling Google Places API (New):", error)
      return []
    }
  }

  // Extract place data matching the Python function logic
  static async extractPlaceData(allResults: any[], apiKey: string): Promise<any[]> {
    const datapoints = []

    for (const place of allResults) {
      try {
        const name = place.displayName?.text || "N/A"
        const place_id = place.id || "N/A"
        const types = place.types || []
        const api_primary_type = place.primaryType || "N/A"
        const address = place.formattedAddress || "N/A"
        const rating = place.rating || null
        const rating_count = place.userRatingCount || 0
        const lat = place.location?.latitude || null
        const lng = place.location?.longitude || null
        const google_map_url = place.googleMapsUri || "N/A"

        // containing_place - make additional API call like in Python
        let cont_place = "N/A"
        const containingPlaces = place.containingPlaces
        if (containingPlaces && containingPlaces.length > 0) {
          try {
            const placeResource = containingPlaces[0].id
            const url = `https://places.googleapis.com/v1/places/${placeResource}`

            const response = await fetch(url, {
              headers: {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": apiKey,
                "X-Goog-FieldMask": "displayName",
              },
            })

            const data = await response.json()
            cont_place = data.displayName?.text || "N/A"

            // Small delay to avoid rate limiting
            await new Promise((resolve) => setTimeout(resolve, 50))
          } catch (error) {
            console.log(`Could not get containing place for ${name}:`, error)
          }
        }

        // containment_WITHIN - extract from addressDescriptor.areas
        let within_list: string[] = []
        const areas = place.addressDescriptor?.areas
        if (areas) {
          for (const area of areas) {
            if (area.containment === "WITHIN") {
              within_list.push(area.displayName?.text || "")
            }
          }
        }

        if (within_list.length === 0) {
          within_list = []
        }

        const business_status = place.businessStatus || "OPERATIONAL"
        const parking_options = place.parkingOptions || null
        const wheelchair_accessible = place.accessibilityOptions?.wheelchairAccessibleEntrance || null
        const website = place.websiteUri || null
        const summary = place.editorialSummary?.text || null

        // Photo references - extract photo names
        const photos_reference: string[] = []
        const photos = place.photos
        if (photos) {
          for (const photo of photos) {
            if (photo.name) {
              photos_reference.push(photo.name)
            }
          }
        }

        // Reviews - extract original text
        const review_list: string[] = []
        const reviews = place.reviews
        if (reviews) {
          for (const review of reviews) {
            const originalText = review.originalText?.text
            if (originalText) {
              review_list.push(originalText)
            }
          }
        }

        const extractedPlace = {
          name,
          place_id,
          types,
          api_primary_type,
          address,
          rating,
          rating_count,
          lat,
          lng,
          google_map_url,
          containing_place: cont_place,
          containment_within: within_list,
          business_status,
          parking_options,
          wheelchair_accessible,
          website,
          summary,
          photos_reference,
          reviews: review_list,
        }

        datapoints.push(extractedPlace)
      } catch (error) {
        console.error(`Error processing place ${place.displayName?.text}:`, error)
      }
    }

    return datapoints
  }

  // FIXED: Extract POIs for a single category using Google Places API (New)
  static async extractPOIsForCategory(
    locality: any,
    category: string,
    config: POIConfig,
  ): Promise<{
    filteredPois: POIExtraction[]
    surroundingPois: POIExtraction[]
  }> {
    const filteredPois: POIExtraction[] = []
    const surroundingPois: POIExtraction[] = []

    try {
      // Build query using template
      const query = config.text_query_template.replace("{}", `${locality.locality_name}, ${locality.city}`)

      // Call Google Places API (New) with enhanced details
      const places = await this.callGooglePlacesNewAPI(query, {
        lat: Number(locality.lat),
        lng: Number(locality.lng),
      })

      console.log(`Found ${places.length} places for ${category} in ${locality.locality_name}`)

      if (places.length === 0) {
        return { filteredPois, surroundingPois }
      }

      // Process each place
      const candidatePois: POIExtraction[] = []

      for (const place of places) {
        // Create base POI object with enhanced fields from New API
        const basePOI: POIExtraction = {
          locality_id: locality.locality_id,
          locality_name: locality.locality_name,
          city: locality.city,
          poi_type: category,
          output_type: "unfiltered", // This will be updated later
          name: place.name,
          place_id: place.place_id,
          primary_type: place.types?.[0] || null,
          types: place.types,
          api_primary_type: place.api_primary_type,
          address: place.address,
          rating: place.rating,
          rating_count: place.rating_count,
          lat: place.lat,
          lng: place.lng,
          google_map_url: place.google_map_url,
          containing_place: place.containing_place !== "N/A" ? place.containing_place : locality.locality_name,
          containment_within:
            place.containment_within.length > 0 ? place.containment_within : [locality.locality_name, locality.city],
          business_status: place.business_status,
          parking_options: place.parking_options,
          wheelchair_accessible: place.wheelchair_accessible,
          website: place.website,
          summary: place.summary,
          photos_reference: place.photos_reference,
          reviews: place.reviews,
        }

        candidatePois.push(basePOI)
      }

      // Apply initial filtering
      let workingPois = [...candidatePois]

      // 1. Apply within logic only if config.apply_within_logic is true
      if (config.apply_within_logic) {
        workingPois = POIService.withinFiltering(workingPois)
      }

      // 2. Apply type filtering
      workingPois = this.filterByType(workingPois, config)

      // 3. Apply rating count threshold for surrounding POIs (less strict)
      const surroundingCandidates = workingPois.filter(
        (poi) => (poi.rating_count || 0) >= Math.max(1, config.rating_count_threshold / 2),
      )

      // 4. Apply stricter rating count threshold for filtered POIs
      workingPois = workingPois.filter((poi) => (poi.rating_count || 0) >= config.rating_count_threshold)

      // 5. Apply name filtering
      if (config.name_filter_exclude.length > 0) {
        workingPois = this.filterByName(workingPois, config.name_filter_exclude)
      }

      // 6. Extract primary types with Selenium if enabled (matching Python step 6)
      if (config.use_selenium && (workingPois.length > 0 || surroundingCandidates.length > 0)) {
        // Combine all POIs by place_id to avoid duplicate Selenium calls
        const uniquePOIs = [
          ...new Map(
            [...workingPois, ...surroundingCandidates].map((poi) => [poi.place_id, poi])
          ).values(),
        ];

        console.log(`🔧 Using external Selenium script for ${uniquePOIs.length} unique POIs`);
        const primaryTypeMap = await POIService.extractPrimaryTypesForPOIs(
          uniquePOIs,
          config.selenium_xpath || DEFAULT_XPATH
        );

        // Assign extracted primary types to both filtered and surrounding POIs
        workingPois.forEach((poi) => {
          poi.primary_type = poi.place_id ? primaryTypeMap[poi.place_id] || "not extracting" : "not extracting";
        });
        surroundingCandidates.forEach((poi) => {
          poi.primary_type = poi.place_id ? primaryTypeMap[poi.place_id] || "not extracting" : "not extracting";
        });
      } else {
        // If Selenium is disabled, set primary_type to "not extracting"
        workingPois.forEach((poi) => {
          poi.primary_type = "not extracting";
        });
        surroundingCandidates.forEach((poi) => {
          poi.primary_type = "not extracting";
        });
      }

      // 7. Apply primary type filtering (matching Python step 7)
      if (config.primary_type_filter_mode === "include") {
        // Only keep POIs whose primary_type is in the allowed list
        workingPois = workingPois.filter((poi) =>
          config.primary_type_filter_list.some((filterType) =>
            (poi.primary_type || "").toLowerCase().includes(filterType.toLowerCase()),
          ),
        )
      } else if (config.primary_type_filter_mode === "exclude") {
        // Remove POIs whose primary_type is in the excluded list
        workingPois = workingPois.filter(
          (poi) =>
            !config.primary_type_filter_list.some((filterType) =>
              (poi.primary_type || "").toLowerCase().includes(filterType.toLowerCase()),
            ),
        )
      }
      // If mode is "none", no filtering is applied

      // Check if filtering resulted in empty list
      if (workingPois.length === 0) {
        console.log(` Primary type filtering resulted in no POIs for category ${category}`)
      }

      // 8. Always apply address/location filtering if mp_list is present
      if (locality.mp_list) {
        workingPois = workingPois.filter((poi) =>
          POIService.filterAddressByMP(poi.address || "", locality.mp_list, locality.city)
        );
      }

      // 9. Top 3 Filtering Except School & School Website Filtering
      workingPois = POIService.selectTop3PerTypeExceptSchools(workingPois)

      // FIXED: Update output_type to "filtered" for final filtered POIs
      workingPois.forEach((poi) => {
        poi.output_type = "filtered"
      })

      // Final filtered POIs
      filteredPois.push(...workingPois)

      // Filter surrounding POIs that are not already in filtered POIs
      const filteredPlaceIds = new Set(filteredPois.map((poi) => poi.place_id))
      const finalSurroundingPois = surroundingCandidates.filter((poi) => !filteredPlaceIds.has(poi.place_id))

      // FIXED: Update output_type to "surrounding" for final surrounding POIs
      finalSurroundingPois.forEach((poi) => {
        poi.output_type = "surrounding"
      })

      surroundingPois.push(...finalSurroundingPois)

      console.log(
        `Category ${category}: ${filteredPois.length} filtered, ${surroundingPois.length} surrounding (after primary filtering)`,
      )

      return { filteredPois, surroundingPois }
    } catch (error) {
      console.error(`Error extracting POIs for category ${category}:`, error)
      return { filteredPois, surroundingPois }
    }
  }

  // Updated: Extract POIs for a locality (all categories) - NOW USES Google Places API (New)
  static async extractPOIsForLocality(locality: any) {
    try {
      const allCategories = Object.keys(CATEGORY_CONFIGS)
      const allFilteredPois: POIExtraction[] = []
      const allSurroundingPois: POIExtraction[] = []

      console.log(`Starting POI extraction for ${locality.locality_name} with ${allCategories.length} categories`)

      // Delete old POI data for this locality from both tables
      await this.deleteOldPOIResults(locality.locality_id)

      // Process each category
      for (const category of allCategories) {
        const config = CATEGORY_CONFIGS[category]
        console.log(`Processing category: ${category}`)

        try {
          // Extract POIs for this category using Google Places API (New)
          const { filteredPois, surroundingPois } = await this.extractPOIsForCategory(locality, category, config)
          allFilteredPois.push(...filteredPois)
          allSurroundingPois.push(...surroundingPois)

          // Add delay to avoid rate limiting
          await new Promise((resolve) => setTimeout(resolve, 200))
        } catch (error) {
          console.error(`Failed to extract POIs for category ${category}:`, error)
          // Continue with other categories even if one fails
        }
      }

      // Save filtered POIs to main table
      if (allFilteredPois.length > 0) {
        console.log(`Saving ${allFilteredPois.length} filtered POIs to main table`)
        await this.saveFilteredPOIResults(allFilteredPois)
      }

      // Save surrounding POIs to surrounding table
      if (allSurroundingPois.length > 0) {
        console.log(`Saving ${allSurroundingPois.length} surrounding POIs to surrounding table`)
        await this.saveSurroundingPOIResults(allSurroundingPois)
      }

      console.log(
        `POI extraction completed for ${locality.locality_name}: ${allFilteredPois.length} filtered + ${allSurroundingPois.length} surrounding POIs`,
      )

      return [...allFilteredPois, ...allSurroundingPois]
    } catch (error) {
      console.error("Error extracting POIs:", error)
      throw error
    }
  }

  // Main method to get locality with POIs (checks freshness automatically)
  static async getLocalityWithPOIs(localityId: string) {
    try {
      // Check if POIs are fresh
      const { hasFreshPOIs, extractionDate } = await this.checkPOIFreshness(localityId)

      if (hasFreshPOIs) {
        // Return existing POIs from both tables
        const pois = await this.getAllPOIsForLocality(localityId)
        return {
          pois,
          fromCache: true,
          extractionDate,
        }
      } else {
        // Check if tables exist before trying to extract
        const [tableCheck1] = await pool.execute<RowDataPacket[]>(
          `SELECT COUNT(*) as table_exists 
         FROM information_schema.tables 
         WHERE table_schema = DATABASE() AND table_name = 'poi_extractions'`,
        )

        const [tableCheck2] = await pool.execute<RowDataPacket[]>(
          `SELECT COUNT(*) as table_exists 
         FROM information_schema.tables 
         WHERE table_schema = DATABASE() AND table_name = 'poi_extractions_surrounding'`,
        )

        if (tableCheck1[0].table_exists === 0 || tableCheck2[0].table_exists === 0) {
          console.log(
            "POI tables don't exist yet. Returning empty POI list. Please run the POI table creation scripts.",
          )
          return {
            pois: [],
            fromCache: false,
            extractionDate: new Date(),
            error: "POI tables not created yet",
          }
        }

        // Need to extract new POIs - first get locality details
        const { LocalityService } = await import("./locality-service")
        const localityResult = await LocalityService.findByLocalityId(localityId, false)

        if (!localityResult.success || !localityResult.data) {
          throw new Error("Locality not found")
        }

        console.log(`Extracting fresh POIs for locality: ${localityId}`)

        // Extract new POIs using Google Places API (New)
        const pois = await this.extractPOIsForLocality(localityResult.data)
        return {
          pois,
          fromCache: false,
          extractionDate: new Date(),
        }
      }
    } catch (error) {
      console.error("Error getting locality with POIs:", error)
      // Return empty POIs instead of throwing error
      return {
        pois: [],
        fromCache: false,
        extractionDate: new Date(),
        error: error instanceof Error ? error.message : "Unknown error",
      }
    }
  }

  // After you have your finalFilteredPois array (output_type: "filtered")
  static selectTop3PerTypeExceptSchools(pois: POIExtraction[]): POIExtraction[] {
    // Schools with website
    const schools = pois.filter((poi) => poi.poi_type === "school" && poi.website && poi.website !== "N/A")
    // For other types, top 3 by rating_count
    const result: POIExtraction[] = [...schools]
    const otherTypes = [...new Set(pois.map((poi) => poi.poi_type).filter((t) => t !== "school"))]
    for (const type of otherTypes) {
      const top3 = pois
        .filter((poi) => poi.poi_type === type)
        .sort((a, b) => (b.rating_count || 0) - (a.rating_count || 0))
        .slice(0, 3)
      result.push(...top3)
    }
    return result
  }

  static filterByPrimaryType(pois: POIExtraction[], config: POIConfig): POIExtraction[] {
    if (config.primary_type_filter_mode === "none" || !config.primary_type_filter_list.length) {
      return pois
    }
    return pois.filter((poi) => {
      const primaryType = poi.primary_type || ""
      const isInList = config.primary_type_filter_list.some((filterType) =>
        primaryType.toLowerCase().includes(filterType.toLowerCase()),
      )
      if (config.primary_type_filter_mode === "include") {
        return isInList
      } else if (config.primary_type_filter_mode === "exclude") {
        return !isInList
      }
      return true
    })
  }

  static withinFiltering(pois: POIExtraction[]): POIExtraction[] {
    // This function removes POIs that are contained within another POI in the same list,
    // matching the logic of the Python within_logic function.

    if (!pois.length) return pois

    // Build combined_within = [containing_place] + containment_within (if present)
    const allNames = new Set(pois.map((poi) => poi.name))
    const poisWithCombined = pois.map((poi, idx) => {
      // containing_place: treat null/"N/A"/undefined as empty string
      const containingPlace = poi.containing_place && poi.containing_place !== "N/A" ? poi.containing_place : ""
      // containment_within: ensure array
      let within: string[] = []
      if (Array.isArray(poi.containment_within)) {
        within = poi.containment_within
      } else if (
        typeof poi.containment_within === "string" &&
        typeof (poi.containment_within as string).trim === "function" &&
        (poi.containment_within as string).trim().startsWith("[")
      ) {
        try {
          within = JSON.parse(poi.containment_within as string)
        } catch {
          within = []
        }
      }
      // If containingPlace is empty, combined_within is just within
      const combined_within = (containingPlace ? [containingPlace] : []).concat(within)
      return {
        ...poi,
        _originalIndex: idx,
        combined_within,
      }
    })

    // If all combined_within are empty, return original list
    if (poisWithCombined.every((poi) => !poi.combined_within.length)) {
      return poisWithCombined.map(({ combined_within, _originalIndex, ...rest }) => rest as POIExtraction)
    }

    // Explode combined_within
    type Exploded = Omit<typeof poisWithCombined[0], 'combined_within'> & { combined_within: string; is_other_name?: boolean }
    const exploded: Exploded[] = []
    for (const poi of poisWithCombined) {
      if (!poi.combined_within.length) {
        exploded.push({ ...poi, combined_within: "" })
      } else {
        for (const val of poi.combined_within) {
          exploded.push({ ...poi, combined_within: val })
        }
      }
    }

    // Mark if combined_within value is another POI's name (and not itself)
    for (const row of exploded) {
      row.is_other_name =
        !!row.combined_within &&
        allNames.has(row.combined_within) &&
        row.combined_within !== row.name
    }

    // Group by _originalIndex to find which ones to drop
    const dropIndices = new Set<number>()
    const grouped = new Map<number, Exploded[]>()
    for (const row of exploded) {
      if (!grouped.has(row._originalIndex)) grouped.set(row._originalIndex, [])
      grouped.get(row._originalIndex)!.push(row)
    }
    for (const [idx, group] of grouped.entries()) {
      if (group.some((row) => row["is_other_name"])) {
        dropIndices.add(idx)
      }
    }

    // Filter out POIs whose _originalIndex is in dropIndices
    const filtered = poisWithCombined.filter((poi) => !dropIndices.has(poi._originalIndex))

    // Remove temp fields
    return filtered.map(({ combined_within, _originalIndex, ...rest }) => rest as POIExtraction)
  }

  // Helper method for safe JSON parsing
  static safeJsonParse(jsonString: string, fallback: any): any {
    try {
      // If it's already an object/array, return as is
      if (typeof jsonString === "object") {
        return jsonString
      }

      // If it's a string that doesn't start with [ or {, it's probably not JSON
      if (typeof jsonString === "string" && !jsonString.trim().startsWith("[") && !jsonString.trim().startsWith("{")) {
        // For types field, if it's a simple string, wrap it in an array
        if (Array.isArray(fallback)) {
          return [jsonString]
        }
        return fallback
      }

      return JSON.parse(jsonString)
    } catch (error) {
      console.log(`JSON parse error for: ${jsonString}, using fallback:`, fallback)
      return fallback
    }
  }

  static async extractPrimaryTypesForPOIs(
    pois: POIExtraction[],
    xpath: string
  ): Promise<Record<string, string>> {
    if (!pois.length) return {};
    const primaryTypes = await POIService.extractPrimaryTypesWithSelenium(pois, xpath);
    const result: Record<string, string> = {};
    pois.forEach((poi, i) => {
      if (poi.place_id) result[poi.place_id] = primaryTypes[i] || "not extracting";
    });
    return result;
  }
}
