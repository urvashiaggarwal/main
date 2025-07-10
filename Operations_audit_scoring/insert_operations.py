# import pandas as pd
# import mysql.connector
# import os
# from dotenv import load_dotenv
# import chardet

# load_dotenv()

# # Detect CSV encoding
# with open("op.csv", "rb") as f:
#     result = chardet.detect(f.read())
# encoding = result['encoding']
# print(f"Detected CSV encoding: {encoding}")

# # Load CSV
# df = pd.read_csv("op.csv", encoding="ISO-8859-1")  # or use the detected encoding

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

# # Get existing index_values and data_point_name from DB to prevent duplicates
# cursor.execute("SELECT index_value, data_point_name FROM op_audit_data")
# existing = set((row[0], row[1]) for row in cursor.fetchall())

# # Prepare insert query
# insert_query = """
# INSERT INTO op_audit_data (
#     index_value,
#     data_point_name,
#     value_99acres,
#     c1,
#     c2,
#     c3,
#     ref_normalised,
#     c1_normalised,
#     c2_normalised,
#     c3_normalised,
#     is_scored
# )
# VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
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
#             row.get("99acres", None),
#             row.get("C1", None),
#             row.get("C2", None),
#             row.get("C3", None),
#             None,  # ref_normalised
#             None,  # c1_normalised
#             None,  # c2_normalised
#             None   # c3_normalised
#         )
#         cursor.execute(insert_query, values)
#         inserted += 1

# # Commit and close connection
# conn.commit()
# cursor.close()
# conn.close()

# print(f"Inserted {inserted} new rows.")






































import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

load_dotenv()

# Detect CSV encoding
with open("op.csv", "rb") as f:
    result = chardet.detect(f.read())
encoding = result['encoding']
print(f"Detected CSV encoding: {encoding}")

# Load CSV
df = pd.read_csv("op.csv", encoding=encoding)

# Connect to MySQL server (without selecting a database yet)
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()

# Create 'audit' database if not exists, then use it
cursor.execute("CREATE DATABASE IF NOT EXISTS audit")
cursor.execute("USE audit")

# Create op_audit_data table with full schema if not exists
create_table_query = """
CREATE TABLE IF NOT EXISTS op_audit_data (
    index_value INT NOT NULL,
    data_point_name VARCHAR(70) NOT NULL,
    value_99acres VARCHAR(150),
    c1 TEXT,
    c2 TEXT,
    c3 TEXT,
    ref_normalised VARCHAR(150),
    c1_normalised VARCHAR(150),
    c2_normalised VARCHAR(150),
    c3_normalised VARCHAR(150),
    is_scored TINYINT(4) DEFAULT 0,
    score INT,
    consensus_value VARCHAR(150),
    consensus_score INT,
    den INT,
    PRIMARY KEY (index_value, data_point_name)
)
"""
cursor.execute(create_table_query)

# Fetch existing composite keys
cursor.execute("SELECT index_value, data_point_name FROM op_audit_data")
existing = set((row[0], row[1]) for row in cursor.fetchall())

# Prepare insert query
insert_query = """
INSERT INTO op_audit_data (
    index_value,
    data_point_name,
    value_99acres,
    c1,
    c2,
    c3,
    ref_normalised,
    c1_normalised,
    c2_normalised,
    c3_normalised,
    is_scored
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
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
            row.get("C1", None),
            row.get("C2", None),
            row.get("C3", None),
            None,  # ref_normalised
            None,  # c1_normalised
            None,  # c2_normalised
            None   # c3_normalised
        )
        cursor.execute(insert_query, values)
        inserted += 1

# Finalize
conn.commit()
cursor.close()
conn.close()

print(f"Inserted {inserted} new rows.")
