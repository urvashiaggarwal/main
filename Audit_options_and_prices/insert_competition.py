import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

load_dotenv()

with open("Config.csv", "rb") as f:
    result = chardet.detect(f.read())
print(result)

# Load CSV
df = pd.read_csv("Config.csv", encoding="ISO-8859-1")

# Connect to DB
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()

# Get existing index_values from DB
cursor.execute("SELECT `index`, data_point_name FROM config_data")
existing = set((row[0], row[1]) for row in cursor.fetchall())

# Insert only new rows
insert_query = """
INSERT INTO config_data (`index`, data_point_name, 99acres, C1, C2, C3)
VALUES (%s, %s, %s, %s, %s, %s)
"""

inserted = 0
for _, row in df.iterrows():
    if pd.isna(row["Index"]) or pd.isna(row["data_point_name"]):
        continue  
    key = (int(row["Index"]), row["data_point_name"])
    if key not in existing:
        values = (
            int(row["Index"]),
            row["data_point_name"],
            row["99acres"],
            row["C1"],
            row["C2"],
            row["C3"],
           
        )
        cursor.execute(insert_query, values)
        inserted += 1

conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows.")
