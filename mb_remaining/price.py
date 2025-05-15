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
input_file = "Mumbai URL's.csv"
output_file = "magicbricks_price.csv"

# Read CSV using pandas
df = pd.read_csv(input_file, skiprows=1, header=None)  # Skip first row
xids = df[0].tolist()  # Extract XIDs from the first column
urls = df[3].tolist()  # Extract URLs from the fourth column (Magic Bricks Phase 1)

# Filter URLs that contain 'pdpid' with other text before and after
filtered_urls = []
filtered_xids = []
for xid, url in zip(xids, urls):
    if 'pdpid' in url:
        filtered_urls.append(url)
        filtered_xids.append(xid)

urls = filtered_urls
xids = filtered_xids
# Work on top 20 records
# urls = urls[3256:]
# xids = xids[3256:]
# xids=["r145369"]
# urls=["https://www.magicbricks.com/173-west-oaks-wakad-pune-pdpid-4d4235323037383531"]# Prepare output data list
data_list = []

 
# Iterate over each URL
for xid, url in zip(xids, urls):
    floor_plans = []
    print(f"Opening URL: {url}")
    driver.get(url)
    time.sleep(3)  # Wait for elements to load

    try:
        price_range_element = driver.find_element(By.CSS_SELECTOR, "div.pdp__pricecard--price")
        price_range = price_range_element.text.strip()
        price_range = price_range.replace("₹", "Rs").strip()
        print(price_range)
        # price = driver.find_element(By.XPATH, '//*[@id="nav-overview"]/div[2]/div[1]/div[1]/div').text.strip()
        # price = price.replace("₹", "Rs").strip()
        # print(price)
    except:
        price = "N/A"

    
    # Extracting data
    try:
        name = driver.find_element(By.CSS_SELECTOR, "div.pdp__name h1").text.strip()
    except:
        name = "N/A"
   
   
 
    # Append data to list
    data_list.append([
        xid, url, name,price_range
    ])

    # Save to CSV simultaneously
    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Check if file is empty to write header
            writer.writerow([
                "XID", "URL", "Name", "Price Range"
            ])
        writer.writerow(data_list[-1])

print(f" Data extraction complete. Results appended in {output_file}")

driver.quit()
 
 