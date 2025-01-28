import pandas as pd
import psycopg2

# Configuración de PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="data_pipeline_db",
    user="user",
    password="root"
)
cursor = conn.cursor()

# Cargar un archivo CSV
def load_csv_to_db(file_path):
    data = pd.read_csv(file_path)
    for _, row in data.iterrows():
        cursor.execute("""
            INSERT INTO transactions (timestamp, price, user_id)
            VALUES (%s, %s, %s)
        """, (row['timestamp'], row['price'], row['user_id']))
    conn.commit()

load_csv_to_db("./data/2012-1.csv")
cursor.close()
conn.close()
