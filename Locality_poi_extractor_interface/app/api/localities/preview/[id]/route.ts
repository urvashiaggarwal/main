import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"
import { POIService } from "@/services/poi-service"

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params

    // Get locality details without triggering POI extraction
    const result = await LocalityService.findByLocalityId(id, true) // Auto-generate MP list if missing

    if (result.success && result.data) {
      // Check POI status without extracting
      const poiStatus = await POIService.checkPOIFreshness(id)

      // Get existing POI count if available
      let totalPois = 0
      if (poiStatus.hasFreshPOIs) {
        const existingPois = await POIService.getAllPOIsForLocality(id)
        totalPois = existingPois.length
      }

      const response = {
        ...result.data,
        poi_status: {
          is_fresh: poiStatus.hasFreshPOIs,
          last_extraction: poiStatus.extractionDate,
          total_pois: totalPois,
        },
      }

      return NextResponse.json(response)
    } else {
      return NextResponse.json({ error: result.error || "Locality not found" }, { status: 404 })
    }
  } catch (error) {
    console.error("Preview API Error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
