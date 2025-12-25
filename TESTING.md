# 🧪 Testing Instructions

## **Prerequisites**

1. ✅ All code changes implemented
2. ✅ CoinPaprika API key added to `.env` file
3. ✅ Docker Desktop installed and running
4. ✅ Virtual environment activated (for local testing)

---

## **🔹 Step 1: Generate Sample CSV Data**

```powershell
# Navigate to project root
cd C:\Users\bossu\OneDrive\Desktop\assignment\backend-etl-system

# Activate virtual environment
venv\Scripts\activate

# Generate sample CSV
python scripts\generate_sample_csv.py
```

**Expected Output:**
```
✅ Sample CSV created successfully!
📁 Location: data\crypto_data.csv
📊 Total rows: 10
```

**Verify CSV file exists:**
```powershell
Get-Content data\crypto_data.csv | Select-Object -First 5
```

---

## **🔹 Step 2: Test Locally (Without Docker)**

### **2.1 Install Dependencies**

```powershell
# Make sure venv is activated
pip install -r requirements.txt
pip install -e .
```

### **2.2 Run the Application**

```powershell
uvicorn src.main:app --reload
```

**Expected startup logs:**
```
🚀 Crypto ETL Backend System Starting...
📦 Version: 2.0.0
✨ Features: CSV + API Ingestion, Normalization, Auto-Start ETL
🔗 Sources: CSV, CoinGecko, CoinPaprika
✅ Auto-ingested X records from CSV
✅ Auto-ingested Y records from CoinGecko
```

### **2.3 Test Health Endpoint**

**In a new PowerShell window:**

```powershell
(Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "data": {
    "total_records": 150
  },
  "features": {
    "csv_ingestion": true,
    "api_ingestion": true,
    "normalization": true,
    "deduplication": true,
    "auto_ingest": true
  }
}
```

### **2.4 Test CSV Ingestion**

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/csv?limit=10" -Method POST -UseBasicParsing | Select-Object -Expand Content
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Ingested 10 records from CSV",
  "count": 10,
  "normalized": true,
  "total_unique_coins": 160
}
```

### **2.5 Test Data Retrieval**

```powershell
# Get first 5 records
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data?page=1&page_size=5" -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Verify:**
- ✅ Records have `canonical_id` field
- ✅ No duplicate coins (same symbol appears only once)
- ✅ Data from multiple sources

### **2.6 Test Statistics**

```powershell
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/stats" -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Verify:**
- ✅ `total_coins` matches unique count
- ✅ `top_gainers` and `top_losers` present
- ✅ Market cap and volume calculated

---

## **🔹 Step 3: Test with Docker**

### **3.1 Stop Local Server**

Press `Ctrl+C` in the terminal running uvicorn

### **3.2 Build and Start Docker Services**

```powershell
# Using PowerShell script (recommended)
.\run.ps1 build
.\run.ps1 up

# OR using docker-compose directly
docker-compose build
docker-compose up -d
```

**Expected Output:**
```
✅ Building Docker images...
✅ Starting services...
📍 API: http://localhost:8000
📖 Docs: http://localhost:8000/docs
```

### **3.3 Check Service Status**

```powershell
.\run.ps1 status

# OR
docker-compose ps
```

**Expected:**
```
NAME                   STATUS       PORTS
crypto-etl-backend    Up 30 sec    0.0.0.0:8000->8000/tcp
crypto-etl-db         Up 30 sec    0.0.0.0:5432->5432/tcp
```

### **3.4 View Logs**

```powershell
.\run.ps1 logs

# OR
docker-compose logs -f backend
```

**Look for:**
```
🚀 Crypto ETL Backend System Starting...
✅ Auto-ingested X records from CSV
✅ Auto-ingested Y records from CoinGecko
✅ Auto-ingested Z records from CoinPaprika
🎉 Auto-ingest completed: 150 unique coins stored
```

### **3.5 Test Auto-Ingestion Worked**

```powershell
(Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing).Content | ConvertFrom-Json
```

**Verify:**
- ✅ `total_records > 0` (data was auto-ingested)
- ✅ `last_updated` is recent
- ✅ All features are `true`

### **3.6 Test PostgreSQL Connection**

```powershell
# Connect to PostgreSQL
docker exec -it crypto-etl-db psql -U crypto_user -d crypto_etl

# Inside PostgreSQL shell:
\dt                           # List tables
SELECT * FROM cryptocurrencies LIMIT 5;
SELECT * FROM source_mappings LIMIT 5;
\q                           # Exit
```

---

## **🔹 Step 4: Test All Endpoints**

### **Option A: Use Interactive API Docs (Recommended)**

1. Open browser: **http://localhost:8000/docs**
2. Test each endpoint:
   - `GET /health` → Click "Try it out" → "Execute"
   - `POST /api/v1/ingest/csv` → Try it out
   - `POST /api/v1/ingest/coingecko` → Try it out
   - `POST /api/v1/ingest/coinpaprika` → Try it out
   - `POST /api/v1/ingest/all` → Try it out
   - `GET /api/v1/data` → Try with filters
   - `GET /api/v1/stats` → View statistics

### **Option B: Use PowerShell Commands**

```powershell
# Test CSV ingestion
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/csv" -Method POST -UseBasicParsing

