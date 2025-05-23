import requests
import pandas as pd
import time
import itertools
import random
import os
import csv

# Load API keys
API_KEYS = ["AIzaSyAsyKg1Qkt2pll1Uok6ZJHjZzx2TUhgazM","AIzaSyB2luEX9qNGWlp5pLxFkzuJzfZb3dFbvTQ"]
CX = "85dfa13c72e034042"  # Custom Search Engine ID

# API Usage Tracking
api_usage_count = {key: 0 for key in API_KEYS}
api_cycle = itertools.cycle(API_KEYS)  

# Settings for rate limiting
API_SWITCH_TIME = random.uniform(6, 8)  
MAX_REQUESTS_PER_MINUTE = 50  
REQUEST_DELAY = random.uniform(2.5, 3)  

last_switch_time = time.time()

# Check if an output file exists and resume processing
output_file = "Magicbricks_links.csv"
if os.path.exists(output_file):
    existing_df = pd.read_csv(output_file)
    processed_xids = set(existing_df["XID"].astype(str))
else:
    processed_xids = set()

def get_next_api_key():
    """Returns the next valid API key, ensuring it has not exceeded 100 requests."""
    global last_switch_time
    current_time = time.time()

    # Switch API key if time limit reached
    if current_time - last_switch_time > API_SWITCH_TIME:
        while True:
            api_key = next(api_cycle)
            if api_usage_count[api_key] < 90:
                last_switch_time = time.time() 
                return api_key
    else:
        return next(api_cycle)  

file_path = r"List.xlsx"
df = pd.read_excel(file_path)

if 'proj_name' not in df.columns or 'City' not in df.columns or 'XID' not in df.columns:
    raise ValueError("Excel file must contain 'proj_name', 'City', and 'XID' columns")

df = df[df["XID"].astype(str).isin(processed_xids) == False] 
df = df.iloc[:200]

output_data = []
current_api_key = get_next_api_key()  

# Process rows
for index, row in df.iterrows():
    time.sleep(REQUEST_DELAY)  

    xid = str(row["XID"]).strip()
    proj_name = str(row["proj_name"]).strip()
    City = str(row["City"]).strip()
    query = f"{proj_name} {City} magicbricks.com"

    # Get a valid API key based on time interval and usage count
    current_api_key = get_next_api_key()
    api_usage_count[current_api_key] += 1  

    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={current_api_key}&cx={CX}"
    response = requests.get(url)
    data = response.json()

    # Check for API errors
    if "error" in data and data["error"]["code"] == 429:
        print(f"Rate limit exceeded for {current_api_key}, switching key...")
        time.sleep(8) 
        current_api_key = get_next_api_key() 
        continue  

    magic_link = "Not Found"
    if "items" in data:
        for item in data["items"]:
            if "magicbricks.com" in item["link"] :
                magic_link = item["link"]
                break  # Stop once we find the first magicbricks.com link with pdpid

    print(f"Row {index+1}: XID:{xid}, Project: {proj_name}, City: {City}, Link: {magic_link}, API Used: {current_api_key}")

    # Append data to CSV file immediately
    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  
            writer.writerow(["XID", "Project Name", "City", "Magicbricks.com Link"])
        writer.writerow([xid, proj_name, City, magic_link])

   
    # Rate limit handling
    if (index + 1) % MAX_REQUESTS_PER_MINUTE == 0:
        print(f"Reached {MAX_REQUESTS_PER_MINUTE} requests, pausing for a while...")
        time.sleep(30)  

print("Results saved to 'Magicbricks_links.csv'.")
