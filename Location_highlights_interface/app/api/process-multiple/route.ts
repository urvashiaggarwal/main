import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import path from "path"
import fs from "fs"

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const csvFile = formData.get("csvFile") as File

    if (!csvFile) {
      return NextResponse.json({ error: "CSV file is required" }, { status: 400 })
    }

    // Save uploaded CSV file temporarily
    const bytes = await csvFile.arrayBuffer()
    const buffer = Buffer.from(bytes)
    const tempFilePath = path.join(process.cwd(), "temp", `upload_${Date.now()}.csv`)

    // Ensure temp directory exists
    const tempDir = path.dirname(tempFilePath)
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true })
    }

    fs.writeFileSync(tempFilePath, buffer)

    try {
      // Execute integrated Python script for multiple project IDs
      const scriptPath = path.join(process.cwd(), "scripts", "integrated_location_processor.py")
      const command = `python ${scriptPath} --multiple "${tempFilePath}"`

      const { stdout, stderr } = await execAsync(command, {
        timeout: 600000, // 10 minutes timeout for batch processing
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
        totalProjects: results.totalProjects || 0,
        processedCount: results.processedCount || 0,
        failedCount: results.failedCount || 0,
        highlightsCount: results.totalHighlights || 0,
        preview: results.preview || [],
        data: results,
        processedProjects: results.processed_projects,
        failedProjects: results.failed_projects,
        summary: {
          total_poi: results.processed_projects?.reduce((sum: number, p: any) => sum + (p.poi_count || 0), 0) || 0,
          total_golf: results.processed_projects?.reduce((sum: number, p: any) => sum + (p.golf_count || 0), 0) || 0,
          total_airports:
            results.processed_projects?.reduce((sum: number, p: any) => sum + (p.airport_count || 0), 0) || 0,
        },
      })
    } finally {
      // Clean up temporary file
      if (fs.existsSync(tempFilePath)) {
        fs.unlinkSync(tempFilePath)
      }
    }
  } catch (error) {
    console.error("Error processing multiple projects:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
