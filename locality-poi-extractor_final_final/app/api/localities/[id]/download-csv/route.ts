import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const { searchParams } = new URL(request.url)
    const outputType = searchParams.get("output_type") || "all"
    const poiType = searchParams.get("poi_type") || "all"

    const result = await LocalityService.findByLocalityIdWithPOIs(id)

    if (!result.success || !result.data) {
      return NextResponse.json({ error: result.error || "Locality not found" }, { status: 404 })
    }

    const locality = result.data
    let pois = locality.pois || []

    // Filter by output type if specified
    if (outputType !== "all") {
      pois = pois.filter((poi: any) => poi.output_type === outputType)
    }

    // Filter by POI type if specified
    if (poiType !== "all") {
      pois = pois.filter((poi: any) => poi.poi_type === poiType)
    }

    // Generate CSV content with enhanced fields
    const csvHeaders = [
      "locality_id",
      "locality_name",
      "city",
      "poi_type",
      "output_type",
      "name",
      "place_id",
      "primary_type",
      "api_primary_type",
      "address",
      "rating",
      "rating_count",
      "lat",
      "lng",
      "google_map_url",
      "business_status",
      "website",
      "wheelchair_accessible",
      "parking_options",
      "photos_reference",
      "extraction_date",
    ]

    const csvRows = pois.map((poi: any) => [
      poi.locality_id || "",
      poi.locality_name || "",
      poi.city || "",
      poi.poi_type || "",
      poi.output_type || "",
      poi.name || "",
      poi.place_id || "",
      poi.primary_type || "",
      poi.api_primary_type || "",
      poi.address || "",
      poi.rating || "",
      poi.rating_count || "",
      poi.lat || "",
      poi.lng || "",
      poi.google_map_url || "",
      poi.business_status || "",
      poi.website || "",
      poi.wheelchair_accessible !== null ? poi.wheelchair_accessible : "",
      poi.parking_options ? JSON.stringify(poi.parking_options) : "",
      poi.photos_reference ? JSON.stringify(poi.photos_reference) : "",
      poi.extraction_date ? new Date(poi.extraction_date).toISOString().split("T")[0] : "",
    ])

    const csvContent = [
      csvHeaders.join(","),
      ...csvRows.map((row) => row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(",")),
    ].join("\n")

    const filename = `${locality.locality_name}_${locality.city}_POIs_${outputType}_${new Date().toISOString().split("T")[0]}.csv`

    return new NextResponse(csvContent, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    })
  } catch (error) {
    console.error("Error generating CSV:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
