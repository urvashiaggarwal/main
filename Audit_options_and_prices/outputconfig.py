import pandas as pd
import mysql.connector
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

# Query data, ordering by `index`
query = "SELECT * FROM config_data ORDER BY `index`"

df = pd.read_sql(query, conn)

# Save to CSV
df.to_csv("mumbai_config_data.csv", index=False)

print("Exported to config_data_grouped_by_index.csv")

conn.close()