import sys
import json
import csv
import argparse
import mysql.connector
from mysql.connector import Error
import os
import math
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import googlemaps

class IntegratedLocationProcessor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'location_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        self.connection = None
        self.gmaps_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        if self.gmaps_key:
            self.gmaps = googlemaps.Client(key=self.gmaps_key)
        else:
            self.gmaps = None
        
        # POI categories from the original script
        self.poi_categories = [
            'school', 'hospital', 'shopping_mall', 'market', 'park',
            'metro_station', 'hotel', 'railway_station', 'college', 'tourist_attraction'
        ]
        
        # Search parameters
        self.poi_radius_km = 15.0
        self.airport_radius_km = 40.0
        self.golf_radius_km = 15.0

    def connect_to_database(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}", file=sys.stderr)
            return False
        return False

    def close_connection(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def safe_float(self, value) -> float:
        """Safely convert value to native Python float"""
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def safe_int(self, value) -> int:
        """Safely convert value to native Python int"""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate the great circle distance between two points on Earth in kilometers"""
        R = 6371  # Radius of Earth in kilometers
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lng2 - lng1)

        a = math.sin(delta_phi / 2.0)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_distance_matrix_in_batches(self, origin: Tuple[float, float], destinations: List[Tuple[float, float]], batch_size: int = 25) -> List[str]:
        """Get driving distances using Google Maps API in batches"""
        if not self.gmaps:
            # Fallback to circular distance if no API key
            return [f"{self.haversine_distance(origin[0], origin[1], dest[0], dest[1]):.1f}" for dest in destinations]
        
        distances = []
        for i in range(0, len(destinations), batch_size):
            batch = destinations[i:i + batch_size]
            try:
                result = self.gmaps.distance_matrix(
                    origins=[origin],
                    destinations=batch,
                    mode='driving',
                    units='metric'
                )
                for j, element in enumerate(result['rows'][0]['elements']):
                    if element['status'] == 'OK':
                        # Extract numeric value from distance text (e.g., "7.2 km" -> "7.2")
                        distance_text = element['distance']['text']
                        distance_value = distance_text.replace(' km', '').replace(',', '')
                        distances.append(distance_value)
                    else:
                        # Fallback to circular distance
                        if j < len(batch):
                            dest = batch[j]
                            circular_dist = self.haversine_distance(origin[0], origin[1], dest[0], dest[1])
                            distances.append(f"{circular_dist:.1f}")
                        else:
                            distances.append('0')
            except Exception as e:
                print(f"Error in batch {i}-{i+batch_size}: {e}", file=sys.stderr)
                # Fallback to circular distances for this batch
                for dest in batch:
                    circular_dist = self.haversine_distance(origin[0], origin[1], dest[0], dest[1])
                    distances.append(f"{circular_dist:.1f}")
            
            time.sleep(0.1)  # Avoid rate-limiting
        
        return distances

    def get_project_data(self, project_id: str) -> Dict[str, Any]:
        """Get project information from projects table using actual schema"""
        if not self.connection:
            return {}

        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT project_id, project_name, latitude, longitude, city
            FROM projects 
            WHERE project_id = %s
            """
            cursor.execute(query, (project_id,))
            result = cursor.fetchone()
            cursor.close()
            return result or {}
        except Error as e:
            print(f"Error fetching project data: {e}", file=sys.stderr)
            return {}

    def check_existing_highlights(self, project_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check if highlights exist and are less than 2 months old"""
        if not self.connection:
            return False, []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Check for existing highlights within 2 months
            query = """
            SELECT *, 
                   DATEDIFF(NOW(), created_at) as days_old
            FROM location_highlights
            WHERE project_id = %s 
            AND created_at >= DATE_SUB(NOW(), INTERVAL 2 MONTH)
            ORDER BY step1_score DESC
            """
            
            cursor.execute(query, (project_id,))
            results = cursor.fetchall()
            cursor.close()
            
            if results:
                # Format results to match expected output structure
                formatted_results = []
                for result in results:
                    formatted_result = {
                        'project_id': result['project_id'],
                        'poi_type': result['poi_type'],
                        'name': result['name'],
                        'address': result.get('address', ''),
                        'distance_km': self.safe_float(result['distance_km']),
                        'step1_score': self.safe_float(result['step1_score']),
                        'rating': self.safe_float(result['rating']) if result.get('rating') else None,
                        'rating_count': self.safe_int(result.get('rating_count')),
                        'driving_distance': result.get('driving_distance', ''),
                        'lat': self.safe_float(result['lat']) if result.get('lat') else None,
                        'lng': self.safe_float(result['lng']) if result.get('lng') else None,
                        'priority': result['priority'],
                        'category': result['category'],
                        'created_at': result['created_at'],
                        'days_old': self.safe_int(result['days_old']),
                        'from_cache': True
                    }
                    formatted_results.append(formatted_result)
                
                return True, formatted_results
            
            return False, []
            
        except Error as e:
            print(f"Error checking existing highlights: {e}", file=sys.stderr)
            return False, []

    def get_surrounding_pois_by_category(self, project_lat: float, project_lng: float, poi_category: str, radius_km: float = None) -> List[Dict[str, Any]]:
        """Get POIs of specific category within radius using actual schema"""
        if not self.connection:
            return []

        if radius_km is None:
            radius_km = self.poi_radius_km

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Using bounding box for initial filtering
            lat_range = radius_km / 111.0
            lng_range = radius_km / (111.0 * math.cos(math.radians(project_lat)))
            
            query = """
            SELECT *,
                   (6371 * acos(cos(radians(%s)) * cos(radians(lat)) * 
                   cos(radians(lng) - radians(%s)) + sin(radians(%s)) * 
                   sin(radians(lat)))) AS circular_distance_km
            FROM poi_extractions_surrounding
            WHERE poi_type = %s
            AND lat BETWEEN %s AND %s
            AND lng BETWEEN %s AND %s
            HAVING circular_distance_km <= %s
            ORDER BY circular_distance_km ASC
            LIMIT 50
            """
            
            cursor.execute(query, (
                project_lat, project_lng, project_lat,
                poi_category,
                project_lat - lat_range, project_lat + lat_range,
                project_lng - lng_range, project_lng + lng_range,
                radius_km
            ))
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Error as e:
            print(f"Error fetching POI data for {poi_category}: {e}", file=sys.stderr)
            return []

    def get_nearby_airports(self, project_lat: float, project_lng: float, radius_km: float = None) -> List[Dict[str, Any]]:
        """Get airports within specified radius using actual schema"""
        if not self.connection:
            return []

        if radius_km is None:
            radius_km = self.airport_radius_km

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            lat_range = radius_km / 111.0
            lng_range = radius_km / (111.0 * math.cos(math.radians(project_lat)))
            
            query = """
            SELECT *,
                   (6371 * acos(cos(radians(%s)) * cos(radians(latitude_deg)) * 
                   cos(radians(longitude_deg) - radians(%s)) + sin(radians(%s)) * 
                   sin(radians(latitude_deg)))) AS circular_distance_km
            FROM airports
            WHERE latitude_deg BETWEEN %s AND %s
            AND longitude_deg BETWEEN %s AND %s
            HAVING circular_distance_km <= %s
            ORDER BY circular_distance_km ASC
            LIMIT 10
            """
            
            cursor.execute(query, (
                project_lat, project_lng, project_lat,
                project_lat - lat_range, project_lat + lat_range,
                project_lng - lng_range, project_lng + lng_range,
                radius_km
            ))
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Error as e:
            print(f"Error fetching airport data: {e}", file=sys.stderr)
            return []

    def get_nearby_golf_courses(self, project_lat: float, project_lng: float, radius_km: float = None) -> List[Dict[str, Any]]:
        """Get nearby golf courses using Google Places API"""
        if not self.gmaps:
            return []
        
        if radius_km is None:
            radius_km = self.golf_radius_km
            
        radius_meters = int(radius_km * 1000)
        
        try:
            search_result = self.gmaps.places(
                query="golf course",
                location=(project_lat, project_lng),
                radius=radius_meters,
            )
            
            golf_courses = []
            if search_result and 'results' in search_result:
                for place in search_result['results']:
                    if 'golf' in place.get('name', '').lower():
                        golf_info = {
                            'name': place.get('name'),
                            'address': place.get('formatted_address') or place.get('vicinity'),
                            'types': ', '.join(place.get('types', [])),
                            'rating': self.safe_float(place.get('rating', 0)),
                            'rating_count': self.safe_int(place.get('user_ratings_total', 0)),
                            'place_id': place.get('place_id'),
                            'lat': self.safe_float(place.get('geometry', {}).get('location', {}).get('lat')),
                            'lng': self.safe_float(place.get('geometry', {}).get('location', {}).get('lng'))
                        }
                        golf_courses.append(golf_info)
            
            return golf_courses
            
        except Exception as e:
            print(f"Error fetching golf courses: {e}", file=sys.stderr)
            return []

    def compute_poi_scores(self, pois: List[Dict[str, Any]], project_coords: Tuple[float, float], poi_type: str = None, alpha: float = 0.7) -> List[Dict[str, Any]]:
        """Compute POI scores based on rating, rating_count, and driving distance"""
        if not pois:
            return []

        # Get driving distances
        destinations = [(self.safe_float(poi['lat']), self.safe_float(poi['lng'])) for poi in pois]
        driving_distances = self.get_distance_matrix_in_batches(project_coords, destinations)
        
        scored_pois = []
        for i, poi in enumerate(pois):
            # Clean distance data
            distance_str = driving_distances[i] if i < len(driving_distances) else "0"
            distance_km = self.safe_float(distance_str)
            
            # Skip if too far
            if distance_km > 15:
                continue
            
            # Clean rating data
            rating = self.safe_float(poi.get('rating', 0))
            rating_count = self.safe_int(poi.get('rating_count', 0))
            
            # Compute scores using the original algorithm
            rating_score = rating * pow(rating_count + 1, alpha)
            distance_score = 1 / (1 + distance_km)
            step1_score = rating_score * distance_score
            
            # Apply POI-type-specific adjustments
            if poi_type == 'hospital':
                big_hospitals = ['max', 'fortis', 'apollo', 'medanta', 'blk']
                name_lower = poi.get('name', '').lower()
                if any(bh in name_lower for bh in big_hospitals):
                    step1_score *= 3
            elif poi_type == 'hotel':
                if '5-star' in poi.get('primary_type', '').lower():
                    step1_score *= 1.5
            
            # Add computed scores to POI data
            poi_copy = poi.copy()
            poi_copy.update({
                'driving_distance': distance_str,
                'distance_km': distance_km,
                'rating_score': rating_score,
                'distance_score': distance_score,
                'step1_score': step1_score
            })
            
            scored_pois.append(poi_copy)
        
        # Sort by score
        if poi_type == 'metro_station':
            scored_pois.sort(key=lambda x: x['distance_score'], reverse=True)
        else:
            scored_pois.sort(key=lambda x: x['step1_score'], reverse=True)
        
        return scored_pois

    def compute_golf_scores(self, golf_courses: List[Dict[str, Any]], project_coords: Tuple[float, float]) -> List[Dict[str, Any]]:
        """Compute golf course scores"""
        if not golf_courses:
            return []

        destinations = [(self.safe_float(gc['lat']), self.safe_float(gc['lng'])) for gc in golf_courses]
        driving_distances = self.get_distance_matrix_in_batches(project_coords, destinations)
        
        scored_golf = []
        for i, gc in enumerate(golf_courses):
            distance_str = driving_distances[i] if i < len(driving_distances) else "0"
            distance_km = self.safe_float(distance_str)
            
            rating = self.safe_float(gc.get('rating', 0))
            rating_count = self.safe_int(gc.get('rating_count', 0))
            
            # Golf course scoring from original script
            score = rating * math.log(rating_count + 1)
            
            gc_copy = gc.copy()
            gc_copy.update({
                'driving_distance': distance_str,
                'distance_km': distance_km,
                'golf_score': score
            })
            
            scored_golf.append(gc_copy)
        
        scored_golf.sort(key=lambda x: x['distance_km'])
        return scored_golf

    def save_highlights_to_db(self, highlights: List[Dict[str, Any]]) -> bool:
        """Save generated highlights to database using actual schema with proper type conversion"""
        if not self.connection or not highlights:
            return False

        try:
            cursor = self.connection.cursor()
            
            # Clear existing highlights for this project
            project_id = highlights[0]['project_id']
            delete_query = "DELETE FROM location_highlights WHERE project_id = %s"
            cursor.execute(delete_query, (project_id,))
            
            # Insert new highlights
            insert_query = """
            INSERT INTO location_highlights 
            (project_id, poi_type, name, address, distance_km, step1_score, rating, rating_count, 
             driving_distance, lat, lng, priority, category, from_cache)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for highlight in highlights:
                # Convert all values to native Python types to avoid MySQL conversion errors
                cursor.execute(insert_query, (
                    str(highlight['project_id']),
                    str(highlight['poi_type']),
                    str(highlight['name']),
                    str(highlight.get('address', '')),
                    self.safe_float(highlight.get('distance_km', 0)),
                    self.safe_float(highlight.get('step1_score', 0)),
                    self.safe_float(highlight.get('rating')) if highlight.get('rating') is not None else None,
                    self.safe_int(highlight.get('rating_count')) if highlight.get('rating_count') is not None else None,
                    str(highlight.get('driving_distance', '')),
                    self.safe_float(highlight.get('lat')) if highlight.get('lat') is not None else None,
                    self.safe_float(highlight.get('lng')) if highlight.get('lng') is not None else None,
                    str(highlight.get('priority', 'medium')),
                    str(highlight.get('category', 'poi')),
                    False  # from_cache = False for new highlights
                ))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            print(f"Error saving highlights to database: {e}", file=sys.stderr)
            return False

    def process_single_project(self, project_id: str) -> Dict[str, Any]:
        """Process a single project with caching logic"""
        if not self.connect_to_database():
            return {"error": "Database connection failed"}

        try:
            # Get project data using actual schema
            project_data = self.get_project_data(project_id)
            if not project_data:
                return {"error": f"Project {project_id} not found"}

            # Check if recent highlights exist (≤ 2 months)
            has_recent_highlights, cached_highlights = self.check_existing_highlights(project_id)
        
            if has_recent_highlights:
                print(f"Using cached highlights for project {project_id} (age: {cached_highlights[0]['days_old']} days)", file=sys.stderr)
            
                result = {
                    "project_id": project_id,
                    "project_name": project_data['project_name'],
                    "project_location": {
                        "lat": self.safe_float(project_data['latitude']),
                        "lng": self.safe_float(project_data['longitude'])
                    },
                    "highlights": cached_highlights,
                    "total_highlights": len(cached_highlights),
                    "poi_count": len([h for h in cached_highlights if h['category'] == 'poi']),
                    "golf_count": len([h for h in cached_highlights if h['poi_type'] == 'golf_course']),
                    "airport_count": len([h for h in cached_highlights if h['poi_type'] == 'airport']),
                    "from_cache": True,
                    "cache_age_days": cached_highlights[0]['days_old'] if cached_highlights else 0,
                    "processed_at": datetime.now().isoformat()
                }
            
                return result
        
            # If no recent highlights, process fresh
            print(f"Processing fresh highlights for project {project_id}", file=sys.stderr)
            
            project_lat = self.safe_float(project_data['latitude'])
            project_lng = self.safe_float(project_data['longitude'])
            project_coords = (project_lat, project_lng)
            
            all_highlights = []
            
            # Process each POI category
            for poi_category in self.poi_categories:
                pois = self.get_surrounding_pois_by_category(project_lat, project_lng, poi_category)
                if pois:
                    scored_pois = self.compute_poi_scores(pois, project_coords, poi_category)
                    
                    # Take top POI from each category
                    if scored_pois:
                        top_poi = scored_pois[0]
                        
                        highlight = {
                            'project_id': project_data['project_id'],
                            'poi_type': poi_category,
                            'name': top_poi.get('name', f'Top {poi_category.replace("_", " ").title()}'),
                            'address': top_poi.get('address', ''),
                            'distance_km': self.safe_float(top_poi.get('distance_km', 0)),
                            'step1_score': round(self.safe_float(top_poi.get('step1_score', 0)), 6),
                            'rating': self.safe_float(top_poi.get('rating')) if top_poi.get('rating') else None,
                            'rating_count': self.safe_int(top_poi.get('rating_count')) if top_poi.get('rating_count') else None,
                            'driving_distance': str(top_poi.get('driving_distance', '')),
                            'lat': self.safe_float(top_poi.get('lat')),
                            'lng': self.safe_float(top_poi.get('lng')),
                            'priority': 'high' if poi_category in ['hospital', 'metro_station'] else 'medium',
                            'category': 'poi',
                            'from_cache': False
                        }
                        
                        all_highlights.append(highlight)
            
            # Process golf courses
            golf_courses = self.get_nearby_golf_courses(project_lat, project_lng)
            if golf_courses:
                scored_golf = self.compute_golf_scores(golf_courses, project_coords)
                
                # Take top 2 golf courses
                for golf in scored_golf[:2]:
                    highlight = {
                        'project_id': project_data['project_id'],
                        'poi_type': 'golf_course',
                        'name': golf.get('name', 'Golf Course'),
                        'address': golf.get('address', ''),
                        'distance_km': self.safe_float(golf.get('distance_km', 0)),
                        'step1_score': round(self.safe_float(golf.get('golf_score', 0)), 6),
                        'rating': self.safe_float(golf.get('rating')) if golf.get('rating') else None,
                        'rating_count': self.safe_int(golf.get('rating_count')) if golf.get('rating_count') else None,
                        'driving_distance': str(golf.get('driving_distance', '')),
                        'lat': self.safe_float(golf.get('lat')),
                        'lng': self.safe_float(golf.get('lng')),
                        'priority': 'medium',
                        'category': 'recreation',
                        'from_cache': False
                    }
                    
                    all_highlights.append(highlight)
            
            # Process airports
            airports = self.get_nearby_airports(project_lat, project_lng)
            if airports:
                # Get driving distances for airports
                airport_destinations = [(self.safe_float(airport['latitude_deg']), self.safe_float(airport['longitude_deg'])) for airport in airports]
                airport_distances = self.get_distance_matrix_in_batches(project_coords, airport_destinations)
                
                # Take top 2 airports
                for i, airport in enumerate(airports[:2]):
                    distance_str = airport_distances[i] if i < len(airport_distances) else "0"
                    distance_km = self.safe_float(distance_str)
                    
                    highlight = {
                        'project_id': project_data['project_id'],
                        'poi_type': 'airport',
                        'name': airport.get('name', 'Airport'),
                        'address': airport.get('address', ''),
                        'distance_km': distance_km,
                        'step1_score': self.safe_float(airport.get('score', 50.0)),
                        'rating': None,
                        'rating_count': None,
                        'driving_distance': str(distance_str),
                        'lat': self.safe_float(airport.get('latitude_deg')),
                        'lng': self.safe_float(airport.get('longitude_deg')),
                        'priority': 'high' if airport.get('type') == 'large_airport' else 'medium',
                        'category': 'transportation',
                        'from_cache': False
                    }
                    
                    all_highlights.append(highlight)
            
            # Sort all highlights by step1_score
            all_highlights.sort(key=lambda x: x['step1_score'], reverse=True)
            
            # Save to database
            self.save_highlights_to_db(all_highlights)

            result = {
                "project_id": project_id,
                "project_name": project_data['project_name'],
                "project_location": {
                    "lat": self.safe_float(project_data['latitude']),
                    "lng": self.safe_float(project_data['longitude'])
                },
                "highlights": all_highlights,
                "total_highlights": len(all_highlights),
                "poi_count": len([h for h in all_highlights if h['category'] == 'poi']),
                "golf_count": len([h for h in all_highlights if h['poi_type'] == 'golf_course']),
                "airport_count": len([h for h in all_highlights if h['poi_type'] == 'airport']),
                "from_cache": False,
                "processed_at": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            return {"error": f"Error processing project: {str(e)}"}

        finally:
            self.close_connection()

    def process_multiple_projects(self, csv_file_path: str) -> Dict[str, Any]:
        """Process multiple project IDs with caching logic"""
        if not self.connect_to_database():
            return {"error": "Database connection failed"}

        try:
            project_ids = []
        
            # Read project IDs from CSV
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                first_row = next(reader, None)
                if first_row and not first_row[0].startswith('PROJ') and not first_row[0].isdigit():
                    pass  # Skip header
                else:
                    if first_row:
                        project_ids.append(first_row[0].strip())
            
                for row in reader:
                    if row and row[0].strip():
                        project_ids.append(row[0].strip())

            all_highlights = []
            processed_projects = []
            failed_projects = []
            cached_projects = []

            # Process each project ID
            for project_id in project_ids:
                try:
                    result = self.process_single_project(project_id)
                    if "error" not in result:
                        all_highlights.extend(result['highlights'])
                    
                        project_summary = {
                            'project_id': project_id,
                            'project_name': result['project_name'],
                            'highlights_count': result['total_highlights'],
                            'poi_count': result['poi_count'],
                            'golf_count': result['golf_count'],
                            'airport_count': result['airport_count'],
                            'from_cache': result.get('from_cache', False)
                        }
                    
                        if result.get('from_cache'):
                            project_summary['cache_age_days'] = result.get('cache_age_days', 0)
                            cached_projects.append(project_summary)
                        else:
                            processed_projects.append(project_summary)
                    else:
                        failed_projects.append({
                            'project_id': project_id,
                            'error': result['error']
                        })
                except Exception as e:
                    failed_projects.append({
                        'project_id': project_id,
                        'error': str(e)
                    })

            # Sort all highlights by step1_score
            all_highlights.sort(key=lambda x: x['step1_score'], reverse=True)

            result = {
                "totalProjects": len(project_ids),
                "processedCount": len(processed_projects),
                "cachedCount": len(cached_projects),
                "failedCount": len(failed_projects),
                "totalHighlights": len(all_highlights),
                "highlights": all_highlights,
                "preview": all_highlights[:10],
                "processed_projects": processed_projects,
                "cached_projects": cached_projects,
                "failed_projects": failed_projects,
                "processed_at": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            return {"error": f"Error processing CSV: {str(e)}"}

        finally:
            self.close_connection()

def main():
    parser = argparse.ArgumentParser(description='Integrated location highlights processor with advanced scoring')
    parser.add_argument('--single', type=str, help='Single project ID to process')
    parser.add_argument('--multiple', type=str, help='CSV file path with multiple project IDs')
    
    args = parser.parse_args()
    
    processor = IntegratedLocationProcessor()
    
    try:
        if args.single:
            result = processor.process_single_project(args.single)
        elif args.multiple:
            result = processor.process_multiple_projects(args.multiple)
        else:
            result = {"error": "Please provide either --single or --multiple argument"}
        
        # Ensure clean JSON output
        print(json.dumps(result, default=str, ensure_ascii=False))
        
    except Exception as e:
        error_result = {"error": f"Script execution error: {str(e)}"}
        print(json.dumps(error_result, default=str))

if __name__ == "__main__":
    main()
