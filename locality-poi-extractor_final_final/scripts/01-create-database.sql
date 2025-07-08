-- Create database
CREATE DATABASE IF NOT EXISTS locality_poi_db;
USE locality_poi_db;

-- Create localities table
CREATE TABLE IF NOT EXISTS localities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  locality_id VARCHAR(50) UNIQUE NOT NULL,
  locality_name VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  lat DECIMAL(10, 8) NOT NULL,
  lng DECIMAL(11, 8) NOT NULL,
  synonyms TEXT,
  child_locality TEXT,
  mp_list TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_locality_id (locality_id),
  INDEX idx_city (city),
  INDEX idx_locality_name (locality_name)
);
