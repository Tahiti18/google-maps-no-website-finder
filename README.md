# Google Maps No-Website Finder

A production-ready web application for finding businesses on Google Maps that do not have a website listed in their Google Business Profile. This tool is designed for lead generation, helping identify local businesses that may need web development and marketing services.

## Overview

This application uses the official Google Places API to search for businesses by geography and category, then filters to identify businesses marked as "OPERATIONAL" but lacking a website field. Results are stored in a PostgreSQL database with deduplication and can be exported as CSV or JSON for outreach campaigns.

## Features

- 🔍 **Smart Business Discovery**: Search by US state, cities, and business categories
- 🌐 **Official Google API**: Uses Google Places Text Search and Place Details APIs
- 🎯 **Advanced Filtering**: Filter by operational status, minimum rating, and review count
- 📊 **Persistent Storage**: PostgreSQL database with deduplication by Google Place ID
- 🚀 **Background Processing**: Asynchronous scan execution with status tracking
- 📥 **Multiple Export Formats**: Download results as CSV or JSON
- 🖥️ **Clean Web UI**: Simple dashboard for creating scans and viewing results
- 📡 **RESTful API**: Full API for programmatic access

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Database**: PostgreSQL (with SQLite support for local dev)
- **ORM**: SQLAlchemy with Alembic migrations
- **Background Jobs**: Threading-based worker (extensible to Celery/RQ)
- **Frontend**: Jinja2 templates, vanilla JavaScript, CSS
- **APIs**: Google Places API (Text Search + Place Details)

## Project Structure

```
google-maps-no-website-finder/
├── app/
│   ├── api/                    # API route handlers
│   │   └── scans.py
│   ├── models/                 # SQLAlchemy models
│   │   ├── scan.py
│   │   ├── business.py
│   │   └── scan_result.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── scan.py
│   │   └── business.py
│   ├── services/               # Business logic
│   │   ├── google_places.py   # Google API integration
│   │   ├── scanner.py         # Scanning logic
│   │   └── worker.py          # Background worker
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── scan_detail.html
│   ├── static/                 # Static assets
│   │   └── css/
│   │       └── style.css
│   ├── config.py              # Configuration
│   ├── db.py                  # Database session
│   └── main.py                # FastAPI application
├── migrations/                 # Alembic migrations
│   ├── env.py
│   └── script.py.mako
├── tests/                      # Unit tests
│   ├── test_google_places.py
│   └── test_api.py
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── alembic.ini                # Alembic configuration
├── .env.example               # Environment variables template
├── .gitignore
└── README.md
```

## Prerequisites

- **Python 3.10+**
- **PostgreSQL 12+** (or use SQLite for local testing)
- **Google Cloud Project** with Places API enabled
- **Google Maps API Key**

### Setting Up Google Places API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Places API
   - Geocoding API (optional, for coordinate-based searches)
4. Create credentials:
   - Navigate to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Restrict the key to the enabled APIs for security
5. Copy your API key for use in `.env` file

**Important**: Google Places API is a paid service. Review the [pricing](https://mapsplatform.google.com/pricing/) and set up billing alerts.

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd google-maps-no-website-finder
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/gmaps_finder

# SQLite (simpler for local development)
# DATABASE_URL=sqlite:///./gmaps_finder.db

# Your Google Maps API key
GOOGLE_MAPS_API_KEY=your_actual_api_key_here

# Application settings
APP_ENV=development
LOG_LEVEL=INFO
```

### 5. Set Up Database

#### Option A: PostgreSQL (Recommended)

```bash
# Create database
createdb gmaps_finder

# Run migrations
alembic upgrade head
```

#### Option B: SQLite (Simpler for Development)

```bash
# Update .env to use SQLite
DATABASE_URL=sqlite:///./gmaps_finder.db

# Run migrations
alembic upgrade head
```

### 6. Run the Application

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using the built-in runner
python app/main.py
```

The application will be available at: http://localhost:8000

## Usage

### Web Interface

1. Open http://localhost:8000 in your browser
2. Fill out the scan form:
   - **State**: 2-letter code (e.g., "CA")
   - **Cities**: One per line (e.g., "Los Angeles", "San Diego")
   - **Categories**: One per line (e.g., "dentist", "plumber", "roofing contractor")
   - **Optional Filters**: Minimum rating, minimum review count
3. Click "Start Scan" - the scan will run in the background
4. View scan status and results in the dashboard
5. Download results as CSV or JSON

### API Endpoints

#### Create a Scan

```bash
POST /api/scans
Content-Type: application/json

{
  "state": "CA",
  "cities": ["Los Angeles", "San Diego"],
  "categories": ["dentist", "plumber"],
  "min_rating": 4.0,
  "min_reviews": 10
}
```

Response:
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00",
  "status": "queued",
  "scan_type": "city_based",
  "input_state": "CA",
  "cities_count": 2,
  "categories_count": 2
}
```

#### List Scans

```bash
GET /api/scans?limit=20&offset=0
```

#### Get Scan Details

```bash
GET /api/scans/{scan_id}
```

#### Get Scan Results

```bash
# JSON format
GET /api/scans/{scan_id}/results?format=json&no_website_only=true

