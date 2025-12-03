# Deployment Guide

This guide covers deploying the Google Maps No-Website Finder application to production environments.

## Prerequisites

Before deploying, ensure you have:

1. **Google Maps API Key** with Places API enabled
2. **PostgreSQL Database** (managed or self-hosted)
3. **Python 3.10+** runtime environment
4. **Access to your deployment platform** (Railway, Render, Heroku, etc.)

## Environment Variables

The application requires these environment variables in production:

```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/database
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Optional (with defaults)
APP_ENV=production
LOG_LEVEL=INFO
API_RATE_LIMIT_DELAY=0.1
MAX_RESULTS_PER_SEARCH=60
```

## Railway Deployment

Railway is the recommended platform for this application.

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `google-maps-no-website-finder` repository

### Step 2: Add PostgreSQL Database

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provision a database and create `DATABASE_URL`

### Step 3: Set Environment Variables

1. Click on your service
2. Go to "Variables" tab
3. Add:
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `APP_ENV`: `production`
   - `LOG_LEVEL`: `INFO`

### Step 4: Configure Start Command

Railway should auto-detect Python, but you can specify the start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or for production with multiple workers:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

(Add `gunicorn` to requirements.txt if using gunicorn)

### Step 5: Run Migrations

After first deployment, run migrations using Railway CLI or the web interface:

```bash
# Using Railway CLI
railway run alembic upgrade head

# Or via web interface: Settings → Service → Run Command
alembic upgrade head
```

### Step 6: Access Your Application

Railway will provide a public URL like: `your-app.up.railway.app`

## Render Deployment

### Step 1: Create Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click "New" → "Web Service"
3. Connect your GitHub repository

### Step 2: Configure Service

- **Name**: `gmaps-finder`
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL

1. Click "New" → "PostgreSQL"
2. Choose a name and plan
3. Copy the "Internal Database URL"

### Step 4: Set Environment Variables

In your web service settings:

- `DATABASE_URL`: (paste PostgreSQL URL)
- `GOOGLE_MAPS_API_KEY`: Your API key
- `APP_ENV`: `production`

### Step 5: Deploy and Run Migrations

After deployment, use Render Shell to run migrations:

```bash
alembic upgrade head
```

## Heroku Deployment

### Step 1: Create Procfile

Create `Procfile` in project root:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: alembic upgrade head
```

### Step 2: Deploy to Heroku

```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set GOOGLE_MAPS_API_KEY=your_key
heroku config:set APP_ENV=production

# Deploy
git push heroku main
```

### Step 3: Verify Deployment

```bash
heroku open
heroku logs --tail
```

## Google Cloud Run Deployment

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start app
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 2: Build and Push

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/gmaps-finder

# Deploy to Cloud Run
gcloud run deploy gmaps-finder \
  --image gcr.io/PROJECT_ID/gmaps-finder \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Step 3: Set Environment Variables

```bash
gcloud run services update gmaps-finder \
  --set-env-vars DATABASE_URL=postgresql://...,GOOGLE_MAPS_API_KEY=...
```

### Step 4: Connect Cloud SQL

Use Cloud SQL Proxy or connect directly via private IP.

## Post-Deployment Checklist

After deploying to any platform:

### 1. Health Check

```bash
curl https://your-app-url.com/health
# Should return: {"status":"healthy"}
```

### 2. Database Verification

Check that tables were created:

```bash
# Connect to your database and verify
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public';

# Should show: scans, businesses, scan_results, scan_cities, alembic_version
```

### 3. Create Test Scan

Use the web interface or API:

```bash
curl -X POST https://your-app-url.com/api/scans \
  -H "Content-Type: application/json" \
  -d '{
    "state": "CA",
    "cities": ["San Francisco"],
    "categories": ["dentist"]
  }'
```

### 4. Monitor Logs

Check application logs for any errors:

- **Railway**: View logs in dashboard
- **Render**: View logs in service page
- **Heroku**: `heroku logs --tail`
- **Cloud Run**: Check Logs Explorer

### 5. Set Up Monitoring

Configure:
- **Error tracking**: Sentry, Rollbar
- **Performance monitoring**: New Relic, Datadog
- **Uptime monitoring**: UptimeRobot, Pingdom

## Scaling Considerations

### Vertical Scaling

For more concurrent scans, increase:
- **RAM**: 512MB minimum, 1GB recommended
- **CPU**: 1 vCPU minimum, 2 vCPUs for high load

### Horizontal Scaling

The application supports multiple instances:
- Background worker uses thread-based processing
- Each instance processes its own scans
- Database handles concurrency via scan status locking

### Future: Distributed Processing

To scale beyond single-instance processing:

1. **Replace** `app/services/worker.py` threading with:
   - Celery + Redis/RabbitMQ
   - Google Cloud Tasks
   - AWS SQS + Lambda

2. **Separate** worker instances from web instances
3. **Add** job queue monitoring

## Troubleshooting

### Common Issues

**Issue**: Database connection fails  
**Solution**: Check `DATABASE_URL` format and network access

**Issue**: Google API errors  
**Solution**: Verify API key, check quota limits, ensure APIs are enabled

**Issue**: Scans stuck in "queued"  
**Solution**: Check logs, verify worker thread started, restart service

**Issue**: High memory usage  
**Solution**: Limit concurrent scans, optimize batch sizes, increase instance RAM

### Debugging Commands

```bash
# Check environment variables
echo $DATABASE_URL
echo $GOOGLE_MAPS_API_KEY

# Test database connection
python -c "from app.db import engine; print(engine.connect())"

# Test Google API
python -c "from app.services.google_places import GooglePlacesService; s=GooglePlacesService(); print(s.search_places_by_city('Los Angeles', 'CA', 'dentist')[:1])"

# Check alembic history
alembic history
alembic current
```

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables** for all secrets
3. **Enable HTTPS** on your deployment platform
4. **Add authentication** before exposing publicly
5. **Set up rate limiting** to prevent abuse
6. **Monitor API costs** in Google Cloud Console
7. **Regular backups** of PostgreSQL database

## Cost Optimization

### Google Places API

- Each scan costs: 1 Text Search + N Place Details calls
- Budget example: $100/month = ~3,000 Place Details calls
- Use filters (`min_rating`, `min_reviews`) to reduce API calls

### Infrastructure

- **Railway Free Tier**: $5/month credit
- **Render Free Tier**: 750 hours/month
- **Heroku Free Tier**: Deprecated (use Hobby tier $7/month)

### Optimization Tips

1. Cache common searches (30-day limit per Google TOS)
2. Schedule scans during off-peak hours
3. Use webhooks instead of polling for status updates
4. Implement exponential backoff for retries

## Support

For deployment issues:
- Check this guide first
- Review platform-specific documentation
- Open an issue on GitHub with deployment logs
- Include platform name, error messages, and environment details

---

**Note**: Always test deployments in a staging environment before promoting to production.