# Test CoinGecko ingestion
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/coingecko?limit=50" -Method POST -UseBasicParsing

# Test CoinPaprika ingestion
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/coinpaprika?limit=30" -Method POST -UseBasicParsing

# Test ingest all
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/all" -Method POST -UseBasicParsing

# Get data with filters
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data?source=csv&page_size=5" -UseBasicParsing
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data?symbol=BTC" -UseBasicParsing

# Get statistics
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/stats" -UseBasicParsing
```

---

## **🔹 Step 5: Test Normalization & Deduplication**

### **5.1 Ingest from Multiple Sources**

```powershell
# Clear existing data and ingest from all sources
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/all" -Method POST -UseBasicParsing
```

### **5.2 Verify Deduplication**

```powershell
# Get all Bitcoin records
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data?symbol=BTC" -UseBasicParsing).Content | ConvertFrom-Json
```

**Expected:**
- ✅ Only ONE Bitcoin record (despite multiple sources)
- ✅ Record has `canonical_id: "btc"`
- ✅ Source is highest priority (coingecko > coinpaprika > csv)

### **5.3 Check Total Unique Coins**

```powershell
$response = (Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data" -UseBasicParsing).Content | ConvertFrom-Json
$response.total
```

**Expected:**
- ✅ Count is less than (CSV records + CoinGecko records + CoinPaprika records)
- ✅ Proves deduplication is working

---

## **🔹 Step 6: Run Automated Tests**

### **6.1 Run Tests Locally**

```powershell
# Activate venv
venv\Scripts\activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage
start htmlcov\index.html
```

### **6.2 Run Tests in Docker**

```powershell
.\run.ps1 test

# OR
docker-compose run --rm backend pytest -v
```

**Expected:**
```
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_get_data_empty PASSED
==================== 2 passed in 0.45s ====================
```

---

## **🔹 Step 7: Verify All Critical Gates PASS**

### **✅ Module 0.1 - CSV Gate**
```powershell
# Test CSV ingestion
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/ingest/csv" -Method POST -UseBasicParsing
```
**Pass criteria:** CSV data ingested successfully

### **✅ Module 0.2 - Hardcoded Secrets Gate**
```powershell
# Check .env is not in git
git status
```
**Pass criteria:** `.env` in `.gitignore`, not tracked

### **✅ Module 0.3 - Deployment Gate**
**Pass criteria:** Will deploy to Render/Railway after testing

### **✅ Module 0.4 - Executable System Gate**
```powershell
# Verify multi-stage Dockerfile
Get-Content Dockerfile | Select-String "FROM python" 

# Verify PostgreSQL in docker-compose
docker-compose ps
```
**Pass criteria:** 
- ✅ Multi-stage Dockerfile (2 FROM statements)
- ✅ PostgreSQL service running
- ✅ Auto-ingest on startup (check logs)

### **✅ Module 2 - Normalization Gate**
```powershell
# Check for canonical_id in data
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/data?page_size=1" -UseBasicParsing).Content | ConvertFrom-Json
```
**Pass criteria:**
- ✅ Records have `canonical_id` field
- ✅ No duplicates (BTC appears only once)

---

## **🔹 Step 8: Cleanup**

### **Stop Services**
```powershell
.\run.ps1 down

# OR
docker-compose down
```

### **Clean Everything (Including Volumes)**
```powershell
.\run.ps1 clean

# OR
docker-compose down -v
```

---

## **✅ Success Criteria Checklist**

- [ ] CSV file generated successfully
- [ ] Local server starts without errors
- [ ] Auto-ingest works on startup
- [ ] All 3 data sources ingest successfully
- [ ] Health endpoint returns `status: "healthy"`
- [ ] Data has `canonical_id` field
- [ ] No duplicate coins (same symbol only once)
- [ ] PostgreSQL service running
- [ ] Docker services start successfully
- [ ] Multi-stage Dockerfile builds
- [ ] Tests pass
- [ ] API documentation accessible at `/docs`

---

## **🐛 Troubleshooting**

### **CSV file not found**
```powershell
python scripts\generate_sample_csv.py
```

### **Port 8000 already in use**
```powershell
# Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### **PostgreSQL connection error**
```powershell
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### **Module import errors**
```powershell
# Reinstall in development mode
pip install -e .
```

---

## **📊 Next Steps After Testing**

1. ✅ All tests pass → Deploy to Render/Railway
2. ✅ Push to GitHub
3. ✅ Create deployment documentation
4. ✅ Submit assignment with live URLs

---

**Need help? Check logs:**
```powershell
# Local logs
# (visible in terminal where uvicorn is running)

# Docker logs
.\run.ps1 logs
```
