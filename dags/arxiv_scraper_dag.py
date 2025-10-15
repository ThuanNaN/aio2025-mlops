from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os

# Import custom functions
from arxiv_scraper import scrape_arxiv_papers, clean_paper_data, save_to_csv, save_to_mongodb

# Default arguments cho DAG
default_args = {
    'owner': 'anhduong3',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 14),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'arxiv_paper_scraper',
    default_args=default_args,
    description='DAG to scrape papers from ArXiv API',
    schedule_interval=timedelta(days=1),  # Run daily
    catchup=False,
    tags=['arxiv', 'scraping', 'research'],
)

# Task 1: Create output directory if not exists
create_output_dir = BashOperator(
    task_id='create_output_directory',
    bash_command='mkdir -p /opt/airflow/tmp/arxiv_data',
    dag=dag,
)

# Task 2: Scrape data from ArXiv
scrape_papers = PythonOperator(
    task_id='scrape_arxiv_papers',
    python_callable=scrape_arxiv_papers,
    op_kwargs={
        'query': 'computer science',  # Search query
        'max_results': 10,  # Maximum number of papers
        'output_dir': '/opt/airflow/tmp/arxiv_data'
    },
    dag=dag,
)

# Task 3: Clean and process data
clean_data = PythonOperator(
    task_id='clean_data',
    python_callable=clean_paper_data,
    op_kwargs={},
    dag=dag,
)

# Task 4: Save cleaned data to CSV
save_data = PythonOperator(
    task_id='save_to_csv',
    python_callable=save_to_csv,
    op_kwargs={
        'output_dir': '/opt/airflow/tmp/arxiv_data'
    },
    dag=dag,
)

# Task 5: Save cleaned data to MongoDB
save_mongodb = PythonOperator(
    task_id='save_to_mongodb',
    python_callable=save_to_mongodb,
    op_kwargs={
        'db_name': 'arxiv_db',
        'collection_name': 'papers'
    },
    dag=dag,
)

# Task 6: Show data summary
show_summary = BashOperator(
    task_id='show_data_summary',
    bash_command='echo "✅ Data saved at: /opt/airflow/tmp/arxiv_data/" && ls -la /opt/airflow/tmp/arxiv_data/ && echo "\n Data also saved to MongoDB (arxiv_db.papers)"',
    dag=dag,
)

# Define the order of tasks
# After cleaning data, save to both CSV and MongoDB in parallel
create_output_dir >> scrape_papers >> clean_data >> [save_data, save_mongodb] >> show_summary

