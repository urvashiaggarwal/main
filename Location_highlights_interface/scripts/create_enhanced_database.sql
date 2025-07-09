-- Create enhanced database schema for location highlights system

CREATE DATABASE IF NOT EXISTS location_db;
USE location_db;

-- Projects table with coordinates and timestamp
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive', 'completed') DEFAULT 'active',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_coordinates (lat, lng),
    INDEX idx_timestamp (timestamp)
);

-- POI extractions surrounding table (already present according to user)
CREATE TABLE IF NOT EXISTS poi_extractions_surrounding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    locality_id VARCHAR(100),
    locality_name VARCHAR(255),
    city VARCHAR(255),
    poi_type VARCHAR(100),
    name VARCHAR(255),
    place_id VARCHAR(255),
    primary_type VARCHAR(100),
    types TEXT,
    api_primary_type VARCHAR(100),
    address TEXT,
    rating DECIMAL(3,2),
    rating_count INT,
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    google_map_url TEXT,
    containing_place VARCHAR(255),
    containment_within TEXT,
    business_status VARCHAR(50),
    parking_options TEXT,
    wheelchair_accessible BOOLEAN,
    website TEXT,
    summary TEXT,
    photos_reference TEXT,
    reviews TEXT,
    extraction_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_locality_id (locality_id),
    INDEX idx_coordinates (lat, lng),
    INDEX idx_poi_type (poi_type),
    INDEX idx_primary_type (primary_type),
    INDEX idx_city (city),
    INDEX idx_extraction_date (extraction_date)
);

-- Airports table
CREATE TABLE IF NOT EXISTS airports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ident VARCHAR(10) UNIQUE NOT NULL,
    type VARCHAR(50),
    name VARCHAR(255),
    address TEXT,
    latitude_deg DECIMAL(10, 8),
    longitude_deg DECIMAL(11, 8),
    continent VARCHAR(10),
    iso_country VARCHAR(10),
    iso_region VARCHAR(10),
    municipality VARCHAR(255),
    gps_code VARCHAR(10),
    iata_code VARCHAR(10),
    home_link TEXT,
    wikipedia_link TEXT,
    keywords TEXT,
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ident (ident),
    INDEX idx_coordinates (latitude_deg, longitude_deg),
    INDEX idx_iata_code (iata_code),
    INDEX idx_type (type),
    INDEX idx_country (iso_country),
    INDEX idx_municipality (municipality)
);

-- Location highlights table (enhanced)
CREATE TABLE IF NOT EXISTS location_highlights (
    highlight_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(50),
    highlight_type VARCHAR(100) NOT NULL,
    category ENUM('poi', 'airport', 'infrastructure', 'accessibility', 'safety', 'environmental') DEFAULT 'poi',
    title VARCHAR(255),
    description TEXT,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('active', 'resolved', 'archived') DEFAULT 'active',
    source_table VARCHAR(50), -- 'poi_extractions_surrounding' or 'airports'
    source_id INT,
    distance_km DECIMAL(8,3), -- Distance from project location
    relevance_score DECIMAL(5,2),
    metadata JSON,
    lat DECIMAL(10, 8),
    lng DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_highlight_type (highlight_type),
    INDEX idx_category (category),
    INDEX idx_priority (priority),
    INDEX idx_status (status),
    INDEX idx_distance (distance_km),
    INDEX idx_coordinates (lat, lng)
);
