# import pandas as pd
# import mysql.connector
# import os
# from dotenv import load_dotenv
# import chardet

# load_dotenv()

# with open("Config.csv", "rb") as f:
#     result = chardet.detect(f.read())
# print(result)

# # Load CSV
# df = pd.read_csv("Config.csv", encoding="ISO-8859-1")

# # Connect to DB
# conn = mysql.connector.connect(
#     host=os.getenv("MYSQL_HOST"),
#     user=os.getenv("MYSQL_USER"),
#     password=os.getenv("MYSQL_PASSWORD"),
#     database=os.getenv("MYSQL_DATABASE"),
#     connection_timeout=5,
#     use_pure=True
# )
# cursor = conn.cursor()

# # Get existing index_values from DB
# cursor.execute("SELECT `index`, data_point_name FROM config_data")
# existing = set((row[0], row[1]) for row in cursor.fetchall())

# # Insert only new rows
# insert_query = """
# INSERT INTO config_data (`index`, data_point_name, 99acres, C1, C2, C3)
# VALUES (%s, %s, %s, %s, %s, %s)
# """

# inserted = 0
# for _, row in df.iterrows():
#     if pd.isna(row["Index"]) or pd.isna(row["data_point_name"]):
#         continue  
#     key = (int(row["Index"]), row["data_point_name"])
#     if key not in existing:
#         values = (
#             int(row["Index"]),
#             row["data_point_name"],
#             row["99acres"],
#             row["C1"],
#             row["C2"],
#             row["C3"],
           
#         )
#         cursor.execute(insert_query, values)
#         inserted += 1

# conn.commit()
# cursor.close()
# conn.close()

# print(f"Inserted {inserted} new rows.")


















































import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

# Load environment variables
load_dotenv()

# Detect CSV encoding
with open("Config.csv", "rb") as f:
    result = chardet.detect(f.read())
print(f"Detected encoding: {result}")

# Load CSV
df = pd.read_csv("Config.csv", encoding=result["encoding"])

# Connect to MySQL without selecting DB (to allow creating if needed)
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()

# Step 1: Create audit DB if it does not exist
cursor.execute("CREATE DATABASE IF NOT EXISTS audit")
cursor.execute("USE audit")

# Step 2: Create config_data table WITHOUT primary key
cursor.execute("""
CREATE TABLE IF NOT EXISTS competition_config_data (
    `index` INT,
    data_point_name VARCHAR(100),
    `99acres` TEXT,
    C1 TEXT,
    C2 TEXT,
    C3 TEXT,
    `Sum-of_option_matching_score` INT,
    `Sum-of_price_matching_score` INT,
    v1 VARCHAR(20),
    v2 VARCHAR(20),
    v3 VARCHAR(20),
    comparable_source VARCHAR(100),
    comparable_row TEXT
)
""")

# Step 3: Prepare insert query
insert_query = """
INSERT INTO competition_config_data (
    `index`, data_point_name, `99acres`, C1, C2, C3,
    `Sum-of_option_matching_score`, `Sum-of_price_matching_score`,
    v1, v2, v3, comparable_source, comparable_row
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Step 4: Insert all rows (no deduplication since no primary key)
inserted = 0
for _, row in df.iterrows():
    if pd.isna(row["Index"]) or pd.isna(row["data_point_name"]):
        continue

    values = (
        int(row["Index"]),
        str(row["data_point_name"]).strip(),
        row.get("99acres"),
        row.get("C1"),
        row.get("C2"),
        row.get("C3"),
        int(row["Sum-of_option_matching_score"]) if pd.notna(row.get("Sum-of_option_matching_score")) else None,
        int(row["Sum-of_price_matching_score"]) if pd.notna(row.get("Sum-of_price_matching_score")) else None,
        row.get("v1"),
        row.get("v2"),
        row.get("v3"),
        row.get("comparable_source"),
        row.get("comparable_row")
    )
    cursor.execute(insert_query, values)
    inserted += 1

# Finalize
conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} rows.")
