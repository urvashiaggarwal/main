import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

load_dotenv()







with open("Config_bible.csv", "rb") as f:
    result = chardet.detect(f.read())
print(result)

# Load CSV
df = pd.read_csv("Config_bible.csv", encoding="ISO-8859-1")

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




cursor.execute("CREATE DATABASE IF NOT EXISTS audit")
cursor.execute("USE audit")

# Step 2: Create config_data table WITHOUT primary key
cursor.execute("""
CREATE TABLE IF NOT EXISTS bible_config_data (
    `index` INT,
    data_point_name VARCHAR(100),
    `99acres` TEXT,
    primary_source TEXT,
    ref_value TEXT,
    comparable_row TEXT,
    `option_matching_score` INT,
    `price_matching_score` INT
 
)
""")
# Get existing index_values from DB
cursor.execute("SELECT `index`, data_point_name FROM bible_config_data")
existing = set((row[0], row[1]) for row in cursor.fetchall())

# Insert only new rows
insert_query = """
INSERT INTO bible_config_data (`index`, data_point_name, 99acres, primary_source)
VALUES (%s, %s, %s, %s)
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
            row["Bible"],
           
        )
        cursor.execute(insert_query, values)
        inserted += 1

conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows.")
