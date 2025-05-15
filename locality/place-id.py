
import requests 
import json, csv
import math, gmaps
import pandas as pd

# Function to calculate the Haversine distance between two points on the Earth
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance

api_key = 'AIzaSyAdHgO5Umxxsrwf-PY3xAQSzAcBLNxC9zE'

# Function to fetch place details based on place_id
def get_place_details(place_id):
    details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews,user_ratings_total&key={api_key}'
    
    response = requests.get(details_url)
    if response.status_code == 200:
        details = response.json()
        if 'result' in details:
            return details['result']
        else:
            print(f"Error fetching details for Place ID: {place_id}")
            return None
    else:
        print(f"Error: Unable to fetch details for Place ID {place_id} (Status code {response.status_code})")
        return None


    
# Open the CSV file with latitudes and longitudes
with open('orignal-lat-long.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    next(reader, None)  # Skip header if it exists
    
    for row in reader:
        xid = row[0]
        string = row[1] + ',' + row[4] + ',' + row[2]  # Search term (address or location)
        print(string)
        
        my_lat = float(row[6])  # Latitude
        my_lng = float(row[7])  # Longitude
        url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query={string}&key={api_key}'

        # Making a GET request for JSON data
        response = requests.get(url)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()
            table_data = []
            locations = []

            for restaurant in data['results']:
                name = restaurant['name']
                lat = restaurant['geometry']['location']['lat']
                lng = restaurant['geometry']['location']['lng']
                place_id = restaurant['place_id']  # Extract place_id
                distance = haversine(my_lat, my_lng, lat, lng)
                
                # Only consider locations within 1 km
                if distance <= 1.0:
                    locations.append({
                        'xid': xid,
                        'search': string,
                        'name': name,
                        'latitude': lat,
                        'longitude': lng,
                        'place_id': place_id,
                        'distance_km': distance  # Store the place_id as well
                    })
                    #print(locations)

            if locations:  # Only proceed if there are locations within 1 km
                # Fetch additional details for each location within 1 km
                for loc in locations:
                     
                    place_details = get_place_details(loc['place_id'])
                    if place_details:
                        loc.update({
                            'user_ratings_total': place_details.get('user_ratings_total', 'N/A')
                        })
                        
                        # Print each restaurant details including extra information
                        print(f"Restaurant Name: {loc['name']}")
                        print(f"Latitude: {loc['latitude']}, Longitude: {loc['longitude']}")
                        print(f"Place ID: {loc['place_id']}, Distance: {loc['distance_km']:.2f} km")
                        print(f"User Ratings Total: {loc['user_ratings_total']}")

                        # Add the location to table_data
                        table_data.append(loc)

                # Create DataFrame and save to CSV (append mode)
                df = pd.DataFrame(table_data)
                df.to_csv('closest-place_id-total_ratings.csv', mode='a', header=False, index=False)

                # Print the final URL
                print(f"Request URL: {response.url}")
              
            else:
                print(f"No locations found within 1 km for search: {string}")
        else:
            print(f"Error: Unable to fetch data (Status code {response.status_code})")

print('done')
