# Run Airflow with Docker

This guide will help you run Airflow ArXiv Scraper using Docker on Windows (or any OS).

## Requirements

- Docker Desktop (installed and running)
- Docker Compose (included with Docker Desktop)
- Git Bash or WSL2 (to run .sh scripts)


### Start manually

```bash
# 1. Create a .env file (copy from template)
# Create a .env file with the following content:
```

Content of the `.env` file:
```env
# Airflow configuration. configuration
AIRFLOW_UID=50000
AIRFLOW_IMAGE_NAME=apache/airflow:2.7.3-python3.11

# Database
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# Airflow Admin User
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_ADMIN_EMAIL=admin@example.com
```

```bash
#2. Create necessary folders
mkdir logs
mkdir plugins
mkdir -p tmp/arxiv_data

#3. Build Docker image
docker compose build

# 4. Initialize database
docker compose up airflow-init

#5. Start services
docker compose up -d
```

## 🌐 Access Airflow

After successful startup:

- **Web UI**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`

## 📋 Management commands

### View logs

```bash
# View logs of all services
docker compose logs -f

# View logs of a specific service
docker compose logs -f airflow-webserver
docker compose logs -f airflow-scheduler
```

### Stop Airflow

```bash
# Stop services (keep data)
docker compose down

# Or use script
bash docker-stop.sh
```

### Delete completely (including database)

```bash
docker compose down -v
```

### Restart

```bash
docker compose restart
```

## Access MongoDB

### Using MongoDB Compass (GUI)
```
Connection String: mongodb://admin:admin123@localhost:27017/
Database: arxiv_db
Collection: papers
```
## Using DAGs

1. Go to http://localhost:8080
2. Login with `admin`/`admin`
3. Find DAG `arxiv_paper_scraper`
4. Turn on the toggle to activate DAG
5. Click "Trigger DAG" to run manually or wait for it to run on a schedule


## 🔍 Data Cleaning Details

### Processing Steps:

1. **Remove Duplicates**: Remove papers with the same ID

2. **String Normalization**:
- Remove extra spaces
- Remove invalid special characters
- Trim whitespace
3. **Missing Values**: Replace empty strings with None
4. **URL Validation**: Check the validity of PDF URLs
5. **Date Formatting**: Ensure the format is YYYY-MM-DD
6. **Critical Fields Check**: Remove papers missing ID or title
7. **Quality Flag**: Add `data_quality` flag for tracking

## 📊 View output data

Data is saved in the folder `tmp/arxiv_data/`:
```bash
# List files
ls -la tmp/arxiv_data/

# View CSV
cat tmp/arxiv_data/arxiv_papers_*.csv
```

Check the logs of each task in Airflow UI:
- `clean_data`: View statistics about data cleaning
- `save_to_mongodb`: View the number of papers inserted/updated

Using MongoDB Compass to check data
## Troubleshooting

### Error: "Cannot connect to the Docker daemon"

Make sure Docker Desktop is running.

### Error: "Port 8080 already in use"

Change port in `docker-compose.yaml`:
```yaml
ports:
- "8081:8080" # Change 8080 to 8081
```

### Error: "Permission denied" on Linux/macOS

```bash
# Set permissions for script
chmod +x docker-start.sh docker-stop.sh
```

### DAG not appearing in UI

```bash
# Check logs
docker compose logs airflow-scheduler

# Restart scheduler
docker compose restart airflow-scheduler
```

### Want to delete database and start over

```bash
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

## Security

**Important Important**: Change the admin password in the `.env` file before deploying to production:

```env
AIRFLOW_ADMIN_USERNAME=your_username
AIRFLOW_ADMIN_PASSWORD=strong_password_here
AIRFLOW_ADMIN_EMAIL=your_email@domain.com
```

Then rebuild:
```bash
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

## 📚 Additional documents

- [Airflow Docker Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)