import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv("Book1.csv")

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
cursor.execute("SELECT index_value, data_point_name FROM audit_data")
existing = set((row[0], row[1]) for row in cursor.fetchall())

# Insert only new rows
insert_query = """
INSERT INTO audit_data (index_value, data_point_name, value_99acres, c1, c2, c3, score, den, consensus_value, consensus_score)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            row.get("score") if not pd.isna(row.get("score")) else None,
            row.get("den") if not pd.isna(row.get("den")) else None,
            row.get("consensus_value") if not pd.isna(row.get("consensus_value")) else None,
            row.get("consensus_score") if not pd.isna(row.get("consensus_score")) else None,
        )
        cursor.execute(insert_query, values)
        inserted += 1

conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows.")
