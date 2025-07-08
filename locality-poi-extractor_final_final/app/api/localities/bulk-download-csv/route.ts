import { type NextRequest, NextResponse } from "next/server"
import { LocalityService } from "@/services/locality-service"

export async function POST(request: NextRequest) {
  try {
    const { locality_ids, output_type = "all", poi_type = "all" } = await request.json()

    if (!Array.isArray(locality_ids)) {
      return NextResponse.json({ error: "locality_ids must be an array" }, { status: 400 })
    }

    const results = await LocalityService.findByLocalityIdsWithPOIs(locality_ids)

    if (!results.success) {
      return NextResponse.json({ error: results.error }, { status: 500 })
    }

    const allPois: any[] = []

    // Collect all POIs from all localities
    for (const locality of results.data || []) {
      if (locality.pois && locality.pois.length > 0) {
        let pois = locality.pois

        // Filter by output type if specified
        if (output_type !== "all") {
          pois = pois.filter((poi: any) => poi.output_type === output_type)
        }

        // Filter by POI type if specified
        if (poi_type !== "all") {
          pois = pois.filter((poi: any) => poi.poi_type === poi_type)
        }

        allPois.push(...pois)
      }
    }

    // Generate CSV content
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
      "extraction_date",
    ]

    const csvRows = allPois.map((poi: any) => [
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
      poi.extraction_date ? new Date(poi.extraction_date).toISOString().split("T")[0] : "",
    ])

    const csvContent = [
      csvHeaders.join(","),
      ...csvRows.map((row) => row.map((field) => `"${String(field).replace(/"/g, '""')}"`).join(",")),
    ].join("\n")

    const filename = `Bulk_POIs_${output_type}_${new Date().toISOString().split("T")[0]}.csv`

    return new NextResponse(csvContent, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    })
  } catch (error) {
    console.error("Error generating bulk CSV:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
