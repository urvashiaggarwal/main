
import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

load_dotenv()

# Detect CSV encoding
with open("bible.csv", "rb") as f:
    result = chardet.detect(f.read())
encoding = result['encoding']
print(f"Detected CSV encoding: {encoding}")

# Load CSV
df = pd.read_csv("bible.csv", encoding=encoding)

# Connect to MySQL (no database selected initially)
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()

# Step 1: Create 'audit' database if not exists
cursor.execute("CREATE DATABASE IF NOT EXISTS audit")
cursor.execute("USE audit")

# Step 2: Create table if not exists
create_table_query = """
CREATE TABLE IF NOT EXISTS bible_op_data (
    `Index` INT NOT NULL,
    `data_point_name` VARCHAR(255) NOT NULL,
    `99acres` TEXT,
    `Primary` TEXT,
    `Secondary` TEXT,
    `ref_normalised` TEXT,
    `primary_normalised` TEXT,
    `secondary_normalised` TEXT,
    `is_scored` TINYINT DEFAULT 0,
    `score` INT,
    PRIMARY KEY (`Index`, `data_point_name`)
)
"""


cursor.execute(create_table_query)

# Step 3: Get existing keys
cursor.execute("SELECT `Index`, data_point_name FROM bible_op_data")
existing = set((row[0], row[1]) for row in cursor.fetchall())

# Step 4: Prepare insert query
insert_query = """
INSERT INTO bible_op_data (
    `Index`,
    `data_point_name`,
    `99acres`,
    `Primary`,
    `Secondary`,
    `ref_normalised`,
    `primary_normalised`,
    `secondary_normalised`,
    `is_scored`,
    `score`
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, NULL)
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
            row.get("99acres", None),
            row.get("Primary", None),
            row.get("Secondary", None),
            None,  # ref_normalised
            None,  # primary_normalised
            None   # secondary_normalised
        )
        cursor.execute(insert_query, values)
        inserted += 1

# Finalize
conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows.")
