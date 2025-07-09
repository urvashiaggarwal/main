import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { results } = await request.json()

    if (!results || !results.data) {
      return NextResponse.json({ error: "No results data provided" }, { status: 400 })
    }

    // Convert results to CSV format matching the exact columns requested
    const csvData = convertToCSV(results.data)

    return new NextResponse(csvData, {
      status: 200,
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": 'attachment; filename="location-highlights-results.csv"',
      },
    })
  } catch (error) {
    console.error("Error generating CSV download:", error)
    return NextResponse.json({ error: "Failed to generate CSV" }, { status: 500 })
  }
}

function convertToCSV(data: any): string {
  if (!data.highlights || !Array.isArray(data.highlights)) {
    return "POI Type,name,address,Distance (km),step1_score\n"
  }

  // Use exact column headers as requested
  const headers = ["POI Type", "name", "address", "Distance (km)", "step1_score"]
  const csvRows = [headers.join(",")]

  data.highlights.forEach((highlight: any) => {
    const row = [
      highlight.poi_type || "",
      `"${(highlight.name || "").replace(/"/g, '""')}"`,
      `"${(highlight.address || "").replace(/"/g, '""')}"`,
      highlight.distance_km || "",
      highlight.step1_score || "",
    ]
    csvRows.push(row.join(","))
  })

  return csvRows.join("\n")
}
