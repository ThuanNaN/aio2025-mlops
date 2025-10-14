

## 🚀 Tính năng

- **Lên lịch tự động**: Chạy hàng ngày để cào dữ liệu mới nhất
- **Tìm kiếm linh hoạt**: Có thể tùy chỉnh từ khóa tìm kiếm
- **Lưu trữ dữ liệu**: Xuất dữ liệu ra file CSV với timestamp
- **Thống kê**: Tạo file summary với thống kê categories
- **Monitoring**: Logging chi tiết để theo dõi quá trình

## 📁 Cấu trúc thư mục

```
AirflowSimple/
├── dags/
│   ├── arxiv_scraper_dag.py    # DAG chính của Airflow
│   └── arxiv_scraper.py        # Module cào dữ liệu
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker image definition
├── docker-compose.yaml         # Docker services configuration
├── .dockerignore               # Files to ignore in Docker build
├── docker-start.sh             # Script khởi động Docker
├── docker-stop.sh              # Script dừng Docker
├── DOCKER_SETUP.md             # Hướng dẫn chi tiết Docker
└── README.md                   # Hướng dẫn này
```

## 🛠️ Setup

### 🐳 Cách 1: Chạy với Docker (Khuyến nghị cho Windows)

Docker giúp tránh các vấn đề về môi trường và dependencies trên Windows.

**Xem hướng dẫn chi tiết:** [DOCKER_SETUP.md](DOCKER_SETUP.md)

```bash
# 1. Tạo file .env với nội dung sau:
# AIRFLOW_UID=50000
# AIRFLOW_IMAGE_NAME=apache/airflow:2.7.3-python3.11
# POSTGRES_USER=airflow
# POSTGRES_PASSWORD=airflow
# POSTGRES_DB=airflow
# AIRFLOW_ADMIN_USERNAME=admin
# AIRFLOW_ADMIN_PASSWORD=admin
# AIRFLOW_ADMIN_EMAIL=admin@example.com

# 2. Build và khởi động
docker compose build
docker compose up airflow-init
docker compose up -d

# 3. Truy cập Web UI
# http://localhost:8080
# Username: admin / Password: admin
```

### 💻 Cách 2: Cài đặt trực tiếp (Linux/macOS hoặc WSL2)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Init Airflow store

```bash
# Create folder Airflow
mkdir airflow

# Init database for Airflow
airflow db init

# Create User (admin)
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password "YourPass123!"

# Create User (PowerShell)
airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password "YourPass123!"

```

### 3. Start Airflow

```bash
# Terminal 1: Start webserver
airflow webserver --port 8080

# Terminal 2: Start scheduler
airflow scheduler
```

### 4. Access Airflow UI

Access in browser: http://localhost:8080

- Username: admin
- Password: in Step 2

## 📊 How to use

### 1. Kích hoạt DAG

1. Truy cập Airflow UI
2. Tìm DAG tên `arxiv_paper_scraper`
3. Bật toggle để kích hoạt DAG
4. DAG sẽ tự động chạy theo lịch (hàng ngày)

### 2. Tùy chỉnh tham sốs

Trong file `dags/arxiv_scraper_dag.py`, bạn có thể thay đổi:

```python
# Từ khóa tìm kiếm
'query': 'machine learning',  # Thay đổi từ khóa ở đây

# Số lượng papers tối đa
'max_results': 50,  # Thay đổi số lượng ở đây

# Thư mục lưu dữ liệu
'output_dir': '/tmp/arxiv_data'  # Thay đổi đường dẫn ở đây
```

### 3. Chạy thủ công

Bạn có thể chạy DAG thủ công bằng cách:
1. Click vào DAG name
2. Click nút "Trigger DAG"

## 📈 Dữ liệu đầu ra

### File CSV
Dữ liệu được lưu trong file CSV với format:
- `arxiv_papers_YYYYMMDD_HHMMSS.csv`

Các cột bao gồm:
- `id`: ArXiv ID của paper
- `title`: Tiêu đề paper
- `authors`: Danh sách tác giả
- `abstract`: Tóm tắt
- `published`: Ngày xuất bản
- `updated`: Ngày cập nhật cuối
- `categories`: Danh mục (cs.AI, cs.LG, etc.)
- `pdf_url`: Link tải PDF
- `doi`: DOI của paper
- `scraped_at`: Thời gian cào dữ liệu

### File Summary
File text với thống kê:
- `summary_YYYYMMDD_HHMMSS.txt`

## 🔧 Tùy chỉnh nâng cao

### Thay đổi lịch chạy

```python
# Trong arxiv_scraper_dag.py
schedule_interval=timedelta(days=1),  # Hàng ngày
# Hoặc
schedule_interval='0 6 * * *',  # 6h sáng hàng ngày (cron format)
```

### Thêm từ khóa tìm kiếm phức tạp

```python
# Ví dụ tìm kiếm papers về deep learning trong năm 2024
'query': 'cat:cs.LG AND submittedDate:[20240101 TO 20241231]'
```

### Lưu dữ liệu vào database

Bạn có thể mở rộng để lưu vào database thay vì CSV:

```python
# Thêm vào arxiv_scraper.py
import sqlite3

def save_to_database(papers, db_path):
    conn = sqlite3.connect(db_path)
    df = pd.DataFrame(papers)
    df.to_sql('arxiv_papers', conn, if_exists='append', index=False)
    conn.close()
```
