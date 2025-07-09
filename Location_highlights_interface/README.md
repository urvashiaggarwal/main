# Location Highlights Finder

A full-stack web application for intelligent location analysis and project management. Upload, process, and analyze real estate or project locations to generate actionable highlights using Google Maps data, advanced scoring, and smart caching.

## Features
- **Single & Batch Project Processing:** Analyze one or many projects via UI or CSV upload.
- **Project Creation:** Add new projects with geolocation and city details.
- **Location Intelligence:** Get POI, airport, and golf course highlights for each project.
- **Smart Caching:** Reuses results up to 2 months old for efficiency.
- **Interactive Dashboard:** View, filter, and download results. See failed projects and create missing ones.
- **Modern UI:** Built with React, Next.js, Tailwind CSS, and Radix UI components.

## Tech Stack
- **Frontend:** React, Next.js, Tailwind CSS, Radix UI
- **Backend:** Next.js API routes, Python (location processing scripts)
- **Database:** MySQL (see `scripts/create_database.sql`)
- **Integrations:** Google Maps API

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.8+
- MySQL 8+
- Google Maps API Key (for full POI/Distance features)

### Installation
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd location-highlights-finder_final_final
   ```
2. **Install dependencies:**
   ```bash
   npm install
   # or
   pnpm install
   ```
3. **Set up the database:**
   - Create a MySQL database and user.
   - Run the schema script:
     ```bash
     mysql -u <user> -p < scripts/create_database.sql
     # or for enhanced schema:
     mysql -u <user> -p < scripts/create_enhanced_database.sql
     ```
   - (Optional) Seed with sample data:
     ```bash
     mysql -u <user> -p < scripts/seed_sample_data.sql
     ```
4. **Configure environment variables:**
   - Create a `.env.local` file in the root with:
     ```env
     DB_HOST=localhost
     DB_NAME=location_db
     DB_USER=root
     DB_PASSWORD=yourpassword
     DB_PORT=3306
     GOOGLE_MAPS_API_KEY=your_gmaps_key
     ```
5. **Run the development server:**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```
   The app will be available at [http://localhost:3000](http://localhost:3000)

## Usage
- **Single Project:** Enter a project ID to process and view highlights.
- **Batch Processing:** Upload a CSV of project IDs for bulk analysis.
- **Create Projects:** Add new projects manually or via CSV.
- **Download Results:** Export highlights as CSV.
- **Failed Projects:** See which projects need to be created and add them easily.

## Backend & Data Processing
- **API Endpoints:**
  - `/api/create-project` - Add a single project
  - `/api/create-projects` - Add multiple projects via CSV
  - `/api/process-single` - Process a single project (calls Python script)
  - `/api/process-multiple` - Process multiple projects (calls Python script)
- **Python Scripts:**
  - `scripts/integrated_location_processor.py` - Main logic for POI, airport, and golf course analysis
  - `scripts/process_locations.py` - Utility for fetching highlights
- **Database Schema:**
  - See `scripts/create_database.sql` and `scripts/create_enhanced_database.sql` for table definitions

## Folder Structure
- `app/` - Next.js app, API routes, pages
- `components/` - UI components
- `hooks/` - Custom React hooks
- `lib/` - Utility functions
- `scripts/` - Database SQL and Python processing scripts
- `public/` - Static assets

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE)
