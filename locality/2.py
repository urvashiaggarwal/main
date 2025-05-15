import requests

api_key = "AIzaSyAdHgO5Umxxsrwf-PY3xAQSzAcBLNxC9zE"
locality = "Noida"  # Replace with your locality
url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={locality}&key={api_key}"

response = requests.get(url)
data=response.json()
print(data)
if response.status_code == 200:
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        place = data["results"][0]
        print(f"Locality Name: {place['name']}")
        print(f"Place ID: {place['place_id']}")
        print(f"Latitude: {place['geometry']['location']['lat']}")
        print(f"Longitude: {place['geometry']['location']['lng']}")
    else:
        print("❌ No results found!")
else:
    print("❌ Error fetching data!")
