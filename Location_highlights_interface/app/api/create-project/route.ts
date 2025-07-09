import { type NextRequest, NextResponse } from "next/server"
import mysql from "mysql2/promise"

const dbConfig = {
  host: process.env.DB_HOST || "localhost",
  database: process.env.DB_NAME || "location_db",
  user: process.env.DB_USER || "root",
  password: process.env.DB_PASSWORD || "",
  port: Number.parseInt(process.env.DB_PORT || "3306"),
}

export async function POST(request: NextRequest) {
  try {
    const { project_id, project_name, latitude, longitude, city } = await request.json()

    if (!project_id || !project_name || !latitude || !longitude || !city) {
      return NextResponse.json({ error: "All fields are required" }, { status: 400 })
    }

    // Validate latitude and longitude
    const lat = Number.parseFloat(latitude)
    const lng = Number.parseFloat(longitude)

    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      return NextResponse.json({ error: "Invalid latitude or longitude values" }, { status: 400 })
    }

    const connection = await mysql.createConnection(dbConfig)

    try {
      // Check if project already exists
      const [existingProjects] = await connection.execute("SELECT project_id FROM projects WHERE project_id = ?", [
        project_id,
      ])

      if (Array.isArray(existingProjects) && existingProjects.length > 0) {
        return NextResponse.json({ error: "Project ID already exists" }, { status: 409 })
      }

      // Insert new project
      await connection.execute(
        "INSERT INTO projects (project_id, project_name, latitude, longitude, city) VALUES (?, ?, ?, ?, ?)",
        [project_id, project_name, lat, lng, city],
      )

      return NextResponse.json({
        success: true,
        message: "Project created successfully",
        project: {
          project_id,
          project_name,
          latitude: lat,
          longitude: lng,
          city,
        },
      })
    } finally {
      await connection.end()
    }
  } catch (error) {
    console.error("Error creating project:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
