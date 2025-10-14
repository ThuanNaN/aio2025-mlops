FROM apache/airflow:2.7.3-python3.11

# Copy và cài đặt dependencies
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# Set working directory
WORKDIR /opt/airflow

