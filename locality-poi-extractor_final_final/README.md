# Locality POI Extractor

A comprehensive Next.js application for managing localities and extracting Points of Interest (POIs) using Google Places API with advanced filtering and Selenium-based primary type extraction.

## 🚀 Features

- **Single Locality Search**: Look up individual localities by ID with auto-fill
- **Bulk CSV Processing**: Upload CSV files to process multiple localities
- **Locality Creation**: Add new localities to the database
- **Real-time POI Extraction**: Extract POIs using Google Places API (New) with enhanced data
- **Smart Caching**: 2-month freshness check to avoid unnecessary API calls
- **Advanced Filtering**: Multi-tier filtering system (unfiltered → surrounding → filtered)
- **Selenium Integration**: Extract precise primary types from Google Maps pages
- **Enhanced Data**: Includes photos, reviews, accessibility, parking, and more

## 📋 Prerequisites

- Node.js 18+ 
- MySQL 8.0+
- Google Places API Key
- Chrome Browser (for Selenium features)

## 🛠️ Setup Instructions

### 1. Clone and Install
\`\`\`bash
git clone <repository-url>
cd locality-poi-extractor
npm install
\`\`\`

### 2. Database Setup
\`\`\`bash
# Create MySQL database and run scripts in order:
mysql -u root -p < scripts/01-create-database.sql
mysql -u root -p < scripts/02-seed-data.sql  
mysql -u root -p < scripts/03-create-poi-table.sql
mysql -u root -p < scripts/04-create-surrounding-poi-table.sql
\`\`\`

### 3. Environment Configuration
\`\`\`bash
cp .env.example .env.local
\`\`\`
Fill in your database credentials and Google Places API key.

### 4. Selenium Setup (Optional but Recommended)
\`\`\`bash
# Auto setup Chrome + ChromeDriver
npm run setup-selenium

# Or diagnose issues
npm run diagnose-selenium
\`\`\`

### 5. Run Development Server
\`\`\`bash
npm run dev
\`\`\`

Visit `http://localhost:3000`

## 🎯 POI Categories Configured

| Category | Selenium | Primary Type Filtering | Special Features |
|----------|----------|----------------------|------------------|
| **Schools** | ✅ | Exclude playschools, coaching | Website filtering |
| **Hospitals** | ✅ | Include only real hospitals | Exclude clinics, blood banks |
| **Hotels** | ✅ | Include only 4-5 star | Rating-based filtering |
| **Shopping Malls** | ❌ | None | Basic filtering |
| **Colleges** | ❌ | None | University inclusion |
| **Metro Stations** | ✅ | Include only subway | Transport filtering |
| **Railway Stations** | ✅ | Include only trains | Transport filtering |
| **Tourist Attractions** | ❌ | None | High rating threshold |
| **Markets** | ❌ | None | Exclude weekly markets |
| **Parks** | ❌ | None | Basic filtering |

## 🔧 API Endpoints

- `GET /api/localities` - List all localities with pagination
- `GET /api/localities/[id]` - Get single locality with POIs
- `GET /api/localities/[id]/download-csv` - Download POI CSV
- `POST /api/localities` - Create new locality
- `POST /api/localities/bulk` - Bulk locality lookup
- `POST /api/localities/bulk-create` - Bulk locality creation
- `POST /api/localities/bulk-download-csv` - Bulk POI CSV download

## 🏗️ Architecture

### Frontend
- **Next.js 15** with App Router
- **React 18** with TypeScript
- **Tailwind CSS** + **shadcn/ui** components
- **Lucide React** icons

### Backend
- **Next.js API Routes**
- **MySQL** with connection pooling
- **Google Places API (New)** for enhanced POI data
- **Selenium WebDriver** for primary type extraction

### Database Schema
\`\`\`
localities
├── locality_id (PK)
├── locality_name, city, lat, lng
├── synonyms, child_locality, mp_list
└── timestamps

poi_extractions (filtered POIs)
├── locality_id (FK)
├── poi_type, name, place_id
├── primary_type, api_primary_type, types
├── address, rating, rating_count
├── lat, lng, google_map_url
├── business_status, website
├── parking_options, wheelchair_accessible
├── photos_reference, reviews, summary
└── timestamps

poi_extractions_surrounding (surrounding POIs)
└── Same schema as poi_extractions
\`\`\`

## 🎛️ Configuration

### Selenium Configuration
\`\`\`javascript
// Enable/disable Selenium per category
use_selenium: true/false

// Custom XPath for primary type extraction  
selenium_xpath: "//div[@aria-label='Category']"

// Primary type filtering
primary_type_filter_mode: "include" | "exclude" | "none"
primary_type_filter_list: ["Hospital", "Private hospital", ...]
\`\`\`

### Filtering Configuration
\`\`\`javascript
// API type filtering
required_types_api: ["hospital", "school"]

// Name exclusion filtering
name_filter_exclude: ["clinic", "coaching"]

// Rating threshold
rating_count_threshold: 10

// Address/location filtering
apply_within_logic: true
\`\`\`

## 🚨 Troubleshooting

### Selenium Issues
\`\`\`bash
# Diagnose setup
npm run diagnose-selenium

# Auto-fix common issues
npm run setup-selenium

# Manual fix
npm install chromedriver@latest
\`\`\`

### Database Issues
- Ensure MySQL is running
- Check connection credentials in `.env.local`
- Verify all SQL scripts have been executed

### API Issues
- Verify Google Places API key is valid
- Check API quotas and billing
- Ensure Places API (New) is enabled

## 📊 Data Flow

1. **Input**: Locality ID or CSV file
2. **Lookup**: Auto-fill from internal database
3. **Freshness Check**: Check if POIs are < 2 months old
4. **Extraction**: Call Google Places API (New) if needed
5. **Filtering**: Apply multi-tier filtering logic
6. **Selenium**: Extract precise primary types (if enabled)
7. **Storage**: Save to filtered/surrounding tables
8. **Output**: Display results + CSV download

## 🔒 Security

- Environment variables for sensitive data
- SQL injection protection with parameterized queries
- Input validation and sanitization
- Rate limiting for API calls

## 📈 Performance

- Connection pooling for database
- Smart caching with freshness checks
- Batch processing for bulk operations
- Optimized database indexes
- Selenium timeout and error handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details
