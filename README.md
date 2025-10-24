# Inventory Values Report Service

Automated service to scrape Markov inventory data and upload to PostgreSQL database on Railway. Runs as a daily cron job.

## Features

- Scrapes inventory data from Markov dashboard
- Transforms and aggregates inventory records
- Uploads to PostgreSQL with upsert logic (handles duplicates)
- Dockerized for easy deployment
- Configured as Railway cron job (runs daily at midnight UTC)

## Project Structure

```
.
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Local testing with Docker
├── railway.json               # Railway deployment config (cron schedule)
├── requirements.txt           # Python dependencies
├── main.py                    # Main orchestration script
├── scrape_markov_inventory.py # Markov scraper module
├── upload_to_postgres.py     # PostgreSQL upload module
└── .env.example              # Environment variables template
```

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Docker (optional, for testing containerized version)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variable:
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

3. Run the script:
```bash
python main.py
```

### Local Docker Testing

1. Build the image:
```bash
docker build -t inventory-scraper .
```

2. Run the container:
```bash
docker run -e DATABASE_URL="your_database_url" inventory-scraper
```

Or use docker-compose:
```bash
export DATABASE_URL="your_database_url"
docker-compose up
```

## Railway Deployment

### Initial Setup

1. Install Railway CLI (optional):
```bash
npm i -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

### Deploy to Railway

#### Option 1: Using Railway CLI

```bash
railway up
```

#### Option 2: Using GitHub Integration

1. Push code to GitHub
2. Connect repository in Railway dashboard
3. Railway will auto-detect Dockerfile and deploy

### Configure Environment Variables

In Railway dashboard, add the following environment variable:

- `DATABASE_URL`: Your PostgreSQL connection string

Railway will automatically provide `DATABASE_URL` if you link a Railway PostgreSQL database to your service.

### Cron Schedule

The service is configured to run **daily at midnight UTC** (12:00 AM UTC).

The cron schedule is defined in `railway.json`:
```json
"cronSchedule": "0 0 * * *"
```

To modify the schedule, update the cron expression:
- `0 0 * * *` - Daily at midnight UTC
- `0 */6 * * *` - Every 6 hours
- `0 9 * * *` - Daily at 9:00 AM UTC
- `0 0 * * 1` - Weekly on Monday at midnight

After changing, redeploy:
```bash
railway up
```

### Monitoring

- View logs in Railway dashboard
- Check deployment status
- Monitor cron job executions

## Database Schema

The service uploads to the `inventory_cost` table with the following columns:

| Column            | Type  | Nullable |
|-------------------|-------|----------|
| key               | text  | NO       |
| gl_group          | text  | YES      |
| type              | text  | YES      |
| qty               | real  | YES      |
| unit              | text  | YES      |
| actual_unit_cost  | money | YES      |
| actual_value      | money | YES      |
| date              | date  | YES      |
| area              | text  | YES      |
| item              | text  | YES      |

Primary key: `key`

## Troubleshooting

### Connection Issues

Check DATABASE_URL format:
```
postgresql://username:password@hostname:port/database
```

### Scraping Fails

- Verify Markov credentials in `scrape_markov_inventory.py`
- Check network connectivity
- Review error logs

### Railway Deployment Issues

- Ensure `railway.json` is in root directory
- Verify environment variables are set
- Check build logs in Railway dashboard

## License

Internal use only - Shottys LLC
