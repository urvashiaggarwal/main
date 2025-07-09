"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import {
  Upload,
  Download,
  Search,
  FileText,
  Database,
  MapPin,
  TrendingUp,
  CheckCircle,
  Eye,
  Filter,
  Plane,
  Building,
  TreePine,
  RefreshCw,
  Loader2,
  Plus,
  AlertCircle,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export default function IntegratedLocationHighlightsFinder() {
  const [singleProjectId, setSingleProjectId] = useState("")
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [activeTab, setActiveTab] = useState("single")
  const [showResults, setShowResults] = useState(false)
  const [filterType, setFilterType] = useState("all")
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [missingProjectId, setMissingProjectId] = useState("")

  // Create project form states
  const [newProject, setNewProject] = useState({
    project_id: "",
    project_name: "",
    latitude: "",
    longitude: "",
    city: "",
  })
  const [createProjectCsv, setCreateProjectCsv] = useState<File | null>(null)
  const [isCreatingProject, setIsCreatingProject] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const createProjectFileRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!singleProjectId.trim()) {
      toast({
        title: "Error",
        description: "Please enter a project ID",
        variant: "destructive",
      })
      return
    }

    setIsProcessing(true)
    setShowResults(false)
    setShowCreateProject(false)

    try {
      const response = await fetch("/api/process-single", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ projectId: singleProjectId }),
      })

      if (!response.ok) {
        throw new Error("Failed to process project ID")
      }

      const data = await response.json()

      if (data.error && data.error.includes("not found")) {
        setMissingProjectId(singleProjectId)
        setShowCreateProject(true)
        setNewProject((prev) => ({ ...prev, project_id: singleProjectId }))
        toast({
          title: "Project Not Found",
          description: `Project ID ${singleProjectId} doesn't exist. Please create it first.`,
          variant: "destructive",
        })
        return
      }

      setResults(data)
      setShowResults(true)

      const cacheMessage = data.data?.from_cache
        ? `Retrieved ${data.highlightsCount} cached highlights (${data.data.cache_age_days} days old)`
        : `Generated ${data.highlightsCount} fresh highlights`

      toast({
        title: "Success",
        description: cacheMessage,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to process project ID",
        variant: "destructive",
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    const file = files[0]

    if (file && file.type === "text/csv") {
      setCsvFile(file)
      toast({
        title: "File uploaded",
        description: `Selected: ${file.name}`,
      })
    } else {
      toast({
        title: "Error",
        description: "Please upload a valid CSV file",
        variant: "destructive",
      })
    }
  }

  const handleCsvUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === "text/csv") {
      setCsvFile(file)
      toast({
        title: "File uploaded",
        description: `Selected: ${file.name}`,
      })
    } else {
      toast({
        title: "Error",
        description: "Please upload a valid CSV file",
        variant: "destructive",
      })
    }
  }

  const handleCreateProjectCsvUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === "text/csv") {
      setCreateProjectCsv(file)
      toast({
        title: "File uploaded",
        description: `Selected: ${file.name}`,
      })
    } else {
      toast({
        title: "Error",
        description: "Please upload a valid CSV file",
        variant: "destructive",
      })
    }
  }

  const handleMultipleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!csvFile) {
      toast({
        title: "Error",
        description: "Please upload a CSV file",
        variant: "destructive",
      })
      return
    }

    setIsProcessing(true)
    setShowResults(false)
    setShowCreateProject(false)

    const formData = new FormData()
    formData.append("csvFile", csvFile)

    try {
      const response = await fetch("/api/process-multiple", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to process CSV file")
      }

      const data = await response.json()

      if (data.data?.failed_projects && data.data.failed_projects.length > 0) {
        const missingProjects = data.data.failed_projects.filter((p: any) => p.error.includes("not found"))

        if (missingProjects.length > 0) {
          toast({
            title: "Some Projects Not Found",
            description: `${missingProjects.length} projects need to be created. Check the results for details.`,
            variant: "destructive",
          })
        }
      }

      setResults(data)
      setShowResults(true)

      const cacheInfo =
        data.data?.cachedCount > 0 ? ` (${data.data.cachedCount} from cache, ${data.processedCount} fresh)` : ""

      toast({
        title: "Success",
        description: `Processed ${data.totalProjects} projects with ${data.highlightsCount} total highlights${cacheInfo}`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to process CSV file",
        variant: "destructive",
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCreateSingleProject = async (e: React.FormEvent) => {
    e.preventDefault()

    if (
      !newProject.project_id ||
      !newProject.project_name ||
      !newProject.latitude ||
      !newProject.longitude ||
      !newProject.city
    ) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    setIsCreatingProject(true)

    try {
      const response = await fetch("/api/create-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newProject),
      })

      if (!response.ok) {
        throw new Error("Failed to create project")
      }

      const data = await response.json()

      toast({
        title: "Success",
        description: `Project ${newProject.project_id} created successfully!`,
      })

      // Reset form
      setNewProject({
        project_id: "",
        project_name: "",
        latitude: "",
        longitude: "",
        city: "",
      })
      setShowCreateProject(false)
      setMissingProjectId("")
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create project",
        variant: "destructive",
      })
    } finally {
      setIsCreatingProject(false)
    }
  }

  const handleCreateMultipleProjects = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!createProjectCsv) {
      toast({
        title: "Error",
        description: "Please upload a CSV file",
        variant: "destructive",
      })
      return
    }

    setIsCreatingProject(true)

    const formData = new FormData()
    formData.append("csvFile", createProjectCsv)

    try {
      const response = await fetch("/api/create-projects", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to create projects")
      }

      const data = await response.json()

      toast({
        title: "Success",
        description: `Created ${data.createdCount} projects successfully!`,
      })

      // Reset form
      setCreateProjectCsv(null)
      if (createProjectFileRef.current) {
        createProjectFileRef.current.value = ""
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create projects",
        variant: "destructive",
      })
    } finally {
      setIsCreatingProject(false)
    }
  }

  const downloadResults = async () => {
    if (!results) return

    try {
      const response = await fetch("/api/download-results", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ results }),
      })

      if (!response.ok) {
        throw new Error("Failed to generate download")
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.style.display = "none"
      a.href = url
      a.download = `location-highlights-${new Date().toISOString().split("T")[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: "Success",
        description: "Results downloaded successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download results",
        variant: "destructive",
      })
    }
  }

  const getFilteredResults = () => {
    if (!results?.preview && !results?.data?.highlights) return []

    const highlights = results.preview || results.data?.highlights || []

    if (filterType === "all") return highlights

    return highlights.filter((item: any) => {
      if (filterType === "poi") return item.category === "poi"
      if (filterType === "golf") return item.poi_type === "golf_course"
      if (filterType === "airport") return item.poi_type === "airport"
      return item.poi_type?.toLowerCase().includes(filterType.toLowerCase())
    })
  }

  const getCategoryIcon = (category: string, highlightType: string) => {
    if (highlightType === "airport") return <Plane className="h-4 w-4" />
    if (highlightType === "golf_course") return <TreePine className="h-4 w-4" />
    if (category === "poi") return <Building className="h-4 w-4" />
    return <MapPin className="h-4 w-4" />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Animated Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full">
              <MapPin className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Smart Location Intelligence
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Intelligent caching with 2-month freshness • Google Maps API integration • Advanced scoring algorithms
          </p>
        </div>

        {/* Main Interface Card */}
        <Card className="mb-6 shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-blue-500/10 to-purple-500/10">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              Cached Analysis Engine
            </CardTitle>
            <CardDescription>
              Smart caching system • Reuses data ≤2 months old • Fresh processing when needed
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <Tabs
              value={activeTab}
              onValueChange={(tab) => {
                setActiveTab(tab);
                setShowResults(false);
                setResults(null);
              }}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3 mb-6 bg-gray-100">
                <TabsTrigger
                  value="single"
                  className="flex items-center gap-2 transition-all duration-200 data-[state=active]:bg-blue-500 data-[state=active]:text-white"
                >
                  <Search className="h-4 w-4" />
                  Single Project
                </TabsTrigger>
                <TabsTrigger
                  value="multiple"
                  className="flex items-center gap-2 transition-all duration-200 data-[state=active]:bg-purple-500 data-[state=active]:text-white"
                >
                  <Upload className="h-4 w-4" />
                  Batch Processing
                </TabsTrigger>
                <TabsTrigger
                  value="create"
                  className="flex items-center gap-2 transition-all duration-200 data-[state=active]:bg-green-500 data-[state=active]:text-white"
                >
                  <Plus className="h-4 w-4" />
                  Create Projects
                </TabsTrigger>
              </TabsList>

              <TabsContent value="single" className="space-y-6">
                <form onSubmit={handleSingleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="projectId" className="text-sm font-medium">
                      Project ID
                    </Label>
                    <div className="relative">
                      <Input
                        id="projectId"
                        type="text"
                        placeholder="Enter project ID (e.g., 418319)"
                        value={singleProjectId}
                        onChange={(e) => setSingleProjectId(e.target.value)}
                        className="w-full pl-10 transition-all duration-200 focus:ring-2 focus:ring-blue-500"
                      />
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    </div>
                  </div>
                  <Button
                    type="submit"
                    disabled={isProcessing}
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-[1.02]"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4 mr-2" />
                        Generate Location Intelligence
                      </>
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="multiple" className="space-y-6">
                <form onSubmit={handleMultipleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="csvFile" className="text-sm font-medium">
                      CSV File with Project IDs
                    </Label>
                    <div
                      className={`relative transition-all duration-300 ${
                        isDragOver ? "scale-105 border-purple-400 bg-purple-50" : ""
                      }`}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    >
                      <label
                        htmlFor="csvFile"
                        className={`flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300 ${
                          isDragOver ? "border-purple-400 bg-purple-50" : "border-gray-300 bg-gray-50 hover:bg-gray-100"
                        }`}
                      >
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          <div
                            className={`p-3 rounded-full mb-4 transition-all duration-300 ${
                              isDragOver ? "bg-purple-200" : "bg-gray-200"
                            }`}
                          >
                            <Upload
                              className={`w-6 h-6 transition-colors duration-300 ${
                                isDragOver ? "text-purple-600" : "text-gray-500"
                              }`}
                            />
                          </div>
                          <p className="mb-2 text-sm text-gray-500">
                            <span className="font-semibold">Click to upload</span> or drag and drop
                          </p>
                          <p className="text-xs text-gray-500">CSV files only</p>
                          {csvFile && (
                            <div className="mt-3 flex items-center gap-2 px-3 py-1 bg-green-100 rounded-full">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              <span className="text-sm text-green-700">{csvFile.name}</span>
                            </div>
                          )}
                        </div>
                        <input
                          ref={fileInputRef}
                          id="csvFile"
                          type="file"
                          accept=".csv"
                          onChange={handleCsvUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                  </div>
                  <Button
                    type="submit"
                    disabled={isProcessing || !csvFile}
                    className="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-[1.02]"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Process Multiple Projects
                      </>
                    )}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="create" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Single Project Creation */}
                  <Card className="border-2 border-green-200">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-700">
                        <Plus className="h-5 w-5" />
                        Create Single Project
                      </CardTitle>
                      <CardDescription>Add a new project with location details</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleCreateSingleProject} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="newProjectId" className="text-sm font-medium">
                            Project ID *
                          </Label>
                          <Input
                            id="newProjectId"
                            type="text"
                            placeholder="e.g., 418319"
                            value={newProject.project_id}
                            onChange={(e) => setNewProject((prev) => ({ ...prev, project_id: e.target.value }))}
                            className="transition-all duration-200 focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="newProjectName" className="text-sm font-medium">
                            Project Name *
                          </Label>
                          <Input
                            id="newProjectName"
                            type="text"
                            placeholder="e.g., Brigade Sanctuary"
                            value={newProject.project_name}
                            onChange={(e) => setNewProject((prev) => ({ ...prev, project_name: e.target.value }))}
                            className="transition-all duration-200 focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="newLatitude" className="text-sm font-medium">
                              Latitude *
                            </Label>
                            <Input
                              id="newLatitude"
                              type="number"
                              step="any"
                              placeholder="e.g., 12.895087"
                              value={newProject.latitude}
                              onChange={(e) => setNewProject((prev) => ({ ...prev, latitude: e.target.value }))}
                              className="transition-all duration-200 focus:ring-2 focus:ring-green-500"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="newLongitude" className="text-sm font-medium">
                              Longitude *
                            </Label>
                            <Input
                              id="newLongitude"
                              type="number"
                              step="any"
                              placeholder="e.g., 77.749055"
                              value={newProject.longitude}
                              onChange={(e) => setNewProject((prev) => ({ ...prev, longitude: e.target.value }))}
                              className="transition-all duration-200 focus:ring-2 focus:ring-green-500"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="newCity" className="text-sm font-medium">
                            City *
                          </Label>
                          <Input
                            id="newCity"
                            type="text"
                            placeholder="e.g., Bangalore East"
                            value={newProject.city}
                            onChange={(e) => setNewProject((prev) => ({ ...prev, city: e.target.value }))}
                            className="transition-all duration-200 focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <Button
                          type="submit"
                          disabled={isCreatingProject}
                          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 transition-all duration-200"
                        >
                          {isCreatingProject ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Creating...
                            </>
                          ) : (
                            <>
                              <Plus className="h-4 w-4 mr-2" />
                              Create Project
                            </>
                          )}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>

                  {/* Multiple Projects Creation */}
                  <Card className="border-2 border-green-200">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-700">
                        <Upload className="h-5 w-5" />
                        Create Multiple Projects
                      </CardTitle>
                      <CardDescription>
                        Upload CSV with project details (project_id, project_name, latitude, longitude, city)
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleCreateMultipleProjects} className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="createProjectCsv" className="text-sm font-medium">
                            CSV File with Project Details
                          </Label>
                          <label
                            htmlFor="createProjectCsv"
                            className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-green-300 rounded-xl cursor-pointer bg-green-50 hover:bg-green-100 transition-all duration-300"
                          >
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                              <div className="p-2 rounded-full mb-2 bg-green-200">
                                <Upload className="w-5 h-5 text-green-600" />
                              </div>
                              <p className="mb-1 text-sm text-green-700">
                                <span className="font-semibold">Click to upload</span>
                              </p>
                              <p className="text-xs text-green-600">CSV files only</p>
                              {createProjectCsv && (
                                <div className="mt-2 flex items-center gap-2 px-2 py-1 bg-green-200 rounded-full">
                                  <CheckCircle className="h-3 w-3 text-green-700" />
                                  <span className="text-xs text-green-700">{createProjectCsv.name}</span>
                                </div>
                              )}
                            </div>
                            <input
                              ref={createProjectFileRef}
                              id="createProjectCsv"
                              type="file"
                              accept=".csv"
                              onChange={handleCreateProjectCsvUpload}
                              className="hidden"
                            />
                          </label>
                        </div>
                        <Button
                          type="submit"
                          disabled={isCreatingProject || !createProjectCsv}
                          className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 transition-all duration-200"
                        >
                          {isCreatingProject ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Creating...
                            </>
                          ) : (
                            <>
                              <Upload className="h-4 w-4 mr-2" />
                              Create Projects
                            </>
                          )}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Create Project Alert */}
        {showCreateProject && (
          <Card className="mb-6 border-2 border-orange-200 bg-orange-50">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <AlertCircle className="h-6 w-6 text-orange-600 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-orange-800 mb-2">Project Not Found</h3>
                  <p className="text-orange-700 mb-4">
                    Project ID "{missingProjectId}" doesn't exist in the database. Please create it first using the
                    "Create Projects" tab.
                  </p>
                  <Button
                    onClick={() => {
                      setActiveTab("create")
                      setShowCreateProject(false)
                    }}
                    className="bg-orange-600 hover:bg-orange-700 text-white"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Go to Create Projects
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {showResults && results && (
          <div className="space-y-6 animate-fade-in">
            {/* Download Button - Always visible when results exist */}
            <div className="flex justify-end">
              <Button
                onClick={downloadResults}
                className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 shadow-lg"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Results CSV
              </Button>
            </div>

            {/* Enhanced Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
              <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100 text-sm">Total Projects</p>
                      <p className="text-3xl font-bold">{results.totalProjects || 1}</p>
                    </div>
                    <Database className="h-8 w-8 text-blue-200" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm">Fresh Processed</p>
                      <p className="text-3xl font-bold">
                        {results.processedCount || (results.data?.from_cache ? 0 : 1)}
                      </p>
                    </div>
                    <RefreshCw className="h-8 w-8 text-green-200" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-yellow-100 text-sm">From Cache</p>
                      <p className="text-3xl font-bold">
                        {results.data?.cachedCount || (results.data?.from_cache ? 1 : 0)}
                      </p>
                    </div>
                    <Database className="h-8 w-8 text-yellow-200" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100 text-sm">POI Highlights</p>
                      <p className="text-3xl font-bold">{results.categories?.poi || results.poiCount || 0}</p>
                    </div>
                    <Building className="h-8 w-8 text-purple-200" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-orange-100 text-sm">Golf & Airports</p>
                      <p className="text-3xl font-bold">
                        {(results.categories?.golf || results.golfCount || 0) +
                          (results.categories?.airports || results.airportCount || 0)}
                      </p>
                    </div>
                    <Plane className="h-8 w-8 text-orange-200" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-teal-500 to-teal-600 text-white border-0 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-teal-100 text-sm">Total Highlights</p>
                      <p className="text-3xl font-bold">{results.highlightsCount || 0}</p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-teal-200" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Failed Projects Alert */}
            {results.data?.failed_projects && results.data.failed_projects.length > 0 && (
              <Card className="border-2 border-red-200 bg-red-50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-700">
                    <AlertCircle className="h-5 w-5" />
                    Failed Projects
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {results.data.failed_projects.map((project: any, index: number) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-red-100 rounded-lg">
                        <div>
                          <span className="font-medium text-red-800">Project ID: {project.project_id}</span>
                          <p className="text-sm text-red-600">{project.error}</p>
                        </div>
                        {project.error.includes("not found") && (
                          <Button
                            size="sm"
                            onClick={() => {
                              setActiveTab("create")
                              setNewProject((prev) => ({ ...prev, project_id: project.project_id }))
                            }}
                            className="bg-red-600 hover:bg-red-700 text-white"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Create
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Enhanced Results Table */}
            <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5" />
                    Location Intelligence Results
                    {results.data?.from_cache && (
                      <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                        <Database className="h-3 w-3 mr-1" />
                        Cached ({results.data.cache_age_days} days old)
                      </Badge>
                    )}
                  </CardTitle>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Filter className="h-4 w-4 text-gray-500" />
                      <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="px-3 py-1 border rounded-md text-sm"
                      >
                        <option value="all">All Categories</option>
                        <option value="poi">POI Only</option>
                        <option value="golf">Golf Courses</option>
                        <option value="airport">Airports</option>
                      </select>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {getFilteredResults().length > 0 ? (
                  <div className="space-y-3">
                    {getFilteredResults().map((highlight: any, index: number) => (
                      <div
                        key={index}
                        className="p-4 border rounded-lg hover:shadow-md transition-all duration-200 hover:bg-gray-50 cursor-pointer"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                                {highlight.project_id}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className={`flex items-center gap-1 ${
                                  highlight.poi_type === "airport"
                                    ? "bg-orange-100 text-orange-700"
                                    : highlight.poi_type === "golf_course"
                                      ? "bg-purple-100 text-purple-700"
                                      : highlight.category === "poi"
                                        ? "bg-green-100 text-green-700"
                                        : "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {getCategoryIcon(highlight.category, highlight.poi_type)}
                                {highlight.poi_type?.replace("_", " ").toUpperCase()}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                Score: {highlight.step1_score}
                              </Badge>
                              {highlight.from_cache && (
                                <Badge
                                  variant="outline"
                                  className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200"
                                >
                                  <Database className="h-3 w-3 mr-1" />
                                  Cached
                                </Badge>
                              )}
                            </div>
                            <h4 className="font-semibold text-gray-900 mb-1">{highlight.name}</h4>
                            <p className="text-gray-600 text-sm mb-2">{highlight.address}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                {highlight.distance_km}km away
                              </span>
                              {highlight.driving_distance && (
                                <span className="flex items-center gap-1">🚗 {highlight.driving_distance} driving</span>
                              )}
                              {highlight.rating && (
                                <span className="flex items-center gap-1">
                                  ⭐ {highlight.rating}/5.0
                                  {highlight.rating_count && ` (${highlight.rating_count} reviews)`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <MapPin className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No highlights found matching your criteria</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
