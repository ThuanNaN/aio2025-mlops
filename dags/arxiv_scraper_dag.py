from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os

# Import custom functions
from arxiv_scraper import scrape_arxiv_papers, save_to_csv

# Default arguments cho DAG
default_args = {
    'owner': 'anhduong',
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
        'query': 'machine learning',  # Search query
        'max_results': 50,  # Maximum number of papers
        'output_dir': '/opt/airflow/tmp/arxiv_data'
    },
    dag=dag,
)

# Task 3: Save data to CSV
save_data = PythonOperator(
    task_id='save_to_csv',
    python_callable=save_to_csv,
    op_kwargs={
        'output_dir': '/opt/airflow/tmp/arxiv_data'
    },
    dag=dag,
)

# Task 4: Show data summary
show_summary = BashOperator(
    task_id='show_data_summary',
    bash_command='echo "Data saved at: /opt/airflow/tmp/arxiv_data/" && ls -la /opt/airflow/tmp/arxiv_data/',
    dag=dag,
)

# Define the order of tasks
create_output_dir >> scrape_papers >> save_data >> show_summary

