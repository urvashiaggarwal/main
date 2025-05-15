import googlemaps
import pandas as pd
import time
from shapely.geometry import Point, Polygon

# Initialize Google Maps API
API_KEY = "AIzaSyAdHgO5Umxxsrwf-PY3xAQSzAcBLNxC9zE"
gmaps = googlemaps.Client(key=API_KEY)

# Load CSV file with localities
df = pd.read_csv("locality.csv")  # Ensure the CSV has a column named 'Locality'

# Function to get boundary coordinates (polygon) of a locality
def get_boundary_coordinates(locality):
    try:
        result = gmaps.geocode(locality)
        if result:
            location = result[0]['geometry']['location']
            place_id = result[0]['place_id']
            details = gmaps.place(place_id=place_id)
            
            # Extract bounds from geometry (if available)
            bounds = details["result"]["geometry"].get("viewport")
            if bounds:
                northeast = bounds["northeast"]
                southwest = bounds["southwest"]
                polygon_coords = [
                    (southwest["lng"], southwest["lat"]),
                    (northeast["lng"], southwest["lat"]),
                    (northeast["lng"], northeast["lat"]),
                    (southwest["lng"], northeast["lat"]),
                    (southwest["lng"], southwest["lat"])  # Closing the polygon
                ]
                return polygon_coords
    except Exception as e:
        print(f"Error fetching boundary for {locality}: {e}")
    return None

# Function to get places of interest
def get_landmarks(bounds_polygon):
    places = []
    try:
        response = gmaps.places_nearby(
            location=(bounds_polygon[0][1], bounds_polygon[0][0]),  # Center of polygon
            radius=2000,  # Wide search, filter later
            type="point_of_interest"
        )
        
        for place in response.get("results", []):
            lat = place["geometry"]["location"]["lat"]
            lng = place["geometry"]["location"]["lng"]
            point = Point(lng, lat)
            
            # Check if the place is inside the polygon
            if Polygon(bounds_polygon).contains(point):
                places.append({
                    "Name": place.get("name"),
                    "Place_ID": place.get("place_id"),
                    "Latitude": lat,
                    "Longitude": lng
                })
    except Exception as e:
        print(f"Error fetching landmarks: {e}")
    return places

# Process each locality
results = []
for locality in df["Locality"]:
    boundary_coords = get_boundary_coordinates(locality)
    if boundary_coords:
        landmarks = get_landmarks(boundary_coords)
        for landmark in landmarks:
            results.append({
                "Locality": locality,
                **landmark
            })
    time.sleep(1)  # Prevent API rate limits

# Save to CSV
output_df = pd.DataFrame(results)
output_df.to_csv("landmarks_within_boundary.csv", index=False)
print("Data saved successfully!")
