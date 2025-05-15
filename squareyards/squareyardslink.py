import requests
import pandas as pd
import time
 
# Load Excel file
file_path = r"List.xlsx"
df = pd.read_excel(file_path)
 
# Ensure column names are correct
if 'proj_name' not in df.columns or 'City' not in df.columns:
    raise ValueError("Excel file must contain 'proj_name' and 'city' columns")
 
API_KEY = "AIzaSyD_p3nmMAi5wl2g3JGFaQI2bwoD2XqRQuE"
CX = "85dfa13c72e034042"
output_data = []
 
df = df.iloc[90:100]
# Process rows from 101 to 150
for _, row in df.iterrows():
    time.sleep(2)
    xid = str(row["XID"]).strip()
    proj_name = str(row["proj_name"]).strip()
    City = str(row["City"]).strip()
    query = f"{proj_name} {City} squareyards.com"
   
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"
    response = requests.get(url)
    data = response.json()
   
    magic_link = "Not Found"
    if "items" in data:
        for item in data["items"]:
            if "squareyards.com" in item["link"] :
                magic_link = item["link"]
                break  # Stop once we find the first squareyards.com link
        
    print(f"XID:{xid},Project: {proj_name}, City: {City}, Link: {magic_link}")
    output_data.append([xid,proj_name, City, magic_link])
 
# Save results to an Excel file
output_df = pd.DataFrame(output_data, columns=["XID","Project Name", "City", "Squareyards.com Link"])
output_df.to_csv("squareyard_links.csv", mode='a', header=False, index=False)
 
print("Results saved to 'squareyard_links.csv'.")