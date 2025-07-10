import pandas as pd
import mysql.connector
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()   

# 1. Connect to MySQL database (replace placeholders with your actual credentials)
conn = mysql.connector.connect(
    host=os.environ.get('MYSQL_HOST'),
    user=os.environ.get('MYSQL_USER'),
    password=os.environ.get('MYSQL_PASSWORD'),
    database=os.environ.get('MYSQL_DATABASE')
)
cursor = conn.cursor(dictionary=True)

table_name = 'amenities_bible'  # Replace with your table name
id_column = 'id'          # Replace with your unique ID column

# 2. Fetch data from MySQL
df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

# 3. Clean `99acres` and `Brochure` column values
def clean_99acres(val):
    if pd.isna(val):
        return []
    items = [re.sub(r'^\d+:', '', x).strip().lower() for x in val.split(',')]
    return list(set(items))

def clean_brochure(val):
    if pd.isna(val):
        return []
    items = [x.strip().lower() for x in re.split(r',|/|;', val)]
    return list(set(items))

df['99acres_clean'] = df['99acres'].apply(clean_99acres)
df['brochure_clean'] = df['Brochure'].apply(clean_brochure)

# 4. Compute missing amenities (in Brochure but not in 99acres)
df['missing_amenities'] = df.apply(
    lambda row: sorted(set(row['brochure_clean']) - set(row['99acres_clean'])),
    axis=1
)

# 5. Update MySQL table with new column values
# Ensure the column exists (add if not)
cursor.execute(f"""
    ALTER TABLE {table_name} 
    ADD COLUMN IF NOT EXISTS missing_amenities TEXT
""")
conn.commit()

# 6. Update each row with the computed missing amenities
for idx, row in df.iterrows():
    cell_value = ', '.join(row['missing_amenities'])
    update_query = f"""
        UPDATE {table_name}
        SET missing_amenities = %s
        WHERE {id_column} = %s
    """
    cursor.execute(update_query, (cell_value, row[id_column]))

    print(f"Updated row {idx+1} of {len(df)}")

conn.commit()

cursor.close()
conn.close()
