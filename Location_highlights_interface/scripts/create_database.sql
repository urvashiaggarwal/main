-- Create database and tables for location highlights system

CREATE DATABASE IF NOT EXISTS location_db;
USE location_db;

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255),
    description TEXT,
    status ENUM('active', 'inactive', 'completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(50),
    location_name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_coordinates (latitude, longitude)
);

-- Location highlights table
CREATE TABLE IF NOT EXISTS location_highlights (
    highlight_id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT,
    highlight_type VARCHAR(100) NOT NULL,
    description TEXT,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('active', 'resolved', 'archived') DEFAULT 'active',
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    INDEX idx_location_id (location_id),
    INDEX idx_highlight_type (highlight_type),
    INDEX idx_status (status)
);

-- Create indexes for better performance
CREATE INDEX idx_project_location ON locations(project_id, location_name);
CREATE INDEX idx_highlight_priority ON location_highlights(priority, status);
