import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet

load_dotenv()

# Detect CSV encoding
with open("amenities_bible_data.csv", "rb") as f:
    result = chardet.detect(f.read())
encoding = result['encoding']
print(f"Detected CSV encoding: {encoding}")

# Load CSV
df = pd.read_csv("amenities_bible_data.csv", encoding=encoding)

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


# 1. Create table if not exists
create_table_query = f'''
CREATE TABLE IF NOT EXISTS amenities_bible (
    id INT PRIMARY KEY,
    `99acres` TEXT,
    Brochure TEXT
)
'''
cursor.execute(create_table_query)

# 3. Insert data into table
insert_query = f"""
    INSERT INTO amenities_bible (id, `99acres`, Brochure)
    VALUES (%s, %s, %s)
    
"""

for _, row in df.iterrows():
    cursor.execute(insert_query, (int(row['Index']), str(row['99acres']), str(row['Brochure'])))
conn.commit()

cursor.close()
conn.close()
print(f'Table created and data inserted, total rows: {len(df)} successfully.')
 
