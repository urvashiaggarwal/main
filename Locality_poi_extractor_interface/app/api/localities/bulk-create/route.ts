import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    const text = await file.text()
    const lines = text.split("\n").filter((line) => line.trim())

    if (lines.length === 0) {
      return NextResponse.json({ error: "CSV file is empty" }, { status: 400 })
    }

    console.log(`📊 Processing CSV with ${lines.length} total lines`)

    // Parse CSV header - handle different possible formats
    const headerLine = lines[0].replace(/\r/g, "") // Remove carriage returns
    const header = headerLine.split(",").map((h) => h.trim().toLowerCase().replace(/"/g, ""))

    console.log(`📋 CSV Headers detected: ${header.join(", ")}`)

    // Check for required fields with flexible naming
    const requiredFieldMappings = {
      locality_id: ["locality_id", "localityid", "id", "locality id"],
      locality_name: ["locality_name", "localityname", "name", "locality name", "locality"],
      city: ["city", "city_name", "cityname"],
      lat: ["lat", "latitude", "lat_value"],
      lng: ["lng", "longitude", "long", "lng_value", "lon"],
    }

    const fieldMapping: Record<string, number> = {}
    const missingFields: string[] = []

    // Map headers to required fields
    for (const [requiredField, possibleNames] of Object.entries(requiredFieldMappings)) {
      let found = false
      for (let i = 0; i < header.length; i++) {
        if (possibleNames.includes(header[i])) {
          fieldMapping[requiredField] = i
          found = true
          break
        }
      }
      if (!found) {
        missingFields.push(requiredField)
      }
    }

    if (missingFields.length > 0) {
      return NextResponse.json(
        {
          error: `Missing required fields: ${missingFields.join(", ")}`,
          detected_headers: header,
          required_fields: Object.keys(requiredFieldMappings),
        },
        { status: 400 },
      )
    }

    console.log(`✅ Field mapping successful:`, fieldMapping)

    // Parse data rows with detailed error tracking
    const localities = []
    const errors: string[] = []
    const skippedRows: number[] = []

    for (let i = 1; i < lines.length; i++) {
      try {
        const line = lines[i].replace(/\r/g, "") // Remove carriage returns
        if (!line.trim()) {
          skippedRows.push(i + 1)
          continue
        }

        // Handle CSV parsing with quoted values
        const values = []
        let current = ""
        let inQuotes = false

        for (let j = 0; j < line.length; j++) {
          const char = line[j]
          if (char === '"') {
            inQuotes = !inQuotes
          } else if (char === "," && !inQuotes) {
            values.push(current.trim())
            current = ""
          } else {
            current += char
          }
        }
        values.push(current.trim()) // Add the last value

        if (values.length < Math.max(...Object.values(fieldMapping)) + 1) {
          errors.push(`Row ${i + 1}: Insufficient columns (expected ${header.length}, got ${values.length})`)
          skippedRows.push(i + 1)
          continue
        }

        // Extract and validate data
        const locality: any = {}

        // Required fields
        locality.locality_id = values[fieldMapping.locality_id]?.replace(/"/g, "").trim()
        locality.locality_name = values[fieldMapping.locality_name]?.replace(/"/g, "").trim()
        locality.city = values[fieldMapping.city]?.replace(/"/g, "").trim()

        // Parse coordinates
        const latStr = values[fieldMapping.lat]?.replace(/"/g, "").trim()
        const lngStr = values[fieldMapping.lng]?.replace(/"/g, "").trim()

        locality.lat = Number.parseFloat(latStr)
        locality.lng = Number.parseFloat(lngStr)

        // Validation
        if (!locality.locality_id || !locality.locality_name || !locality.city) {
          errors.push(
            `Row ${i + 1}: Missing required data (locality_id: "${locality.locality_id}", locality_name: "${locality.locality_name}", city: "${locality.city}")`,
          )
          skippedRows.push(i + 1)
          continue
        }

        if (isNaN(locality.lat) || isNaN(locality.lng)) {
          errors.push(`Row ${i + 1}: Invalid coordinates (lat: "${latStr}", lng: "${lngStr}")`)
          skippedRows.push(i + 1)
          continue
        }

        // Coordinate range validation
        if (locality.lat < -90 || locality.lat > 90 || locality.lng < -180 || locality.lng > 180) {
          errors.push(`Row ${i + 1}: Coordinates out of range (lat: ${locality.lat}, lng: ${locality.lng})`)
          skippedRows.push(i + 1)
          continue
        }

        // Optional fields
        const optionalFieldMappings = {
          synonyms: ["synonyms", "synonym"],
          child_locality: ["child_locality", "child locality", "child_localities"],
          mp_list: ["mp_list", "mp list", "mplist"],
        }

        for (const [optionalField, possibleNames] of Object.entries(optionalFieldMappings)) {
          for (let j = 0; j < header.length; j++) {
            if (possibleNames.includes(header[j]) && values[j]) {
              locality[optionalField] = values[j].replace(/"/g, "").trim()
              break
            }
          }
        }

        localities.push(locality)
      } catch (error) {
        errors.push(`Row ${i + 1}: Parsing error - ${error}`)
        skippedRows.push(i + 1)
      }
    }

    console.log(`📊 Parsing Results:`)
    console.log(`   Total lines: ${lines.length}`)
    console.log(`   Valid localities parsed: ${localities.length}`)
    console.log(`   Skipped rows: ${skippedRows.length}`)
    console.log(`   Parsing errors: ${errors.length}`)

    if (localities.length === 0) {
      return NextResponse.json(
        {
          error: "No valid localities found in CSV",
          parsing_errors: errors.slice(0, 10), // Show first 10 errors
          total_errors: errors.length,
          skipped_rows: skippedRows.slice(0, 20), // Show first 20 skipped rows
        },
        { status: 400 },
      )
    }

    // Attempt bulk creation with detailed tracking
    console.log(`🚀 Starting bulk creation of ${localities.length} localities...`)
    const result = await LocalityService.createBulk(localities)

    // Enhanced response with detailed breakdown + backward compatibility
    const response = {
      success: result.success,
      // Old format for backward compatibility
      created: result.data?.created || 0,
      skipped: result.data?.skipped || 0,
      errors: result.data?.errors || [],
      // New detailed format
      summary: {
        total_lines_in_csv: lines.length - 1, // Exclude header
        valid_localities_parsed: localities.length,
        successfully_created: result.data?.created || 0,
        skipped_duplicates: result.data?.skipped || 0,
        parsing_errors: errors.length,
        skipped_rows_count: skippedRows.length,
      },
      details: {
        created_count: result.data?.created || 0,
        skipped_count: result.data?.skipped || 0,
        creation_errors: result.data?.errors || [],
        parsing_errors: errors.slice(0, 10), // First 10 parsing errors
        skipped_rows: skippedRows.slice(0, 20), // First 20 skipped row numbers
        duplicates: result.data?.duplicates || [],
      },
      message: result.message || `Processed ${localities.length} localities from CSV`,
    }

    return NextResponse.json(response)
  } catch (error) {
    console.error("Bulk create error:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
