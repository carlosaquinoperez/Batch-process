import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Configuration for connecting to the PostgreSQL database
DB_HOST = "airflow-db"
DB_NAME = "data_pipeline_db"
DB_USER = "root"
DB_PASS = "root"

# Create a connection to the PostgreSQL database using SQLAlchemy
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}")
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=5432
)

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Initialize variables to track statistics
row_count = 0
price_min = float("inf")
price_max = float("-inf")
price_sum = 0

def process_csv(file_path):
    """
    Process a single CSV file:
    - Reads the file in chunks to handle large datasets.
    - Inserts rows into the database table.
    - Dynamically updates statistics (row count, minimum, maximum, and average price).
    
    Parameters:
    file_path (str): Path to the CSV file to be processed.
    """
    global row_count, price_min, price_max, price_sum

    # Read CSV in chunks
    for chunk in pd.read_csv(file_path, chunksize=100):
        for _, row in chunk.iterrows():
            # Ensure the "price" field is valid; replace invalid or missing values with 0
            price = row["price"] if pd.notna(row["price"]) and isinstance(row["price"], (int, float)) else 0
            
            # Insert the data into the "transactions" table
            cursor.execute(
                "INSERT INTO public.transactions (timestamp, price, user_id) VALUES (%s, %s, %s)",
                (row["timestamp"], price, row["user_id"]),
            )

            # Update running statistics
            row_count += 1
            price_min = min(price_min, price)
            price_max = max(price_max, price)
            price_sum += price

    # Commit the transaction to save changes to the database
    conn.commit()
    # Print the updated statistics for this file
    print(
        f"Processed {file_path} | Rows: {row_count} | Min: {price_min} | Max: {price_max} | "
        f"Avg: {price_sum / row_count if row_count > 0 else 'NaN'}"
    )

def query_db_statistics():
    """
    Query the database to retrieve current statistics:
    - Total row count.
    - Average price.
    - Minimum price.
    - Maximum price.
    """
    cursor.execute(
        "SELECT COUNT(*) as total_rows, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price FROM public.transactions"
    )
    result = cursor.fetchone()
    # Print the statistics retrieved from the database
    print(
        f"Database Statistics: Rows: {result[0]}, "
        f"Avg: {result[1] if result[1] is not None else 'NaN'}, "
        f"Min: {result[2] if result[2] is not None else 'NaN'}, "
        f"Max: {result[3] if result[3] is not None else 'NaN'}"
    )

def process_all_csv(data_dir):
    """
    Process all CSV files in the specified directory:
    - Excludes the "validation.csv" file.
    - Updates statistics dynamically after each file is processed.
    
    Parameters:
    data_dir (str): Path to the directory containing CSV files.
    """

    # List and sort all CSV files in the directory, excluding "validation.csv"
    csv_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".csv") and f != "validation.csv"])
    
    # Process each file sequentially
    for file in csv_files:
        print(f"Processing file: {file}")
        process_csv(os.path.join(data_dir, file))
        query_db_statistics()  # Query database after each CSV is processed

if __name__ == "__main__":
    """
    Main execution block:
    - Processes all CSV files except "validation.csv".
    - Processes "validation.csv" separately to observe its effect on statistics.
    """

    # Directory where the CSV files are stored
    data_dir = "/opt/airflow/dags/data"

    # Process all files except validation.csv
    process_all_csv(data_dir)

    # Process the "validation.csv" file, if it exists
    validation_file = os.path.join(data_dir, "validation.csv")
    if os.path.exists(validation_file):
        print(f"Processing validation file: {validation_file}")
        process_csv(validation_file)
        query_db_statistics()  # Query and print statistics after processing "validation.csv"
