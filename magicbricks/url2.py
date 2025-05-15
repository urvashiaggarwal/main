import requests
import pandas as pd
import time
 
# Load Excel file
file_path = r"List_data.xlsx"
df = pd.read_excel(file_path)
 
# Ensure column names are correct
if 'Proj Name' not in df.columns or 'City' not in df.columns:
    raise ValueError("Excel file must contain 'proj_name' and 'city' columns")
 
API_KEY = "AIzaSyDHXKNrtN0V_eEdaNUmi3SVaKJ5w7K2CKI"
CX = "85dfa13c72e034042"
output_data = []
 
df = df.iloc[1227:1280]
# Process rows from 101 to 150
for _, row in df.iterrows():
    time.sleep(2)
    xid = str(row["XID"]).strip()
    proj_name = str(row["Proj Name"]).strip()
    City = str(row["City"]).strip()
    query = f"{proj_name} {City}"
   
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"
    response = requests.get(url)
    data = response.json()
   
    magic_link = "Not Found"
    if "items" in data:
        for item in data["items"]:
            if "magicbricks.com" in item["link"] and "pdpid" in item["link"]:
                magic_link = item["link"]
                break  # Stop once we find the first magicbricks.com link
        
    print(f"XID:{xid},Project: {proj_name}, City: {City}, Link: {magic_link}")
    output_data.append([xid,proj_name, City, magic_link])
 
# Save results to an Excel file
output_df = pd.DataFrame(output_data, columns=["XID","Project Name", "City", "Magicbricks.com Link"])
output_df.to_csv("test_link.csv", mode='a', header=False, index=False)
 
print("Results saved to 'Magicbricks_links_updated.csv'.")