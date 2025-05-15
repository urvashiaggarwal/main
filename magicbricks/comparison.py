import pandas as pd
from fuzzywuzzy import fuzz
 
# Load the CSV files
print("Loading CSV files...")
csv1 = pd.read_csv("99acres.csv")
csv2 = pd.read_csv("magicbricks.csv")
print("CSV files loaded successfully.")
 
# Define column mapping between csv1 (99acres) and csv2 (housing)
column_mapping = {
    "name": "Name",
    "builderinfo_name": "Builder",
    "location_localityname": "Address",
    "constructionstage_constructionstatus": "Status",
    "primarySaleType": "Project Type"

}
 
# Prepare lists to store matched and mismatched data
matches = []
mismatches = []
 
print("Starting the matching process...")
 
# Function to preprocess text for better matching
def preprocess(text):
    if pd.isna(text) or text == "nan":
        return ""
    return str(text).lower().replace("_", " ").strip()
 
# Iterate over each row in housing.csv
for index, row in csv2.iterrows():
    xid = row["XID"]
    print(f"Processing XID: {xid} ({index + 1}/{len(csv2)})")
    match_row = csv1[csv1["XID"] == xid]
   
    if match_row.empty:
        print(f"XID {xid} not found in 99acres, skipping...")
        continue  # Skip if XID not found in 99acres
   
    match_row = match_row.iloc[0]  # Convert to series
    mismatch_entry = {"XID": xid}
    is_match = True
   
    for col1, col2 in column_mapping.items():
        val1 = preprocess(match_row[col1])
        val2 = preprocess(row[col2])
        score = fuzz.ratio(val1, val2)
       
        print(f"Comparing {col2}: '{val1}' vs '{val2}', Score = {score}")
        mismatch_entry[col2] = row[col2] if score >= 60 else f"99acres: {match_row[col1]} | MagicBricks: {row[col2]}"
        mismatch_entry[f"{col2}_Score"] = score
        if score < 60:
            is_match = False
   
    if is_match:
        print(f"XID {xid} matched successfully.")
        matches.append(mismatch_entry)
    else:
        print(f"XID {xid} has mismatches.")
        mismatches.append(mismatch_entry)
 
print("Matching process completed.")
 
# Convert results to DataFrame and save to CSV
print("Saving matches.csv...")
pd.DataFrame(matches).to_csv("matches.csv", index=False)
print("Saving mismatches.csv...")
pd.DataFrame(mismatches).to_csv("mismatches.csv", index=False)
print("Process completed successfully!")