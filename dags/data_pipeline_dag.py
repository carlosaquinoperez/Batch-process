"""
This DAG processes CSV files in micro-batches, calculates statistics
(row count, min, max, avg), and updates them dynamically as files are processed.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os

# Add the 'scripts' folder to the system PATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scripts"))

from main import process_csv  # Import the method from main.py
from main import query_db_statistics  # Import the statistics query function

default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

# Directory containing the CSV files
DATA_DIR = "/opt/airflow/dags/data"

# Validate the data directory
if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
    raise ValueError(f"Data directory {DATA_DIR} does not exist or is empty.")

with DAG(
    dag_id="data_pipeline_dag",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    # List to store dynamically created tasks
    tasks = []

    # Dynamically create tasks for each CSV file (excluding validation.csv)
    for file_name in sorted(os.listdir(DATA_DIR)):
        if file_name.endswith(".csv") and file_name != "validation.csv":
            task = PythonOperator(
                task_id=f"process_{file_name.replace('.', '_')}",
                python_callable=process_csv,
                op_kwargs={"file_path": os.path.join(DATA_DIR, file_name)},
            )
            tasks.append(task)

    # Task for processing the validation.csv file
    process_validation = PythonOperator(
        task_id="process_validation_csv",
        python_callable=process_csv,
        op_kwargs={"file_path": os.path.join(DATA_DIR, "validation.csv")},
    )

    # Task for logging the final statistics
    log_statistics = PythonOperator(
    task_id="log_final_statistics",
    python_callable=query_db_statistics,
    )

    # Set dependencies: Process all CSV files first, then process validation.csv
    if tasks:
        tasks[-1] >> process_validation >> log_statistics