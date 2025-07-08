import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# Step 1: Set up Google Sheets connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("thematic-center-456905-p2-9fe58916a625.json", scope)
client = gspread.authorize(creds)

# Step 2: Open the Google Sheet
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("amenities")

data = sheet.get_all_records()
df = pd.DataFrame(data)

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

# Step 5: Update back to Google Sheet
# Insert new column if not present
header = sheet.row_values(1)
if "missing_amenities" not in header:
    sheet.update_cell(1, len(header) + 1, "missing_amenities")  # add header

# Update each row's missing amenities
for i, value in enumerate(df['missing_amenities'], start=2):  # row 2 onwards
    cell_value = ', '.join(value)
    sheet.update_cell(i, len(header) + 1, cell_value)
