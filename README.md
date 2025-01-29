
# Data Pipeline for Micro-Batch Processing with Airflow and PostgreSQL

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Setup and Installation](#setup-and-installation)
4. [Folder Structure](#folder-structure)
5. [Pipeline Execution](#pipeline-execution)
6. [Code Explanation](#code-explanation)
7. [Results](#results)
8. [License](#license)

---

## Introduction

This project demonstrates a data pipeline that processes CSV files in micro-batches using **Apache Airflow** and stores them in **PostgreSQL**. The pipeline calculates statistics (row count, minimum, maximum, average) dynamically and updates them after processing each file.

---

## Prerequisites

Before starting, ensure you have the following installed:

- **Docker**: Version 20.x or later
- **Docker Compose**: Version 1.29.x or later
- **Python**: Version 3.8 or later
- **Git**

---

## Setup and Installation

### Step 1: Clone the Repository

```bash
git clone <repository_url>
cd <repository_folder>
```

### Step 2: Setup Docker

Create a `docker-compose.yml` file in the project root with the following configuration:

```yaml
version: "3.8"
services:
  airflow-db:
    image: postgres:14
    container_name: airflow-db
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: data_pipeline_db
    ports:
      - "5433:5432"
    volumes:
      - airflow-db-data:/var/lib/postgresql/data

  airflow-webserver:
    image: apache/airflow:2.6.3
    container_name: airflow-webserver
    depends_on:
      - airflow-db
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://root:root@airflow-db:5432/data_pipeline_db
      AIRFLOW__CORE__LOAD_EXAMPLES: "False"
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    command: >
      bash -c "
      airflow db init &&
      airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin &&
      airflow webserver
      "

  airflow-scheduler:
    image: apache/airflow:2.6.3
    container_name: airflow-scheduler
    depends_on:
      - airflow-webserver
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://root:root@airflow-db:5432/data_pipeline_db
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    command: >
      bash -c "airflow scheduler"

volumes:
  airflow-db-data:
```

### Step 3: Start Docker Services

Run the following command to start all services:

```bash
sudo docker-compose up -d
```

---

## Folder Structure

```plaintext
Batch-process/
│
├── dags/
│   ├── data_pipeline_dag.py       # Airflow DAG definition
│   └── data/                      # Directory containing CSV files
│
├── scripts/
│   └── main.py                    # Main script for processing CSV files
│
├── logs/                          # Airflow logs
├── plugins/                       # Airflow plugins (if any)
├── docker-compose.yml             # Docker Compose configuration
└── README.md                      # Project documentation
```

---

## Pipeline Execution

### Step 1: Access Airflow UI

- Open your browser and navigate to `http://localhost:8080`.
- Log in using:
  - **Username**: `admin`
  - **Password**: `admin`

### Step 2: Trigger the DAG

- Locate the `data_pipeline_dag` in the Airflow UI.
- Trigger the DAG manually by clicking the "play" button.

---

## Code Explanation

### `main.py`

#### `process_csv(file_path)`
This function processes a single CSV file and inserts its data into the PostgreSQL database. It also updates statistics dynamically.

```python
def process_csv(file_path):
    for chunk in pd.read_csv(file_path, chunksize=100):
        for _, row in chunk.iterrows():
            cursor.execute(
                "INSERT INTO public.transactions (timestamp, price, user_id) VALUES (%s, %s, %s)",
                (row["timestamp"], row["price"], row["user_id"]),
            )
```

#### `query_db_statistics()`
This function queries the database for statistics like row count, average, minimum, and maximum price.

```python
def query_db_statistics():
    cursor.execute(
        "SELECT COUNT(*), AVG(price), MIN(price), MAX(price) FROM public.transactions"
    )
    result = cursor.fetchone()
    print(f"Rows: {result[0]}, Avg: {result[1]}, Min: {result[2]}, Max: {result[3]}")
```

### `data_pipeline_dag.py`

Defines the DAG for processing CSV files in sequence, followed by the validation file.

---

## Results

Here is an example output during pipeline execution:

```plaintext
Processed /opt/airflow/dags/data/2012-1.csv | Rows: 50 | Min: 10 | Max: 100 | Avg: 55.0
Processed /opt/airflow/dags/data/validation.csv | Rows: 150 | Min: 10 | Max: 110 | Avg: 60.5
Database Statistics: Rows: 200, Avg: 58.2, Min: 10, Max: 110
```

---

## License

This project is licensed under the MIT License by Carlos.
