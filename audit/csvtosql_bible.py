import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv("Book12.csv")

# Connect to MySQL
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()

# Fetch existing keys from bible_data
cursor.execute("SELECT index_value, data_point_name FROM bible_data")
existing_keys = set((row[0], row[1]) for row in cursor.fetchall())

insert_query = """
INSERT INTO bible_data (
    index_value, data_point_name, value_99acres,
    primary_source, secondary_source, score
) VALUES (%s, %s, %s, %s, %s, %s)
"""

# Insert new rows only
inserted = 0
for _, row in df.iterrows():
    if pd.isna(row["Index"]) or pd.isna(row["data_point_name"]):
        continue

    key = (int(row["Index"]), row["data_point_name"])
    if key not in existing_keys:
        values = (
            int(row["Index"]),
            row["data_point_name"],
            row.get("99acres") if not pd.isna(row.get("99acres")) else None,
            row.get("Primary") if not pd.isna(row.get("Primary")) else None,
            row.get("Secondary") if not pd.isna(row.get("Secondary")) else None,
            int(row.get("score")) if not pd.isna(row.get("score")) else None,
        )
        cursor.execute(insert_query, values)
        inserted += 1

conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows into bible_data.")
