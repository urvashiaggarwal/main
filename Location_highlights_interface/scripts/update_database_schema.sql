-- Update database schema to match actual table structures

USE location_db;

-- Update projects table to match actual structure
DROP TABLE IF EXISTS projects;
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(100),
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_coordinates (latitude, longitude)
);

-- Update airports table to match actual structure (already exists)
-- Airports table structure is correct as shown in image

-- poi_extractions_surrounding table structure is correct as shown
-- No changes needed

-- Update location_highlights table to store results in the required format
DROP TABLE IF EXISTS location_highlights;
CREATE TABLE location_highlights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL,
    poi_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    distance_km DECIMAL(8, 2),
    step1_score DECIMAL(10, 6),
    rating DECIMAL(2,1),
    rating_count INT,
    driving_distance VARCHAR(50),
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    priority VARCHAR(20),
    category VARCHAR(50),
    from_cache BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_poi_type (poi_type),
    INDEX idx_created_at (created_at)
);

-- Insert sample project data to match your example
INSERT INTO projects (city, project_id, project_name, latitude, longitude) VALUES
('Bangalore East', '418319', 'Brigade Sanctuary', 12.895087, 77.749055);
