import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"

export async function POST(request: NextRequest) {
  try {
    const { locality_ids } = await request.json()

    if (!Array.isArray(locality_ids)) {
      return NextResponse.json({ error: "locality_ids must be an array" }, { status: 400 })
    }

    const results = await LocalityService.findByLocalityIdsWithPOIs(locality_ids)

    if (results.success) {
      // Return all results including both found and not found
      const found = results.data?.filter((item) => item.locality_id && !item.error) || []
      const notFound = results.data?.filter((item) => item.error || item.status === "not_found") || []

      return NextResponse.json({
        found,
        not_found: notFound,
        summary: {
          total_requested: locality_ids.length,
          found_count: found.length,
          not_found_count: notFound.length,
          total_pois: found.reduce((sum, item) => sum + (item.pois?.length || 0), 0),
        },
      })
    } else {
      return NextResponse.json({ error: results.error }, { status: 500 })
    }
  } catch (error) {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
