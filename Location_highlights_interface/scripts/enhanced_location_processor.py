import sys
import json
import csv
import argparse
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import math
from typing import List, Dict, Any, Tuple

class EnhancedLocationHighlightProcessor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'location_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        self.connection = None
        self.search_radius_km = 10.0  # Default search radius in kilometers

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

    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate the great circle distance between two points on Earth in kilometers"""
        # Convert decimal degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r

    def get_project_data(self, project_id: str) -> Dict[str, Any]:
        """Get project information from projects table"""
        if not self.connection:
            return {}

        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT project_id, name, lat, lng, timestamp, status, description
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

    def get_surrounding_pois(self, project_lat: float, project_lng: float, radius_km: float = None) -> List[Dict[str, Any]]:
        """Get POIs within specified radius of project location"""
        if not self.connection:
            return []

        if radius_km is None:
            radius_km = self.search_radius_km

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Using bounding box for initial filtering, then precise distance calculation
            lat_range = radius_km / 111.0  # Approximate degrees per km for latitude
            lng_range = radius_km / (111.0 * math.cos(math.radians(project_lat)))  # Adjust for longitude
            
            query = """
            SELECT *,
                   (6371 * acos(cos(radians(%s)) * cos(radians(lat)) * 
                   cos(radians(lng) - radians(%s)) + sin(radians(%s)) * 
                   sin(radians(lat)))) AS distance_km
            FROM poi_extractions_surrounding
            WHERE lat BETWEEN %s AND %s
            AND lng BETWEEN %s AND %s
            HAVING distance_km <= %s
            ORDER BY distance_km ASC
            LIMIT 100
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
            print(f"Error fetching POI data: {e}", file=sys.stderr)
            return []

    def get_nearby_airports(self, project_lat: float, project_lng: float, radius_km: float = 50.0) -> List[Dict[str, Any]]:
        """Get airports within specified radius of project location"""
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            lat_range = radius_km / 111.0
            lng_range = radius_km / (111.0 * math.cos(math.radians(project_lat)))
            
            query = """
            SELECT *,
                   (6371 * acos(cos(radians(%s)) * cos(radians(latitude_deg)) * 
                   cos(radians(longitude_deg) - radians(%s)) + sin(radians(%s)) * 
                   sin(radians(latitude_deg)))) AS distance_km
            FROM airports
            WHERE latitude_deg BETWEEN %s AND %s
            AND longitude_deg BETWEEN %s AND %s
            HAVING distance_km <= %s
            ORDER BY distance_km ASC
            LIMIT 20
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

    def calculate_relevance_score(self, poi_data: Dict[str, Any], distance_km: float) -> float:
        """Calculate relevance score based on POI characteristics and distance"""
        base_score = 50.0
        
        # Distance factor (closer = higher score)
        distance_factor = max(0, 100 - (distance_km * 10))
        
        # Rating factor
        rating_factor = 0
        if poi_data.get('rating') and poi_data.get('rating_count'):
            rating = float(poi_data['rating'])
            rating_count = int(poi_data['rating_count'])
            rating_factor = (rating * 10) + min(rating_count / 100, 20)
        
        # POI type importance
        important_types = {
            'hospital': 30, 'school': 25, 'university': 25, 'police': 25,
            'fire_station': 25, 'subway_station': 20, 'bus_station': 15,
            'shopping_mall': 15, 'restaurant': 10, 'gas_station': 10,
            'tourist_attraction': 20, 'park': 15
        }
        
        type_factor = important_types.get(poi_data.get('poi_type', ''), 5)
        
        total_score = base_score + distance_factor + rating_factor + type_factor
        return min(100.0, max(0.0, total_score))

    def generate_poi_highlights(self, project_data: Dict[str, Any], pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate location highlights from POI data"""
        highlights = []
        
        for poi in pois:
            distance_km = poi.get('distance_km', 0)
            relevance_score = self.calculate_relevance_score(poi, distance_km)
            
            # Determine priority based on POI type and distance
            priority = 'low'
            if poi.get('poi_type') in ['hospital', 'police', 'fire_station'] and distance_km < 2:
                priority = 'high'
            elif poi.get('poi_type') in ['school', 'university', 'subway_station'] and distance_km < 5:
                priority = 'medium'
            elif distance_km < 1:
                priority = 'medium'
            
            # Generate description based on POI characteristics
            description = self.generate_poi_description(poi)
            
            highlight = {
                'project_id': project_data['project_id'],
                'highlight_type': poi.get('poi_type', 'unknown'),
                'category': 'poi',
                'title': poi.get('name', 'Unknown POI'),
                'description': description,
                'priority': priority,
                'status': 'active',
                'source_table': 'poi_extractions_surrounding',
                'source_id': poi.get('id'),
                'distance_km': round(distance_km, 2),
                'relevance_score': round(relevance_score, 2),
                'lat': poi.get('lat'),
                'lng': poi.get('lng'),
                'address': poi.get('address', ''),
                'rating': poi.get('rating'),
                'rating_count': poi.get('rating_count'),
                'website': poi.get('website'),
                'business_status': poi.get('business_status'),
                'wheelchair_accessible': poi.get('wheelchair_accessible'),
                'created_at': datetime.now().isoformat()
            }
            
            highlights.append(highlight)
        
        return highlights

    def generate_airport_highlights(self, project_data: Dict[str, Any], airports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate location highlights from airport data"""
        highlights = []
        
        for airport in airports:
            distance_km = airport.get('distance_km', 0)
            
            # Determine priority based on airport type and distance
            priority = 'low'
            if airport.get('type') == 'large_airport' and distance_km < 30:
                priority = 'high'
            elif airport.get('type') == 'medium_airport' and distance_km < 20:
                priority = 'medium'
            elif distance_km < 10:
                priority = 'medium'
            
            description = f"Airport located {distance_km:.1f}km from project site. "
            if airport.get('iata_code'):
                description += f"IATA Code: {airport['iata_code']}. "
            if airport.get('type'):
                description += f"Type: {airport['type'].replace('_', ' ').title()}."
            
            highlight = {
                'project_id': project_data['project_id'],
                'highlight_type': 'airport',
                'category': 'airport',
                'title': airport.get('name', 'Unknown Airport'),
                'description': description,
                'priority': priority,
                'status': 'active',
                'source_table': 'airports',
                'source_id': airport.get('id'),
                'distance_km': round(distance_km, 2),
                'relevance_score': airport.get('score', 50.0),
                'lat': airport.get('latitude_deg'),
                'lng': airport.get('longitude_deg'),
                'airport_type': airport.get('type'),
                'iata_code': airport.get('iata_code'),
                'municipality': airport.get('municipality'),
                'created_at': datetime.now().isoformat()
            }
            
            highlights.append(highlight)
        
        return highlights

    def generate_poi_description(self, poi: Dict[str, Any]) -> str:
        """Generate descriptive text for POI highlight"""
        description_parts = []
        
        # Basic info
        poi_type = poi.get('poi_type', 'location').replace('_', ' ').title()
        distance = poi.get('distance_km', 0)
        description_parts.append(f"{poi_type} located {distance:.2f}km from project site.")
        
        # Rating info
        if poi.get('rating') and poi.get('rating_count'):
            rating = poi['rating']
            count = poi['rating_count']
            description_parts.append(f"Rated {rating}/5.0 based on {count} reviews.")
        
        # Business status
        if poi.get('business_status') == 'OPERATIONAL':
            description_parts.append("Currently operational.")
        elif poi.get('business_status'):
            description_parts.append(f"Status: {poi['business_status']}.")
        
        # Accessibility
        if poi.get('wheelchair_accessible'):
            description_parts.append("Wheelchair accessible.")
        
        # Additional context based on type
        poi_type_lower = poi.get('poi_type', '').lower()
        if poi_type_lower in ['hospital', 'clinic']:
            description_parts.append("Important for emergency medical services access.")
        elif poi_type_lower in ['school', 'university']:
            description_parts.append("Consider traffic patterns during school hours.")
        elif poi_type_lower in ['subway_station', 'bus_station']:
            description_parts.append("Provides public transportation connectivity.")
        elif poi_type_lower == 'gas_station':
            description_parts.append("Convenient for project vehicle refueling.")
        
        return " ".join(description_parts)

    def save_highlights_to_db(self, highlights: List[Dict[str, Any]]) -> bool:
        """Save generated highlights to database"""
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
            (project_id, highlight_type, category, title, description, priority, status, 
             source_table, source_id, distance_km, relevance_score, lat, lng, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for highlight in highlights:
                metadata = {
                    'address': highlight.get('address'),
                    'rating': highlight.get('rating'),
                    'rating_count': highlight.get('rating_count'),
                    'website': highlight.get('website'),
                    'business_status': highlight.get('business_status'),
                    'wheelchair_accessible': highlight.get('wheelchair_accessible'),
                    'airport_type': highlight.get('airport_type'),
                    'iata_code': highlight.get('iata_code'),
                    'municipality': highlight.get('municipality')
                }
                
                cursor.execute(insert_query, (
                    highlight['project_id'],
                    highlight['highlight_type'],
                    highlight['category'],
                    highlight['title'],
                    highlight['description'],
                    highlight['priority'],
                    highlight['status'],
                    highlight['source_table'],
                    highlight['source_id'],
                    highlight['distance_km'],
                    highlight['relevance_score'],
                    highlight['lat'],
                    highlight['lng'],
                    json.dumps(metadata)
                ))
            
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            print(f"Error saving highlights to database: {e}", file=sys.stderr)
            return False

    def process_single_project(self, project_id: str) -> Dict[str, Any]:
        """Process a single project ID and generate location highlights"""
        if not self.connect_to_database():
            return {"error": "Database connection failed"}

        try:
            # Get project data
            project_data = self.get_project_data(project_id)
            if not project_data:
                return {"error": f"Project {project_id} not found"}

            project_lat = float(project_data['lat'])
            project_lng = float(project_data['lng'])

            # Get surrounding POIs
            pois = self.get_surrounding_pois(project_lat, project_lng)
            
            # Get nearby airports
            airports = self.get_nearby_airports(project_lat, project_lng)

            # Generate highlights
            poi_highlights = self.generate_poi_highlights(project_data, pois)
            airport_highlights = self.generate_airport_highlights(project_data, airports)
            
            all_highlights = poi_highlights + airport_highlights
            
            # Sort by relevance score and distance
            all_highlights.sort(key=lambda x: (-x['relevance_score'], x['distance_km']))

            # Save to database
            self.save_highlights_to_db(all_highlights)

            result = {
                "project_id": project_id,
                "project_name": project_data['name'],
                "project_location": {
                    "lat": project_lat,
                    "lng": project_lng
                },
                "highlights": all_highlights,
                "total_highlights": len(all_highlights),
                "poi_count": len(poi_highlights),
                "airport_count": len(airport_highlights),
                "processed_at": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            return {"error": f"Error processing project: {str(e)}"}

        finally:
            self.close_connection()

    def process_multiple_projects(self, csv_file_path: str) -> Dict[str, Any]:
        """Process multiple project IDs from CSV file"""
        if not self.connect_to_database():
            return {"error": "Database connection failed"}

        try:
            project_ids = []
            
            # Read project IDs from CSV
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header if present
                first_row = next(reader, None)
                if first_row and not first_row[0].startswith('PROJ'):
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

            # Process each project ID
            for project_id in project_ids:
                try:
                    result = self.process_single_project(project_id)
                    if "error" not in result:
                        all_highlights.extend(result['highlights'])
                        processed_projects.append({
                            'project_id': project_id,
                            'project_name': result['project_name'],
                            'highlights_count': result['total_highlights']
                        })
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

            # Sort all highlights by relevance
            all_highlights.sort(key=lambda x: (-x['relevance_score'], x['distance_km']))

            result = {
                "totalProjects": len(project_ids),
                "processedCount": len(processed_projects),
                "failedCount": len(failed_projects),
                "totalHighlights": len(all_highlights),
                "highlights": all_highlights,
                "preview": all_highlights[:10],  # First 10 results for preview
                "processed_projects": processed_projects,
                "failed_projects": failed_projects,
                "processed_at": datetime.now().isoformat()
            }

            return result

        except Exception as e:
            return {"error": f"Error processing CSV: {str(e)}"}

        finally:
            self.close_connection()

def main():
    parser = argparse.ArgumentParser(description='Enhanced location highlights processor')
    parser.add_argument('--single', type=str, help='Single project ID to process')
    parser.add_argument('--multiple', type=str, help='CSV file path with multiple project IDs')
    parser.add_argument('--radius', type=float, default=10.0, help='Search radius in kilometers')
    
    args = parser.parse_args()
    
    processor = EnhancedLocationHighlightProcessor()
    processor.search_radius_km = args.radius
    
    if args.single:
        result = processor.process_single_project(args.single)
    elif args.multiple:
        result = processor.process_multiple_projects(args.multiple)
    else:
        result = {"error": "Please provide either --single or --multiple argument"}
    
    # Output result as JSON
    print(json.dumps(result, default=str))

if __name__ == "__main__":
    main()
