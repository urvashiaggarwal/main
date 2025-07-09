-- Insert enhanced sample data for testing

USE location_db;

-- Insert sample projects with coordinates
INSERT INTO projects (project_id, name, lat, lng, timestamp, status, description) VALUES
('PROJ-12345', 'Downtown Development Hub', 40.7128, -74.0060, '2024-01-15 10:30:00', 'active', 'Major urban development project in Manhattan'),
('PROJ-67890', 'Coastal Resort Paradise', 25.7617, -80.1918, '2024-02-01 14:20:00', 'active', 'Luxury beachfront resort in Miami'),
('PROJ-11111', 'Mountain Lodge Retreat', 39.7392, -104.9903, '2024-01-20 09:15:00', 'completed', 'Eco-friendly mountain lodge in Denver area'),
('PROJ-22222', 'Central Park Renovation', 40.7829, -73.9654, '2024-03-01 11:45:00', 'active', 'Historic park restoration project'),
('PROJ-33333', 'Tech Campus Complex', 37.7749, -122.4194, '2024-02-15 16:30:00', 'active', 'Modern technology campus in San Francisco');

-- Insert sample POI extractions
INSERT INTO poi_extractions_surrounding (locality_id, locality_name, city, poi_type, name, place_id, primary_type, types, api_primary_type, address, rating, rating_count, lat, lng, google_map_url, business_status, wheelchair_accessible, website, summary, extraction_date) VALUES
('LOC001', 'Manhattan Financial District', 'New York', 'restaurant', 'Stone Street Tavern', 'ChIJd8BlQ2BZwokRAFUEcm_qrcA', 'restaurant', 'restaurant,bar,establishment,food,point_of_interest', 'restaurant', '52 Stone St, New York, NY 10004', 4.2, 1250, 40.7041, -74.0124, 'https://maps.google.com/?cid=123456789', 'OPERATIONAL', true, 'https://stonest-tavern.com', 'Historic tavern in financial district', '2024-01-10'),
('LOC001', 'Manhattan Financial District', 'New York', 'hospital', 'NewYork-Presbyterian Lower Manhattan Hospital', 'ChIJVVVVVVVVwokRBBBBBBBBBBB', 'hospital', 'hospital,health,establishment,point_of_interest', 'hospital', '170 William St, New York, NY 10038', 3.8, 890, 40.7089, -74.0052, 'https://maps.google.com/?cid=987654321', 'OPERATIONAL', true, 'https://nyp.org', 'Major hospital serving lower Manhattan', '2024-01-10'),
('LOC002', 'Miami Beach', 'Miami', 'tourist_attraction', 'South Beach', 'ChIJEQEQEQEQEQEQEQEQEQEQEQ', 'tourist_attraction', 'tourist_attraction,establishment,point_of_interest', 'tourist_attraction', 'South Beach, Miami Beach, FL', 4.5, 15420, 25.7814, -80.1300, 'https://maps.google.com/?cid=111222333', 'OPERATIONAL', true, null, 'Famous beach destination with art deco architecture', '2024-02-01'),
('LOC003', 'Denver Metro', 'Denver', 'gas_station', 'Shell Gas Station', 'ChIJRRRRRRRRRRRRRRRRRRRRRR', 'gas_station', 'gas_station,establishment,point_of_interest', 'gas_station', '1234 Colorado Blvd, Denver, CO 80220', 3.9, 245, 39.7391, -104.9847, 'https://maps.google.com/?cid=444555666', 'OPERATIONAL', true, 'https://shell.com', 'Convenient fuel station with amenities', '2024-01-20'),
('LOC004', 'Central Park Area', 'New York', 'park', 'Central Park Conservatory Garden', 'ChIJSSSSSSSSSSSSSSSSSSSSS', 'park', 'park,establishment,point_of_interest,tourist_attraction', 'park', '105th St &, 5th Ave, New York, NY 10029', 4.6, 3200, 40.7947, -73.9537, 'https://maps.google.com/?cid=777888999', 'OPERATIONAL', true, 'https://centralparknyc.org', 'Beautiful formal garden within Central Park', '2024-03-01'),
('LOC005', 'San Francisco SOMA', 'San Francisco', 'subway_station', 'Montgomery St BART Station', 'ChIJTTTTTTTTTTTTTTTTTTTTTT', 'transit_station', 'subway_station,transit_station,establishment,point_of_interest', 'transit_station', '598 Market St, San Francisco, CA 94104', 3.7, 1890, 37.7894, -122.4013, 'https://maps.google.com/?cid=101112131', 'OPERATIONAL', true, 'https://bart.gov', 'Major BART station in downtown SF', '2024-02-15');

-- Insert sample airports
INSERT INTO airports (ident, type, name, address, latitude_deg, longitude_deg, continent, iso_country, iso_region, municipality, gps_code, iata_code, home_link, wikipedia_link, keywords, score) VALUES
('KJFK', 'large_airport', 'John F Kennedy International Airport', 'Queens, NY 11430, USA', 40.6413, -73.7781, 'NA', 'US', 'US-NY', 'New York', 'KJFK', 'JFK', 'https://www.jfkairport.com/', 'https://en.wikipedia.org/wiki/John_F._Kennedy_International_Airport', 'JFK,Kennedy,International,New York', 95.5),
('KMIA', 'large_airport', 'Miami International Airport', '2100 NW 42nd Ave, Miami, FL 33126, USA', 25.7932, -80.2906, 'NA', 'US', 'US-FL', 'Miami', 'KMIA', 'MIA', 'https://www.miami-airport.com/', 'https://en.wikipedia.org/wiki/Miami_International_Airport', 'Miami,International,MIA', 92.3),
('KDEN', 'large_airport', 'Denver International Airport', '8500 Peña Blvd, Denver, CO 80249, USA', 39.8617, -104.6731, 'NA', 'US', 'US-CO', 'Denver', 'KDEN', 'DEN', 'https://www.flydenver.com/', 'https://en.wikipedia.org/wiki/Denver_International_Airport', 'Denver,International,DEN', 94.1),
('KLGA', 'medium_airport', 'LaGuardia Airport', 'East Elmhurst, NY 11371, USA', 40.7769, -73.8740, 'NA', 'US', 'US-NY', 'New York', 'KLGA', 'LGA', 'https://www.laguardiaairport.com/', 'https://en.wikipedia.org/wiki/LaGuardia_Airport', 'LaGuardia,LGA,New York', 88.7),
('KSFO', 'large_airport', 'San Francisco International Airport', 'San Francisco, CA 94128, USA', 37.6213, -122.3790, 'NA', 'US', 'US-CA', 'San Francisco', 'KSFO', 'SFO', 'https://www.flysfo.com/', 'https://en.wikipedia.org/wiki/San_Francisco_International_Airport', 'San Francisco,International,SFO', 96.2);
