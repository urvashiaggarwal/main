-- Insert sample localities
INSERT INTO localities (locality_id, locality_name, city, lat, lng, synonyms, child_locality, mp_list) VALUES
('894722', 'Niwaru Road', 'Jaipur', 26.9124, 75.7873, 'Niwaru, Niwar Road', NULL, 'Niwaru Road, Jaipur'),
('123456', 'Koramangala', 'Bangalore', 12.9352, 77.6245, 'Koramangala, Kormangala', '1st Block, 4th Block, 6th Block', 'Koramangala, Bangalore'),
('789012', 'Bandra West', 'Mumbai', 19.0596, 72.8295, 'Bandra, Bandra W', 'Linking Road, Hill Road', 'Bandra West, Mumbai'),
('345678', 'Connaught Place', 'Delhi', 28.6315, 77.2167, 'CP, Connaught Place, Rajiv Chowk', NULL, 'Connaught Place, New Delhi'),
('567890', 'Cyber City', 'Gurugram', 28.4595, 77.0266, 'Cybercity, DLF Cyber City', 'Phase 1, Phase 2, Phase 3', 'Cyber City, Gurugram');
