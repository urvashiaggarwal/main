import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv
import chardet
import re
load_dotenv()

# Detect CSV encoding
with open("amenities_competition.csv", "rb") as f:
    result = chardet.detect(f.read())
encoding = result['encoding']
print(f"Detected CSV encoding: {encoding}")

# Load CSV
df = pd.read_csv("amenities_competition.csv", encoding=encoding)
# Step 1: Connect to MySQL database (replace placeholders with your actual credentials)
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    connection_timeout=5,
    use_pure=True
)
cursor = conn.cursor()


cursor.execute("CREATE DATABASE IF NOT EXISTS audit")
cursor.execute("USE audit")


create_table_query = f'''
CREATE TABLE IF NOT EXISTS competition_amenities (
    `Index` INT PRIMARY KEY,
    `99acres` TEXT,
    `C1` TEXT,
    `C2` TEXT,
    `C3` TEXT

)
'''
cursor.execute(create_table_query)


# 3. Insert data into table
insert_query = f"""
    INSERT INTO competition_amenities( `Index`, `99acres`, `C1`,`C2`,`C3`)
    VALUES (%s, %s, %s, %s, %s)
    
"""
for _, row in df.iterrows():
    cursor.execute(insert_query, (int(row['Index']), str(row['99acres']), str(row['C1']),str(row['C2']),str(row['C3'])))
conn.commit()



# Step 3: Functions to process amenities
def extract_amenities_99acres(amenities_str):
    if pd.isna(amenities_str):
        return []
    items = re.split(r',\s*', amenities_str)
    # Normalize: remove numbers, strip spaces, and convert to lowercase
    return list(set([re.sub(r'^\d+:\s*', '', item).strip().lower() for item in items]))

def extract_amenities_other(text):
    if pd.isna(text):
        return []
    items = re.split(r',|;|/|&', text)
    # Normalize: strip spaces and convert to lowercase
    return list(set([item.strip().lower() for item in items if item.strip()]))

# Step 4: Process columns
df['99acres_clean'] = df['99acres'].apply(extract_amenities_99acres)
df['C1_clean'] = df['C1'].apply(extract_amenities_other)
df['C2_clean'] = df['C2'].apply(extract_amenities_other)
df['C3_clean'] = df['C3'].apply(extract_amenities_other)

df['combined_C'] = df.apply(lambda row: list(set(row['C1_clean'] + row['C2_clean'] + row['C3_clean'])), axis=1)
df['missing_amenities'] = df.apply(
    lambda row: sorted(set(map(str.lower, row['99acres_clean'])) - set(map(str.lower, row['combined_C']))),
    axis=1
)

# Step 5: Update MySQL table with new column values
# Ensure the column exists (add if not)
cursor.execute(f"""
    ALTER TABLE competition_amenities
    ADD COLUMN IF NOT EXISTS missing_amenities TEXT
""")
conn.commit()

# Update each row's missing amenities
for idx, row in df.iterrows():
    cell_value = ', '.join(row['missing_amenities'])
    update_query = f"""
        UPDATE competition_amenities
        SET missing_amenities = %s
        WHERE `Index` = %s
    """
    cursor.execute(update_query, (cell_value, row["Index"]))


conn.commit()

cursor.close()
conn.close()
print(f'Table created and data inserted, total rows: {len(df)} successfully.')
