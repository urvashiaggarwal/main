import { type NextRequest, NextResponse } from "next/server"
import mysql from "mysql2/promise"
import fs from "fs"
import path from "path"
import csv from "csv-parser"

const dbConfig = {
  host: process.env.DB_HOST || "localhost",
  database: process.env.DB_NAME || "location_db",
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASSWORD || "",
  port: Number.parseInt(process.env.DB_PORT || "3306"),
}

interface ProjectData {
  project_id: string
  project_name: string
  latitude: number
  longitude: number
  city: string
}

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
    const tempFilePath = path.join(process.cwd(), "temp", `create_projects_${Date.now()}.csv`)

    // Ensure temp directory exists
    const tempDir = path.dirname(tempFilePath)
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true })
    }

    fs.writeFileSync(tempFilePath, buffer)

    try {
      // Parse CSV file
      const projects: ProjectData[] = []
      const errors: string[] = []

      await new Promise<void>((resolve, reject) => {
        fs.createReadStream(tempFilePath)
          .pipe(csv())
          .on("data", (row) => {
            try {
              const project_id = row.project_id?.toString().trim()
              const project_name = row.project_name?.toString().trim()
              const latitude = Number.parseFloat(row.latitude)
              const longitude = Number.parseFloat(row.longitude)
              const city = row.city?.toString().trim()

              if (!project_id || !project_name || !city) {
                errors.push(`Row with project_id ${project_id || "unknown"}: Missing required fields`)
                return
              }

              if (
                isNaN(latitude) ||
                isNaN(longitude) ||
                latitude < -90 ||
                latitude > 90 ||
                longitude < -180 ||
                longitude > 180
              ) {
                errors.push(`Row with project_id ${project_id}: Invalid latitude or longitude values`)
                return
              }

              projects.push({
                project_id,
                project_name,
                latitude,
                longitude,
                city,
              })
            } catch (error) {
              errors.push(`Error parsing row: ${error instanceof Error ? error.message : "Unknown error"}`)
            }
          })
          .on("end", resolve)
          .on("error", reject)
      })

      if (projects.length === 0) {
        return NextResponse.json(
          {
            error: "No valid projects found in CSV",
            details: errors,
          },
          { status: 400 },
        )
      }

      const connection = await mysql.createConnection(dbConfig)

      try {
        let createdCount = 0
        let skippedCount = 0
        const creationErrors: string[] = []

        for (const project of projects) {
          try {
            // Check if project already exists
            const [existingProjects] = await connection.execute(
              "SELECT project_id FROM projects WHERE project_id = ?",
              [project.project_id],
            )

            if (Array.isArray(existingProjects) && existingProjects.length > 0) {
              skippedCount++
              creationErrors.push(`Project ${project.project_id} already exists`)
              continue
            }

            // Insert new project
            await connection.execute(
              "INSERT INTO projects (project_id, project_name, latitude, longitude, city) VALUES (?, ?, ?, ?, ?)",
              [project.project_id, project.project_name, project.latitude, project.longitude, project.city],
            )

            createdCount++
          } catch (error) {
            creationErrors.push(
              `Failed to create project ${project.project_id}: ${error instanceof Error ? error.message : "Unknown error"}`,
            )
          }
        }

        return NextResponse.json({
          success: true,
          message: `Successfully processed ${projects.length} projects`,
          createdCount,
          skippedCount,
          totalProcessed: projects.length,
          errors: [...errors, ...creationErrors],
        })
      } finally {
        await connection.end()
      }
    } finally {
      // Clean up temporary file
      if (fs.existsSync(tempFilePath)) {
        fs.unlinkSync(tempFilePath)
      }
    }
  } catch (error) {
    console.error("Error creating projects:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
