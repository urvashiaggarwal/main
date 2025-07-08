"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Download, Upload, Loader2, AlertTriangle, XCircle } from "lucide-react"

export default function MultipleLocalityForm() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState("")

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.type === "text/csv") {
      setFile(selectedFile)
      setError("")
    } else {
      setError("Please select a valid CSV file")
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file")
      return
    }

    setLoading(true)
    setError("")
    setResults(null)

    try {
      // First, read the CSV to extract locality IDs
      const text = await file.text()
      const lines = text.split("\n").filter((line) => line.trim())

      if (lines.length === 0) {
        setError("CSV file is empty")
        return
      }

      // Assume first column is locality_id
      const localityIds = lines
        .slice(1)
        .map((line) => {
          const columns = line.split(",")
          return columns[0]?.trim().replace(/"/g, "")
        })
        .filter((id) => id)

      if (localityIds.length === 0) {
        setError("No valid locality IDs found in CSV")
        return
      }

      // Call bulk API
      const response = await fetch("/api/localities/bulk", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ locality_ids: localityIds }),
      })

      const data = await response.json()

      if (response.ok) {
        setResults(data)
      } else {
        setError(data.error || "Failed to process localities")
      }
    } catch (err) {
      setError("Error processing file")
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadCSV = async (outputType = "all") => {
    if (!results || !results.found) return

    setDownloading(true)
    try {
      const localityIds = results.found.map((item: any) => item.locality_id)

      const response = await fetch("/api/localities/bulk-download-csv", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          locality_ids: localityIds,
          output_type: outputType,
        }),
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `Bulk_POIs_${outputType}_${new Date().toISOString().split("T")[0]}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        setError("Failed to download CSV")
      }
    } catch (err) {
      setError("Download failed")
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="csv-file">CSV File</Label>
          <Input id="csv-file" type="file" accept=".csv" onChange={handleFileChange} />
          <p className="text-sm text-muted-foreground mt-1">CSV should have locality_id in the first column</p>
        </div>

        <Button onClick={handleUpload} disabled={loading || !file}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Upload className="w-4 h-4 mr-2" />}
          Process CSV
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {results && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Processing Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">{results.summary?.found_count || 0}</div>
                  <div className="text-sm text-muted-foreground">Found</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">{results.summary?.not_found_count || 0}</div>
                  <div className="text-sm text-muted-foreground">Not Found</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">{results.summary?.total_pois || 0}</div>
                  <div className="text-sm text-muted-foreground">Total POIs</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Show Not Found Locality IDs */}
          {results.not_found && results.not_found.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-red-600" />
                  Locality IDs Not Found ({results.not_found.length})
                </CardTitle>
                <CardDescription>These locality IDs from your CSV were not found in the database</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
                  {results.not_found.map((item: any, index: number) => (
                    <div
                      key={index}
                      className="px-2 py-1 bg-red-50 border border-red-200 rounded text-sm text-red-700 text-center font-mono"
                    >
                      {item.locality_id || item}
                    </div>
                  ))}
                </div>
                {results.not_found.length > 50 && (
                  <div className="mt-2 text-sm text-muted-foreground">
                    Showing first 50 of {results.not_found.length} not found locality IDs
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Show Found Localities Summary */}
          {results.found && results.found.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Download className="h-5 w-5 text-green-600" />
                  Found Localities ({results.found.length})
                </CardTitle>
                <CardDescription>These localities were found and POI data is available</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {results.found.slice(0, 20).map((locality: any, index: number) => (
                    <div key={index} className="flex justify-between items-center text-sm border-b pb-1">
                      <div>
                        <span className="font-mono text-blue-600">{locality.locality_id}</span>
                        <span className="ml-2">
                          {locality.locality_name}, {locality.city}
                        </span>
                      </div>
                      <div className="text-muted-foreground">{locality.pois?.length || 0} POIs</div>
                    </div>
                  ))}
                  {results.found.length > 20 && (
                    <div className="text-sm text-muted-foreground text-center pt-2">
                      ... and {results.found.length - 20} more localities
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {results.found && results.found.length > 0 && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Download Bulk POI Data</CardTitle>
                  <CardDescription>Download all POI data in CSV format</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2 flex-wrap">
                    <Button onClick={() => handleDownloadCSV("all")} disabled={downloading} variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      All POIs
                    </Button>
                    <Button onClick={() => handleDownloadCSV("filtered")} disabled={downloading} variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      Filtered Only
                    </Button>
                    <Button onClick={() => handleDownloadCSV("surrounding")} disabled={downloading} variant="outline">
                      <Download className="w-4 h-4 mr-2" />
                      Surrounding Only
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>POI Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {["filtered", "surrounding"].map((type) => {
                      const count = results.found.reduce((sum: number, locality: any) => {
                        return sum + (locality.pois?.filter((poi: any) => poi.output_type === type).length || 0)
                      }, 0)
                      return (
                        <div key={type} className="text-center">
                          <div className="text-2xl font-bold">{count}</div>
                          <div className="text-sm text-muted-foreground capitalize">{type}</div>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {/* Warning for Not Found IDs */}
          {results.not_found && results.not_found.length > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>{results.not_found.length} locality IDs were not found</strong> in the database. You may need to
                create these localities first using the "Create Locality" tab, or verify that the locality IDs are
                correct.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  )
}
