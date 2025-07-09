-- Insert sample data for testing

USE location_db;

-- Insert sample projects
INSERT INTO projects (project_id, project_name, description, status) VALUES
('PROJ-12345', 'Downtown Development', 'Urban development project in downtown area', 'active'),
('PROJ-67890', 'Coastal Resort', 'Luxury resort development on the coast', 'active'),
('PROJ-11111', 'Mountain Lodge', 'Eco-friendly lodge in mountain region', 'completed'),
('PROJ-22222', 'City Park Renovation', 'Renovation of central city park', 'active'),
('PROJ-33333', 'Shopping Complex', 'New shopping and entertainment complex', 'inactive');

-- Insert sample locations
INSERT INTO locations (project_id, location_name, address, latitude, longitude, location_type) VALUES
('PROJ-12345', 'Main Plaza', '123 Downtown St, City Center', 40.7128, -74.0060, 'commercial'),
('PROJ-12345', 'Parking Garage', '456 Center Ave, Downtown', 40.7130, -74.0058, 'infrastructure'),
('PROJ-67890', 'Beach Front', 'Ocean View Drive, Coastal Area', 25.7617, -80.1918, 'recreational'),
('PROJ-67890', 'Hotel Lobby', 'Resort Main Building', 25.7620, -80.1920, 'hospitality'),
('PROJ-11111', 'Lodge Entrance', 'Mountain Trail Head', 39.7392, -104.9903, 'hospitality'),
('PROJ-22222', 'Central Fountain', 'City Park Center', 40.7829, -73.9654, 'recreational'),
('PROJ-33333', 'Food Court', 'Shopping Center Level 2', 34.0522, -118.2437, 'commercial');

-- Insert sample location highlights
INSERT INTO location_highlights (location_id, highlight_type, description, priority, status) VALUES
(1, 'Safety Concern', 'Uneven pavement near main entrance requires attention', 'high', 'active'),
(1, 'Accessibility', 'Wheelchair ramp installed and functional', 'medium', 'resolved'),
(2, 'Maintenance', 'Lighting system needs regular inspection', 'medium', 'active'),
(3, 'Environmental', 'Beach erosion monitoring required', 'high', 'active'),
(3, 'Wildlife', 'Sea turtle nesting area - seasonal restrictions apply', 'critical', 'active'),
(4, 'Design Feature', 'Panoramic ocean view from lobby', 'low', 'active'),
(5, 'Scenic View', 'Mountain vista point with hiking trail access', 'medium', 'active'),
(6, 'Water Feature', 'Historic fountain restored to original condition', 'low', 'resolved'),
(7, 'Traffic Flow', 'Peak hours congestion in food court area', 'medium', 'active');
