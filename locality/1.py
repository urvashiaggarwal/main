import googlemaps
import pandas as pd
import time

# Initialize Google Maps API
API_KEY = "AIzaSyAdHgO5Umxxsrwf-PY3xAQSzAcBLNxC9zE"
gmaps = googlemaps.Client(key=API_KEY)

# Load CSV file with localities
df = pd.read_csv("locality.csv")  # Ensure the CSV has a column named 'Locality'

# Function to get Place ID of a locality
def get_place_id(locality):
    try:
        result = gmaps.geocode(locality)
        if result:
            return result[0]['place_id']
    except Exception as e:
        print(f"Error fetching place ID for {locality}: {e}")
    return None

# Function to get places of interest and landmarks
def get_landmarks(place_id):
    places = []
    try:
        response = gmaps.places_nearby(
            location=gmaps.place(place_id=place_id)['result']['geometry']['location'],
            radius=2000,  # Adjust search radius
            type='point_of_interest'  # Can also use 'landmark'
        )
        for place in response.get("results", []):
            places.append({
                "Name": place.get("name"),
                "Place_ID": place.get("place_id"),
                "Latitude": place["geometry"]["location"]["lat"],
                "Longitude": place["geometry"]["location"]["lng"]
            })
    except Exception as e:
        print(f"Error fetching landmarks for {place_id}: {e}")
    return places

# Process each locality
results = []
for locality in df["Locality"]:
    place_id = get_place_id(locality)
   
    print(place_id)
    exit()
    if place_id:
        landmarks = get_landmarks(place_id)
        for landmark in landmarks:
            results.append({
                "Locality": locality,
                **landmark
            })
    time.sleep(1)  # Prevent API rate limits

# Save to CSV
output_df = pd.DataFrame(results)
output_df.to_csv("landmarks_data.csv", index=False)
print("Data saved successfully!")
