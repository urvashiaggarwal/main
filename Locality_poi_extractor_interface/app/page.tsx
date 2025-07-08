"use client"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import SingleLocalityForm from "../components/SingleLocalityForm"
import MultipleLocalityForm from "../components/MultipleLocalityForm"
import CreateLocalityForm from "../components/CreateLocalityForm"

export default function LocalityPOIExtractor() {
  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-2">Locality POI Extractor</h1>
        <p className="text-muted-foreground">
          Extract and manage locality points of interest with auto-fill capabilities
        </p>
      </div>

      <Tabs defaultValue="single" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="single">Single Locality</TabsTrigger>
          <TabsTrigger value="multiple">Multiple via CSV</TabsTrigger>
          <TabsTrigger value="create">Create Locality</TabsTrigger>
        </TabsList>

        <TabsContent value="single" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Single Locality Lookup</CardTitle>
              <CardDescription>Enter a locality ID to auto-fill details from the internal database</CardDescription>
            </CardHeader>
            <CardContent>
              <SingleLocalityForm />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="multiple" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Multiple Localities via CSV</CardTitle>
              <CardDescription>Upload a CSV file with locality IDs to auto-fill details in bulk</CardDescription>
            </CardHeader>
            <CardContent>
              <MultipleLocalityForm />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="create" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Create New Locality</CardTitle>
              <CardDescription>
                Add new localities to the internal database when locality ID doesn't exist
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CreateLocalityForm />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
