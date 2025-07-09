import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import path from "path"

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const { projectId } = await request.json()

    if (!projectId) {
      return NextResponse.json({ error: "Project ID is required" }, { status: 400 })
    }

    // Execute integrated Python script for single project ID
    const scriptPath = path.join(process.cwd(), "scripts", "integrated_location_processor.py")
    const command = `python ${scriptPath} --single "${projectId}"`

    const { stdout, stderr } = await execAsync(command, {
      timeout: 300000, // 5 minutes timeout for Google Maps API calls
    })

    // Log stderr for debugging but don't treat as error unless stdout is empty
    if (stderr) {
      console.warn("Python script warnings:", stderr)
    }

    if (!stdout || stdout.trim() === "") {
      console.error("Empty output from Python script")
      return NextResponse.json({ error: "No output from processing script" }, { status: 500 })
    }

    // Clean stdout and attempt to parse JSON
    const cleanOutput = stdout.trim()
    let results

    try {
      results = JSON.parse(cleanOutput)
    } catch (parseError) {
      console.error("JSON parse error:", parseError)
      console.error("Raw output:", stdout)
      return NextResponse.json(
        {
          error: "Invalid response format from processing script",
          details: parseError instanceof Error ? parseError.message : "Unknown parse error",
        },
        { status: 500 },
      )
    }

    if (results.error) {
      return NextResponse.json({ error: results.error }, { status: 400 })
    }

    return NextResponse.json({
      success: true,
      totalProjects: 1,
      processedCount: 1,
      highlightsCount: results.total_highlights || 0,
      preview: results.highlights?.slice(0, 5) || [],
      data: results,
      projectName: results.project_name,
      projectLocation: results.project_location,
      poiCount: results.poi_count,
      golfCount: results.golf_count,
      airportCount: results.airport_count,
      categories: {
        poi: results.poi_count || 0,
        golf: results.golf_count || 0,
        airports: results.airport_count || 0,
      },
    })
  } catch (error) {
    console.error("Error processing single project:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
