"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, CheckCircle } from "lucide-react"

export default function CreateLocalityForm() {
  const [formData, setFormData] = useState({
    locality_id: "",
    locality_name: "",
    city: "",
    lat: "",
    lng: "",
    synonyms: "",
    child_locality: "",
    mp_list: "",
  })
  const [success, setSuccess] = useState("")
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setError("")
    setSuccess("")
  }

  const validateForm = (): boolean => {
    if (!formData.locality_id.trim()) {
      setError("Locality ID is required")
      return false
    }
    if (!formData.locality_name.trim()) {
      setError("Locality Name is required")
      return false
    }
    if (!formData.city.trim()) {
      setError("City is required")
      return false
    }
    if (!formData.lat.trim() || isNaN(Number(formData.lat))) {
      setError("Valid Latitude is required")
      return false
    }
    if (!formData.lng.trim() || isNaN(Number(formData.lng))) {
      setError("Valid Longitude is required")
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsSubmitting(true)
    setError("")

    try {
      const newLocality = {
        locality_id: formData.locality_id.trim(),
        locality_name: formData.locality_name.trim(),
        city: formData.city.trim(),
        lat: Number(formData.lat),
        lng: Number(formData.lng),
        synonyms: formData.synonyms.trim() || undefined,
        child_locality: formData.child_locality.trim() || undefined,
        mp_list: formData.mp_list.trim() || undefined,
      }

      const response = await fetch("/api/localities", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newLocality),
      })

      if (response.ok) {
        const createdLocality = await response.json()
        setSuccess(
          `Locality "${createdLocality.locality_name}" created successfully with ID: ${createdLocality.locality_id}`,
        )
        setFormData({
          locality_id: "",
          locality_name: "",
          city: "",
          lat: "",
          lng: "",
          synonyms: "",
          child_locality: "",
          mp_list: "",
        })
      } else {
        const errorData = await response.json()
        setError(errorData.error || "Failed to create locality")
      }
    } catch (error) {
      console.error("Create error:", error)
      setError("Network error. Please check your connection and try again.")
    }

    setIsSubmitting(false)
  }

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsSubmitting(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/api/localities/bulk-create", {
        method: "POST",
        body: formData,
      })

      const result = await response.json()

      if (response.ok) {
        setSuccess(`CSV processed successfully! Created: ${result.created}, Skipped: ${result.skipped} localities`)
        if (result.errors && result.errors.length > 0) {
          setError(
            `Some errors occurred: ${result.errors.slice(0, 3).join(", ")}${result.errors.length > 3 ? "..." : ""}`,
          )
        }
      } else {
        setError(result.error || "Failed to process CSV")
      }
    } catch (error) {
      setError("Error uploading CSV file")
    }

    setIsSubmitting(false)
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="single" className="w-full">
        <TabsList>
          <TabsTrigger value="single">Single Entry</TabsTrigger>
          <TabsTrigger value="bulk">Bulk Upload (CSV)</TabsTrigger>
        </TabsList>

        <TabsContent value="single">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="locality_id">Locality ID *</Label>
                <Input
                  id="locality_id"
                  value={formData.locality_id}
                  onChange={(e) => handleInputChange("locality_id", e.target.value)}
                  placeholder="e.g., LOC004"
                  required
                />
              </div>
              <div>
                <Label htmlFor="locality_name">Locality Name *</Label>
                <Input
                  id="locality_name"
                  value={formData.locality_name}
                  onChange={(e) => handleInputChange("locality_name", e.target.value)}
                  placeholder="e.g., Bandra West"
                  required
                />
              </div>
              <div>
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleInputChange("city", e.target.value)}
                  placeholder="e.g., Mumbai"
                  required
                />
              </div>
              <div>
                <Label htmlFor="lat">Latitude *</Label>
                <Input
                  id="lat"
                  type="number"
                  step="any"
                  value={formData.lat}
                  onChange={(e) => handleInputChange("lat", e.target.value)}
                  placeholder="e.g., 19.0544"
                  required
                />
              </div>
              <div>
                <Label htmlFor="lng">Longitude *</Label>
                <Input
                  id="lng"
                  type="number"
                  step="any"
                  value={formData.lng}
                  onChange={(e) => handleInputChange("lng", e.target.value)}
                  placeholder="e.g., 72.8381"
                  required
                />
              </div>
              <div>
                <Label htmlFor="synonyms">Synonyms (Optional)</Label>
                <Input
                  id="synonyms"
                  value={formData.synonyms}
                  onChange={(e) => handleInputChange("synonyms", e.target.value)}
                  placeholder="e.g., Bandra, West Bandra"
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="child_locality">Child Localities (Optional)</Label>
                <Textarea
                  id="child_locality"
                  value={formData.child_locality}
                  onChange={(e) => handleInputChange("child_locality", e.target.value)}
                  placeholder="e.g., Linking Road, Hill Road, Carter Road"
                  rows={2}
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="mp_list">MP List (Optional)</Label>
                <Input
                  id="mp_list"
                  value={formData.mp_list}
                  onChange={(e) => handleInputChange("mp_list", e.target.value)}
                  placeholder="e.g., MP006, MP007"
                />
              </div>
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              {isSubmitting ? "Creating..." : "Create Locality"}
            </Button>
          </form>
        </TabsContent>

        <TabsContent value="bulk">
          <Card>
            <CardHeader>
              <CardTitle>Bulk Upload via CSV</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="csv-upload">CSV File</Label>
                  <Input
                    id="csv-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleCSVUpload}
                    className="cursor-pointer"
                    disabled={isSubmitting}
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Required columns: locality_id, locality_name, city, lat, lng
                    <br />
                    Optional columns: synonyms, child_locality, mp_list
                    <br />
                    <strong>Note:</strong> Duplicate locality IDs will be skipped automatically
                  </p>
                </div>
                {isSubmitting && (
                  <div className="text-sm text-muted-foreground">Processing CSV file... This may take a moment.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
