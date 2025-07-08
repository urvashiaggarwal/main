import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const result = await LocalityService.findByLocalityIdWithPOIs(id)

    if (result.success) {
      // Add debugging to see what we're returning
      console.log(`API returning data for ${id}:`)
      console.log(`Total POIs: ${result.data.pois?.length || 0}`)

      if (result.data.pois && result.data.pois.length > 0) {
        console.log(`First POI structure:`, result.data.pois[0])
        const outputTypes = result.data.pois.map((poi: any) => poi.output_type)
        console.log(`All output types: ${outputTypes.join(", ")}`)

        const filteredCount = result.data.pois.filter((poi: any) => poi.output_type === "filtered").length
        const surroundingCount = result.data.pois.filter((poi: any) => poi.output_type === "surrounding").length

        console.log(`Backend counts - Filtered: ${filteredCount}, Surrounding: ${surroundingCount}`)
      }

      return NextResponse.json(result.data)
    } else {
      return NextResponse.json({ error: result.error }, { status: 404 })
    }
  } catch (error) {
    console.error("API Error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
