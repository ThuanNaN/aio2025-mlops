# 🐳 Chạy Airflow với Docker

Hướng dẫn này giúp bạn chạy Airflow ArXiv Scraper bằng Docker trên Windows (hoặc bất kỳ hệ điều hành nào).

## ✅ Yêu cầu

- Docker Desktop (đã cài đặt và đang chạy)
- Docker Compose (đi kèm với Docker Desktop)
- Git Bash hoặc WSL2 (để chạy script .sh)

## 🚀 Khởi động nhanh

### Cách 1: Sử dụng script tự động (Linux/macOS/Git Bash)

```bash
# Chạy script khởi động
bash docker-start.sh
```

### Cách 2: Khởi động thủ công (PowerShell/CMD)

```bash
# 1. Tạo file .env (copy từ template)
# Tạo file .env với nội dung sau:
```

Nội dung file `.env`:
```env
# Airflow configuration
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
# 2. Tạo thư mục cần thiết
mkdir logs
mkdir plugins
mkdir -p tmp/arxiv_data

# 3. Build Docker image
docker compose build

# 4. Khởi tạo database
docker compose up airflow-init

# 5. Khởi động services
docker compose up -d
```

## 🌐 Truy cập Airflow

Sau khi khởi động thành công:

- **Web UI**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`

## 📋 Các lệnh quản lý

### Xem logs

```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs của một service cụ thể
docker compose logs -f airflow-webserver
docker compose logs -f airflow-scheduler
```

### Dừng Airflow

```bash
# Dừng các services (giữ lại data)
docker compose down

# Hoặc dùng script
bash docker-stop.sh
```

### Xóa hoàn toàn (bao gồm database)

```bash
docker compose down -v
```

### Khởi động lại

```bash
docker compose restart
```

### Rebuild image sau khi thay đổi requirements.txt

```bash
docker compose build --no-cache
docker compose up -d
```

## 🔧 Cấu trúc Docker

### Dockerfile

Build image từ `apache/airflow:2.7.3-python3.11` và cài thêm các dependencies trong `requirements.txt`:
- arxiv
- pandas
- numpy
- requests
- Flask-Session (quan trọng cho webserver)

### docker-compose.yaml

Chạy 4 services chính:
1. **postgres**: Database cho Airflow metadata
2. **airflow-webserver**: Web UI
3. **airflow-scheduler**: Lên lịch và trigger DAGs
4. **airflow-triggerer**: Xử lý deferrable tasks
5. **airflow-init**: Khởi tạo database và tạo admin user (chỉ chạy 1 lần)

### Volumes được mount

- `./dags` → `/opt/airflow/dags` - DAGs của bạn
- `./logs` → `/opt/airflow/logs` - Logs
- `./plugins` → `/opt/airflow/plugins` - Plugins (nếu có)
- `./tmp` → `/opt/airflow/tmp` - Dữ liệu output (arxiv_data)

## 🎯 Sử dụng DAG

1. Truy cập http://localhost:8080
2. Đăng nhập với `admin`/`admin`
3. Tìm DAG `arxiv_paper_scraper`
4. Bật toggle để kích hoạt DAG
5. Click "Trigger DAG" để chạy thủ công hoặc chờ chạy theo lịch

## 📊 Xem dữ liệu output

Dữ liệu được lưu trong thư mục `tmp/arxiv_data/`:

```bash
# List files
ls -la tmp/arxiv_data/

# Xem CSV
cat tmp/arxiv_data/arxiv_papers_*.csv
```

## 🐛 Troubleshooting

### Lỗi: "Cannot connect to the Docker daemon"

Đảm bảo Docker Desktop đang chạy.

### Lỗi: "Port 8080 already in use"

Đổi port trong `docker-compose.yaml`:
```yaml
ports:
  - "8081:8080"  # Đổi 8080 thành 8081
```

### Lỗi: "Permission denied" trên Linux/macOS

```bash
# Set quyền cho script
chmod +x docker-start.sh docker-stop.sh
```

### DAG không xuất hiện trong UI

```bash
# Kiểm tra logs
docker compose logs airflow-scheduler

# Restart scheduler
docker compose restart airflow-scheduler
```

### Muốn xóa database và bắt đầu lại

```bash
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

## 🔐 Bảo mật

**Quan trọng**: Đổi mật khẩu admin trong file `.env` trước khi deploy production:

```env
AIRFLOW_ADMIN_USERNAME=your_username
AIRFLOW_ADMIN_PASSWORD=strong_password_here
AIRFLOW_ADMIN_EMAIL=your_email@domain.com
```

Sau đó rebuild:
```bash
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

## 📚 Tài liệu thêm

- [Airflow Docker Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

