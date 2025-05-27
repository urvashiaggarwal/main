import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MySQL
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    connection_timeout=5,
    use_pure=True
)

# SQL JOIN query with deduplicated 99acres column
query = """
SELECT 
    a.index_value,
    a.data_point_name,
    a.value_99acres AS value_99acres,
    a.c1, a.c2, a.c3,
    b.primary_source,
    b.secondary_source,
    a.score AS audit_score,a.den,
    a.consensus_value,
    a.consensus_score,
    b.score AS bible_score
FROM audit_data a
JOIN bible_data b
    ON a.index_value = b.index_value AND a.data_point_name = b.data_point_name
"""

# Load into DataFrame
df = pd.read_sql(query, conn)

# Save to CSV
df.to_csv("joined_audit_bible.csv", index=False, encoding="utf-8-sig")

conn.close()
print("Exported joined data to 'joined_audit_bible.csv'")
