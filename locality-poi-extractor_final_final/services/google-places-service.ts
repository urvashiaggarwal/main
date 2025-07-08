export class GooglePlacesService {
  private static API_KEY = process.env.GOOGLE_PLACES_API_KEY

  static async getMpList(locality: string, city: string): Promise<string> {
    if (!this.API_KEY) {
      console.error("Google Places API key not configured")
      return "error"
    }

    try {
      const query = `${locality} ${city}`
      const url = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${encodeURIComponent(query)}&key=${this.API_KEY}`

      const response = await fetch(url)
      const data = await response.json()

      if (data.status === "OK" && data.results && data.results.length > 0) {
        const places = data.results

        if (places.length === 1) {
          return `${places[0].name}, ${locality}`
        } else {
          // Look for a place with "locality" in types
          for (const place of places) {
            if (place.types && place.types.includes("locality")) {
              return `${place.name}, ${locality}`
            }
          }
          // If no locality type found, return the first result
          return `${places[0].name}, ${locality}`
        }
      } else {
        console.error("Google Places API error:", data.status)
        return "error"
      }
    } catch (error) {
      console.error("Error calling Google Places API:", error)
      return "error"
    }
  }
}
