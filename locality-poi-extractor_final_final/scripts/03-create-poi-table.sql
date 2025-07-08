-- Create main POI extractions table (filtered POIs)
CREATE TABLE IF NOT EXISTS poi_extractions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  locality_id VARCHAR(50) NOT NULL,
  locality_name VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  poi_type VARCHAR(50) NOT NULL,
  name VARCHAR(255),
  place_id VARCHAR(255),
  primary_type VARCHAR(100),
  types JSON,
  api_primary_type VARCHAR(100),
  address TEXT,
  rating DECIMAL(2,1),
  rating_count INT DEFAULT 0,
  lat DECIMAL(10, 8),
  lng DECIMAL(11, 8),
  google_map_url TEXT,
  containing_place VARCHAR(255),
  containment_within JSON,
  business_status VARCHAR(50) DEFAULT 'OPERATIONAL',
  parking_options JSON,
  wheelchair_accessible BOOLEAN,
  website VARCHAR(500),
  summary TEXT,
  photos_reference JSON,
  reviews JSON,
  extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  INDEX idx_locality_id (locality_id),
  INDEX idx_poi_type (poi_type),
  INDEX idx_extraction_date (extraction_date),
  FOREIGN KEY (locality_id) REFERENCES localities(locality_id) ON DELETE CASCADE
);

-- Create POI extraction jobs table
CREATE TABLE IF NOT EXISTS poi_extraction_jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  locality_id VARCHAR(50) NOT NULL,
  status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
  total_pois INT DEFAULT 0,
  processed_pois INT DEFAULT 0,
  error_message TEXT,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  
  INDEX idx_locality_id (locality_id),
  INDEX idx_status (status),
  FOREIGN KEY (locality_id) REFERENCES localities(locality_id) ON DELETE CASCADE
);
