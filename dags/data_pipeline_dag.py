"""
This DAG processes CSV files in micro-batches, calculates statistics
(row count, min, max, avg), and updates them dynamically as files are processed.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os

# Add the 'scripts' folder to the system PATH to make modules accessible
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scripts"))

# Import required functions from main.py
from main import process_csv  # Import the method from main.py
from main import query_db_statistics  # Import the statistics query function

# Default arguments applied to all tasks in the DAG
default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

# Directory containing the CSV files to process
DATA_DIR = "/opt/airflow/dags/data"

# Validate the existence of the data directory and ensure it is not empty
if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
    raise ValueError(f"Data directory {DATA_DIR} does not exist or is empty.")

# Define the DAG
with DAG(
    dag_id="data_pipeline_dag", # Unique identifier for the DAG
    default_args=default_args, # Apply default arguments
    schedule_interval=None, # No automatic scheduling; run manually
    catchup=False, # Avoid running past dates that were missed
) as dag:

    # List to store dynamically created tasks for each CSV file
    tasks = []

    # Dynamically create a PythonOperator for each CSV file (excluding "validation.csv")
    for file_name in sorted(os.listdir(DATA_DIR)):
        if file_name.endswith(".csv") and file_name != "validation.csv":
            task = PythonOperator(
                task_id=f"process_{file_name.replace('.', '_')}", # Unique task ID based on file name
                python_callable=process_csv, # Function to call for processing the CSV
                op_kwargs={"file_path": os.path.join(DATA_DIR, file_name)}, # Pass the file path as an argument
            )
            tasks.append(task) # Add the task to the list of dynamically created tasks

    # Define a task to process the "validation.csv" file
    process_validation = PythonOperator(
        task_id="process_validation_csv",
        python_callable=process_csv,
        op_kwargs={"file_path": os.path.join(DATA_DIR, "validation.csv")},
    )

    # Define a task to log the final statistics after all files are processed
    log_statistics = PythonOperator(
    task_id="log_final_statistics",
    python_callable=query_db_statistics, # Function to call for logging statistics
    )

    # Set the task dependencies:
    # - Process all regular CSV files first.
    # - Then process "validation.csv".
    # - Finally, log the final statistics.
    if tasks:
        tasks[-1] >> process_validation >> log_statistics