# CSV format (downloads file)
GET /api/scans/{scan_id}/results?format=csv&no_website_only=true
```

## Data Model

### Scans Table
Stores scan job metadata:
- `id`: UUID primary key
- `status`: queued, running, completed, failed
- `input_state`, `input_categories`: Search parameters
- `min_rating`, `min_reviews`: Optional filters
- `total_businesses_processed`, `total_without_website`: Summary counts

### Businesses Table
Stores unique businesses (deduplicated by `place_id`):
- `place_id`: Google Place ID (unique)
- `name`, `formatted_address`: Basic info
- `city`, `state`, `country`: Location
- `latitude`, `longitude`: Coordinates
- `phone`, `website`: Contact info
- `rating`, `user_ratings_total`: Reviews
- `business_status`: OPERATIONAL, etc.
- `categories`: JSONB array of business types

### Scan Results Table
Links scans to businesses:
- `scan_id` → `scans.id`
- `business_id` → `businesses.id`
- `has_website_at_scan_time`: Boolean snapshot

This design allows:
- One business to appear in multiple scans
- Tracking website status changes over time
- Efficient querying of "businesses without websites in scan X"

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_google_places.py -v
```

## Configuration

All configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL/SQLite connection string | `postgresql://...` |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | Required |
| `APP_ENV` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_RATE_LIMIT_DELAY` | Delay between API calls (seconds) | `0.1` |
| `MAX_RESULTS_PER_SEARCH` | Max results per search | `60` |

## Deployment

This application is designed to run on any platform that supports Python and PostgreSQL. Here are general deployment steps:

### General Requirements

1. **Python Runtime**: Python 3.10 or higher
2. **Database**: PostgreSQL instance (managed or self-hosted)
3. **Environment Variables**: Set all required env vars in your platform
4. **Process Manager**: Use a production ASGI server (uvicorn, gunicorn + uvicorn workers)

### Deployment Steps

1. **Prepare Environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export DATABASE_URL="postgresql://..."
   export GOOGLE_MAPS_API_KEY="..."
   export APP_ENV="production"
   export LOG_LEVEL="INFO"
   ```

2. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Start Application**:
   ```bash
   # Using uvicorn (single worker)
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   # Using gunicorn with uvicorn workers (recommended)
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

4. **Health Check**: Verify the deployment at `/health` endpoint

### Platform-Specific Notes

**Railway**:
- Connect GitHub repository
- Add PostgreSQL plugin
- Set environment variables in Railway dashboard
- Railway will auto-detect Python and run the app

**Render**:
- Create new Web Service from GitHub repo
- Add PostgreSQL database
- Set environment variables
- Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Heroku**:
- Create `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add Heroku Postgres addon
- Set config vars for environment variables

**Google Cloud Run**:
- Create `Dockerfile` with Python and dependencies
- Deploy container to Cloud Run
- Connect Cloud SQL PostgreSQL instance
- Set environment variables in Cloud Run settings

## Google API Considerations

### Rate Limiting

The application includes basic rate limiting with configurable delays between API calls. Google Places API has the following limits (as of 2024):

- **Text Search**: $32 per 1,000 requests
- **Place Details**: $17 per 1,000 requests (Basic), $32 (Advanced)
- **Monthly $200 free credit** (approximately 6,250 Place Details calls)

### Cost Optimization

- Each scan makes 1 Text Search call per (city, category) pair
- Each business requires 1 Place Details call
- Set `MAX_RESULTS_PER_SEARCH` lower to reduce costs during testing
- Use `min_rating` and `min_reviews` filters to reduce Place Details calls

### Terms of Service

This application uses official Google APIs and complies with Google's Terms of Service. Ensure you:
- Display results according to Google's attribution requirements
- Do not cache place details for longer than 30 days
- Do not scrape or systematically download Google Maps data
- Review [Google Maps Platform Terms](https://cloud.google.com/maps-platform/terms)

## Future Enhancements

The codebase is structured to support these future features:

### Grid-Based Scanning
- Currently: City-based text search
- Future: Generate lat/lng grid and use Nearby Search for exhaustive coverage
- Implementation stub in `app/models/scan.py` (ScanType.GRID_BASED)

### Background Job Queue
- Currently: Simple threading-based worker
- Future: Celery with Redis/RabbitMQ for distributed processing
- Worker abstraction in `app/services/worker.py` makes this swap easy

### Authentication
- Currently: No authentication (single-user)
- Future: Add user accounts, API keys, role-based access
- Clean API structure supports adding auth middleware

### Scheduled Scans
- Currently: Manual scan creation
- Future: Cron-like scheduled scans to track changes over time

### Email Discovery
- Currently: Only finds businesses without websites
- Future: Integrate email discovery services to enrich leads

### Multi-Country Support
- Currently: Designed for US (state + city)
- Future: Extend to other countries with appropriate location formats

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection manually
psql -h localhost -U postgres -d gmaps_finder

# For SQLite, just check file permissions
ls -la gmaps_finder.db
```

### Google API Errors

- **REQUEST_DENIED**: Check API key is valid and APIs are enabled
- **OVER_QUERY_LIMIT**: Exceeded quota, wait or increase Google Cloud billing
- **INVALID_REQUEST**: Check request parameters (city/state format)

### Worker Not Processing Scans

Check logs for errors:
```bash
# Application logs will show worker startup
# Look for "Worker thread started" message
# Check for scan processing logs
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is provided as-is for business lead generation purposes. Ensure compliance with Google Maps Platform Terms of Service when using this application.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check Google Maps Platform [documentation](https://developers.google.com/maps/documentation/places/web-service/overview)
- Review FastAPI [documentation](https://fastapi.tiangolo.com/)

---

**Note**: This application requires a valid Google Maps API key and incurs costs based on API usage. Always monitor your Google Cloud billing and set up budget alerts.
