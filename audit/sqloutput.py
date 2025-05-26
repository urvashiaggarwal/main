import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
    connection_timeout=5,
    use_pure=True
)

df = pd.read_sql("SELECT * FROM audit_data", conn)
df.to_csv("audit_results.csv", index=False)
print("Exported to audit_results.csv")

conn.close()
