import sys
import json
import csv
import argparse
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class LocationHighlightProcessor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'location_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        self.connection = None

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

    def get_location_highlights(self, project_id):
        """Fetch location highlights for a specific project ID"""
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Query to get location highlights for the project
            query = """
            SELECT 
                p.project_id,
                l.location_name as location,
                lh.highlight_type,
                lh.description,
                CONCAT(l.latitude, ',', l.longitude) as coordinates,
                lh.created_at
            FROM projects p
            JOIN locations l ON p.project_id = l.project_id
            JOIN location_highlights lh ON l.location_id = lh.location_id
            WHERE p.project_id = %s
            ORDER BY lh.created_at DESC
            """
            
            cursor.execute(query, (project_id,))
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            print(f"Error fetching location highlights: {e}", file=sys.stderr)
            return []

    def process_single_project(self, project_id):
        """Process a single project ID"""
        if not self.connect_to_database():
            return {"error": "Database connection failed"}

        try:
            highlights = self.get_location_highlights(project_id)
            
            result = {
                "project_id": project_id,
                "highlights": highlights,
                "total_highlights": len(highlights),
                "processed_at": datetime.now().isoformat()
            }
            
            return result
            
        finally:
            self.close_connection()

    def process_multiple_projects(self, csv_file_path):
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
                    # If first row doesn't look like a project ID, it's probably a header
                    pass
                else:
                    # First row is a project ID, add it back
                    if first_row:
                        project_ids.append(first_row[0].strip())
                
                # Read remaining rows
                for row in reader:
                    if row and row[0].strip():
                        project_ids.append(row[0].strip())

            all_highlights = []
            processed_count = 0
            
            # Process each project ID
            for project_id in project_ids:
                highlights = self.get_location_highlights(project_id)
                for highlight in highlights:
                    all_highlights.append(highlight)
                if highlights:
                    processed_count += 1

            result = {
                "totalProjects": len(project_ids),
                "processedCount": processed_count,
                "totalHighlights": len(all_highlights),
                "highlights": all_highlights,
                "preview": all_highlights[:5],  # First 5 results for preview
                "processed_at": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Error processing CSV: {str(e)}"}
            
        finally:
            self.close_connection()

def main():
    parser = argparse.ArgumentParser(description='Process location highlights for project IDs')
    parser.add_argument('--single', type=str, help='Single project ID to process')
    parser.add_argument('--multiple', type=str, help='CSV file path with multiple project IDs')
    
    args = parser.parse_args()
    
    processor = LocationHighlightProcessor()
    
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
