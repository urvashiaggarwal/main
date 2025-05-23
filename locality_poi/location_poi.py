import requests
import pandas as pd

# Google Maps API Key
API_KEY = "AIzaSyD4muQalGhg3waN48avO3PqHpliWppT-TI"

locality = "Noida Sector 18"

# Function to get Place ID of a locality
def get_place_id(locality):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={locality}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        place_id = data["results"][0]["place_id"]
        location = data["results"][0]["geometry"]["location"]
        return place_id, location["lat"], location["lng"]
    else:
        print(f"Error fetching Place ID for {locality}: {data['status']}")
        return None, None, None

# Function to get places of interest and landmarks
def get_landmarks(lat, lng, radius=2000):
    places = []
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=point_of_interest&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        for place in data["results"]:
            places.append({
                "Name": place.get("name"),
                "Place_ID": place.get("place_id"),
                "Latitude": place["geometry"]["location"]["lat"],
                "Longitude": place["geometry"]["location"]["lng"]
            })
    else:
        print(f"Error fetching landmarks: {data['status']}")
    
    return places

# Get Place ID for the locality
place_id, lat, lng = get_place_id(locality)

if place_id:
    print(f" Place ID for '{locality}': {place_id}")
    print(f" Coordinates: Latitude {lat}, Longitude {lng}")

    landmarks = get_landmarks(lat, lng)

    df = pd.DataFrame(landmarks)
    print("\n Nearby Landmarks & Points of Interest:")
    print(df)

    # Save to CSV
    df.to_csv(f"{locality.replace(' ', '_')}_landmarks.csv", index=False)
    print("\nData saved successfully!")

else:
    print("Could not retrieve Place ID.")
