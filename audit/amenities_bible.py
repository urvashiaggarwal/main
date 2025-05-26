import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("thematic-center-456905-p2-9fe58916a625.json", scope)
client = gspread.authorize(creds)


sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("a2")
data = sheet.get_all_records()
df = pd.DataFrame(data)

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

# Missing amenities
df['missing_amenities'] = df.apply(
    lambda row: sorted(set(row['brochure_clean']) - set(row['99acres_clean'])),
    axis=1
)

# Update Google Sheet with new column
header = sheet.row_values(1)
missing_col_index = len(header) + 1
if "missing_amenities" not in header:
    sheet.update_cell(1, missing_col_index, "missing_amenities")
else:
    missing_col_index = header.index("missing_amenities") + 1

for i, value in enumerate(df['missing_amenities'], start=2):
    cell_value = ', '.join(value)
    sheet.update_cell(i, missing_col_index, cell_value)
