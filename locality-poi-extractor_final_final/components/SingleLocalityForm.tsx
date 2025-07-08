"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Download, Search, Loader2, CheckCircle, MapPin, Calendar, Database } from "lucide-react"

export default function SingleLocalityForm() {
  const [localityId, setLocalityId] = useState("")
  const [localityPreview, setLocalityPreview] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState("")

  const handleLocalityIdChange = (value: string) => {
    setLocalityId(value)
    setLocalityPreview(null)
    setResult(null)
    setError("")
  }

  const handlePreviewLocality = async () => {
    if (!localityId.trim()) {
      setError("Please enter a locality ID")
      return
    }

    setLoading(true)
    setError("")
    setLocalityPreview(null)

    try {
      // First, just get locality details without POI processing
      const response = await fetch(`/api/localities/preview/${localityId}`)
      const data = await response.json()

      if (response.ok) {
        setLocalityPreview(data)
      } else {
        setError(data.error || "Locality not found")
      }
    } catch (err) {
      setError("Network error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleProcessPOIs = async () => {
    if (!localityPreview) {
      setError("Please preview locality first")
      return
    }

    setProcessing(true)
    setError("")
    setResult(null)

    try {
      const response = await fetch(`/api/localities/${localityId}`)
      const data = await response.json()

      if (response.ok) {
        setResult(data)
      } else {
        setError(data.error || "Failed to extract POIs")
      }
    } catch (err) {
      setError("Network error occurred")
    } finally {
      setProcessing(false)
    }
  }

  const handleDownloadCSV = async (outputType = "all") => {
    if (!result) return

    setDownloading(true)
    try {
      const response = await fetch(`/api/localities/${localityId}/download-csv?output_type=${outputType}`)

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `${result.locality_name}_${result.city}_POIs_${outputType}.csv`
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
      {/* Step 1: Enter Locality ID */}
      <Card>
        <CardHeader>
          <CardTitle>Enter Locality ID</CardTitle>
          <CardDescription>Enter the locality ID to preview details before POI extraction</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="locality-id">Locality ID</Label>
              <Input
                id="locality-id"
                value={localityId}
                onChange={(e) => handleLocalityIdChange(e.target.value)}
                placeholder="Enter locality ID (e.g., 894722)"
                onKeyPress={(e) => e.key === "Enter" && handlePreviewLocality()}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handlePreviewLocality} disabled={loading || !localityId.trim()}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                Preview
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step 2: Locality Preview */}
      {localityPreview && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Verify Locality Details
            </CardTitle>
            <CardDescription>Please confirm this is the correct locality before extracting POIs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Locality Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-green-600" />
                    <span className="font-semibold">Locality Details</span>
                  </div>
                  <div className="text-sm space-y-1">
                    <div>
                      <span className="font-medium">ID:</span> {localityPreview.locality_id}
                    </div>
                    <div>
                      <span className="font-medium">Name:</span> {localityPreview.locality_name}
                    </div>
                    <div>
                      <span className="font-medium">City:</span> {localityPreview.city}
                    </div>
                    <div>
                      <span className="font-medium">Coordinates:</span> {localityPreview.lat}, {localityPreview.lng}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-blue-600" />
                    <span className="font-semibold">Additional Info</span>
                  </div>
                  <div className="text-sm space-y-1">
                    {localityPreview.synonyms && (
                      <div>
                        <span className="font-medium">Synonyms:</span> {localityPreview.synonyms}
                      </div>
                    )}
                    {localityPreview.child_locality && (
                      <div>
                        <span className="font-medium">Child Localities:</span> {localityPreview.child_locality}
                      </div>
                    )}
                    {localityPreview.mp_list && (
                      <div>
                        <span className="font-medium">MP List:</span> {localityPreview.mp_list}
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Created:</span>{" "}
                      {new Date(localityPreview.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* POI Status Check */}
              {localityPreview.poi_status && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="h-4 w-4 text-blue-600" />
                    <span className="font-semibold">POI Extraction Status</span>
                  </div>
                  <div className="text-sm space-y-1">
                    <div>
                      <span className="font-medium">Last Extraction:</span>{" "}
                      {localityPreview.poi_status.last_extraction
                        ? new Date(localityPreview.poi_status.last_extraction).toLocaleDateString()
                        : "Never"}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>{" "}
                      <span
                        className={
                          localityPreview.poi_status.is_fresh ? "text-green-600 font-medium" : "text-orange-600"
                        }
                      >
                        {localityPreview.poi_status.is_fresh ? "Fresh (< 2 months)" : "Needs Update"}
                      </span>
                    </div>
                    {localityPreview.poi_status.total_pois > 0 && (
                      <div>
                        <span className="font-medium">Existing POIs:</span> {localityPreview.poi_status.total_pois}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Button */}
              <div className="flex justify-center">
                <Button onClick={handleProcessPOIs} disabled={processing} size="lg" className="px-8">
                  {processing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                  {processing
                    ? "Extracting POIs..."
                    : localityPreview.poi_status?.is_fresh
                      ? "Load Existing POIs"
                      : "Extract Fresh POIs"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Step 3: Results */}
      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                POI Extraction Results
              </CardTitle>
              <CardDescription>
                {result.locality_name}, {result.city} • Lat: {result.lat}, Lng: {result.lng}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong>Locality ID:</strong> {result.locality_id}
                </div>
                <div>
                  <strong>Total POIs:</strong> {result.pois?.length || 0}
                </div>
                <div>
                  <strong>From Cache:</strong> {result.poi_extraction_info?.from_cache ? "Yes" : "No"}
                </div>
                <div>
                  <strong>Extraction Date:</strong>{" "}
                  {result.poi_extraction_info?.extraction_date
                    ? new Date(result.poi_extraction_info.extraction_date).toLocaleDateString()
                    : "N/A"}
                </div>
              </div>
            </CardContent>
          </Card>

          {result.pois && result.pois.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Download POI Data</CardTitle>
                <CardDescription>Download POI data in CSV format</CardDescription>
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
          )}

          {result.pois && result.pois.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>POI Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {["filtered", "surrounding"].map((type) => {
                    const count = result.pois.filter((poi: any) => poi.output_type === type).length
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
          )}
        </div>
      )}
    </div>
  )
}
