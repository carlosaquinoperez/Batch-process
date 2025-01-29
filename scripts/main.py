import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Database configuration
DB_HOST = "airflow-db"
DB_NAME = "data_pipeline_db"
DB_USER = "root"
DB_PASS = "root"

# Connect to PostgreSQL
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}")
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=5432
)
cursor = conn.cursor()

# Initialize statistics
row_count = 0
price_min = float("inf")
price_max = float("-inf")
price_sum = 0

def process_csv(file_path):
    """
    Process a single CSV file and load data into the database while updating statistics.
    """
    global row_count, price_min, price_max, price_sum

    # Read CSV in chunks
    for chunk in pd.read_csv(file_path, chunksize=100):
        for _, row in chunk.iterrows():
            # Replace non-numeric or null values in 'price' with 0
            price = row["price"] if pd.notna(row["price"]) and isinstance(row["price"], (int, float)) else 0
            
            # Insert row into the database
            cursor.execute(
                "INSERT INTO public.transactions (timestamp, price, user_id) VALUES (%s, %s, %s)",
                (row["timestamp"], price, row["user_id"]),
            )

            # Update statistics
            row_count += 1
            price_min = min(price_min, price)
            price_max = max(price_max, price)
            price_sum += price

    conn.commit()
    print(
        f"Processed {file_path} | Rows: {row_count} | Min: {price_min} | Max: {price_max} | "
        f"Avg: {price_sum / row_count if row_count > 0 else 'NaN'}"
    )

def query_db_statistics():
    """
    Query the database to get the total count, average, minimum, and maximum price.
    """
    cursor.execute(
        "SELECT COUNT(*) as total_rows, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price FROM public.transactions"
    )
    result = cursor.fetchone()
    print(
        f"Database Statistics: Rows: {result[0]}, "
        f"Avg: {result[1] if result[1] is not None else 'NaN'}, "
        f"Min: {result[2] if result[2] is not None else 'NaN'}, "
        f"Max: {result[3] if result[3] is not None else 'NaN'}"
    )

def process_all_csv(data_dir):
    """
    Iterate through all CSV files in the data directory (excluding validation.csv)
    and process them sequentially.
    """
    csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".csv") and f != "validation.csv"])
    
    for file in csv_files:
        print(f"Processing file: {file}")
        process_csv(os.path.join(data_dir, file))
        query_db_statistics()  # Query database after each CSV is processed

if __name__ == "__main__":
    # Specify the directory containing the CSV files
    data_dir = "/opt/airflow/dags/data"  # Adjust this path as necessary

    # Process all files except validation.csv
    process_all_csv(data_dir)

    # Process validation.csv separately
    validation_file = os.path.join(data_dir, "validation.csv")
    if os.path.exists(validation_file):
        print(f"Processing validation file: {validation_file}")
        process_csv(validation_file)
        query_db_statistics()  # Query database after processing validation.csv
