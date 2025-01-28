import os
import pandas as pd
import psycopg2
from psycopg2 import sql

# Conexión a PostgreSQL
conn = psycopg2.connect(
    dbname="data_pipeline_db",
    user="user",
    password="root",
    host="localhost",
    port=5432
)
cursor = conn.cursor()

# Inicializar estadísticas en tiempo real
stats = {
    "row_count": 0,
    "price_sum": 0.0,
    "price_min": float("inf"),
    "price_max": float("-inf")
}

def update_statistics(new_data):
    """Actualizar estadísticas con nuevos datos."""
    global stats
    stats["row_count"] += len(new_data)
    stats["price_sum"] += new_data["price"].sum()
    stats["price_min"] = min(stats["price_min"], new_data["price"].min())
    stats["price_max"] = max(stats["price_max"], new_data["price"].max())

def print_statistics():
    """Imprimir estadísticas actuales."""
    print(f"Total Rows: {stats['row_count']}")
    print(f"Average Price: {stats['price_sum'] / stats['row_count']:.2f}")
    print(f"Min Price: {stats['price_min']}")
    print(f"Max Price: {stats['price_max']}")

# Procesar archivos en la carpeta
data_folder = "./data"
files = sorted([f for f in os.listdir(data_folder) if f.endswith(".csv") and "validation" not in f])

for file in files:
    print(f"Processing file: {file}")
    file_path = os.path.join(data_folder, file)
    
    # Cargar archivo CSV
    data = pd.read_csv(file_path)
    
    # Insertar datos en la base de datos
    for _, row in data.iterrows():
        cursor.execute(
            "INSERT INTO transactions (timestamp, price, user_id) VALUES (%s, %s, %s)",
            (row["timestamp"], row["price"], row["user_id"])
        )
        conn.commit()
    
    # Actualizar estadísticas en tiempo real
    update_statistics(data)
    
    # Imprimir estadísticas actuales
    print_statistics()

# Cerrar conexión
cursor.close()
conn.close()
