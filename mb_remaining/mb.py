import time
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import openpyxl
import re
 
# Setup Selenium WebDriver
options = Options()
#options.add_argument("--headless")  # Run in headless mode
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
 
# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
 
# Read input CSV (Skipping first row)
input_file = "Copy of URL Data - Noida.csv"
output_file = "magic_review.csv"

# Read the input CSV and extract XID and Square Yards Phase URLs

urls_xids = []

# Read the input CSV and extract XID and Square Yards Phase URLs
with open(input_file, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        xid = row["project_id"]
        for phase in ["MB  Phase 1", "MB  Phase 2", "MB  Phase 3", "MB  Phase 4"]:
            url = row.get(phase, "").strip()
            if url:
                if not url.startswith("http://") and not url.startswith("https://"):
                    url = "http://" + url  # Add http:// if missing
                if 'pdpid' in url:
                    urls_xids.append((xid, url, phase))

# urls_xids=urls_xids[422:]

# # Option to start from a specific index
# urls_xids = urls_xids[102:]
#urls_xids = [("XID123", "https://www.magicbricks.com/moreshwar-19-east-nerul-navi-mumbai-pdpid-4d4235323133353931", "1")]
# Prepare output data list
data_list = []

# Iterate over each XID and its corresponding Square Yards Phase URLs
for xid, url, phase in urls_xids:
    print(f"Opening URL: {url} for XID: {xid} and Phase: {phase}")
    driver.get(url)
    time.sleep(2)
    try:
        project_name = driver.find_element(By.CSS_SELECTOR, ".pdp__name h1").text.strip()
    except:
        project_name = "N/A"

    
        # Check for Ratings & Reviews section
    try:
        ratings_reviews_heading = driver.find_element(By.CSS_SELECTOR, ".pdp__projreview__heading").text.strip()
        if "Ratings & Reviews" in ratings_reviews_heading:
            location_text = driver.find_element(By.CSS_SELECTOR, ".pdp__projreview__headtext").text.strip()
            if project_name in location_text:
                print(f"Ratings & Reviews found for project: {project_name}")
                
                review_elem = driver.find_element(By.CSS_SELECTOR, ".pdp__projreview__labeltotalreview")
                  # update this if needed
                review_text = review_elem.text.strip()
              
                print(f"Review Count: {review_text}")
        else:
           
            review_text= "N/A"
            print("Ratings & Reviews section not found.")
    except Exception as e:
        print(f"Error while checking Ratings & Reviews section: {e}")



    # Append data to the output list
    data_list.append({
        "XID": xid,
        "Phase": phase,
        "Project Name": project_name,
    
        "Review Count": review_text
    })

    # Write data to CSV file simultaneously
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["XID", "Phase", "Project Name", "Project Status", "Video Count", "Review Count", "Image Count"])
        if file.tell() == 0:  # Write header only if file is empty
            writer.writeheader()
        writer.writerow({
            "XID": xid,
            "Phase": phase,
            "Project Name": project_name,
            "Review Count": review_text
        })


 