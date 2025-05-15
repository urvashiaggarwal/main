from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time
import os
import validators
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Selenium WebDriver
driver = webdriver.Chrome()
driver.set_page_load_timeout(180)  # Set timeout to 180 seconds

# Read URLs and XIDs from CSV
input_csv_filename = "further21.csv"
urls_xids = []

# Read the input CSV and extract XID and Square Yards Phase URLs
with open(input_csv_filename, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        xid = row["XID"]
        
        url=row["Comp 3"]    
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url  # Add http:// if missing
            if url.endswith("/project"):
                urls_xids.append((xid, url))

# # Option to start from a specific index
urls_xids = urls_xids[:]
#urls_xids=[("XID123", "https://www.squareyards.com/noida-residential-property/aba-county-107/10931/project", "Phase 1"),]


# Open each URL and extract data
for xid, url in urls_xids:
    if not validators.url(url):
        print(f"Invalid URL: {url}")
        continue

    retries = 3  # Number of retries for loading the page
    for attempt in range(retries):
        try:
            print(f"Attempting to load URL (Attempt {attempt + 1}/{retries}): {url}")
            driver.get(url)
            time.sleep(3)
            break  # Exit retry loop if successful
        except Exception as e:
            print(f"Error loading URL {url} on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:
                print(f"Failed to load URL after {retries} attempts: {url}")
                continue  # Skip to the next URL

    try:
        # Handle potential popup
        
        try:
            project_name = driver.find_element(By.CSS_SELECTOR, "h1.npMainHeading strong").text.strip()
        except Exception:
            project_name = "N/A"

        # Extract location
        try:
            location = driver.find_element(By.CSS_SELECTOR, "h1.npMainHeading .location").text.strip()
        except Exception:
            location = "N/A"

        # Extract price range
        try:
            price_range = driver.find_element(By.CSS_SELECTOR, "div.npPriceBox").text.strip()
            price_range = price_range.replace("₹", "Rs").strip()
        except Exception:
            price_range = "N/A"

        # Extract price per square foot
        try:
            price_per_sqft = driver.find_element(By.CSS_SELECTOR, "div.npPerSqft").text.strip()
            price_per_sqft = price_per_sqft.replace("₹", "Rs").strip()
        except Exception:
            price_per_sqft = "N/A"
        
        

        # Extract "Why Consider" list items
        try:
            view_more_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-link")
            driver.execute_script("arguments[0].click();", view_more_button)
            time.sleep(2)
            try:
                usp_elements = driver.find_elements(By.CSS_SELECTOR, ".whyConsiderContentModal .whyConsiderList li")
                # Extract text
                usps = [usp.text for usp in usp_elements]
                #print("USP:", usps)
                
            except Exception:
                # 
                usp=[]

            usp = ",".join(usps)
            print("USP:", usp)
            close_button = driver.find_element(By.CSS_SELECTOR, "button.rightCloseButton")
            driver.execute_script("arguments[0].click();", close_button)

        except Exception:
            usp = "N/A"

        try:
            time.sleep(5)  # Wait for the popup to appear
            popup_div = driver.find_element(By.ID, "ClientInfoForm_projectpopup_formbox")
            close_button = popup_div.find_element(By.CSS_SELECTOR, "button.closeButton")
            driver.execute_script("arguments[0].click();", close_button)
            print("Popup closed.")
        except Exception:
            print("No popup appeared.")

        try:
            rera_panel = driver.find_element(By.CSS_SELECTOR, ".panelHeader[data-reraid]")
            
            rera_number = rera_panel.find_element(By.CSS_SELECTOR, "strong").text.split()[0].strip()
                
            print("RERA Number:", rera_number)
        except Exception:
            rera_number = "N/A"
            print("RERA Number not found.")

        # Extract project status
        try:
            project_status_element = driver.find_element(By.CSS_SELECTOR, "td em.icon-project-status + span + strong")
            project_status = project_status_element.text.strip()
        except Exception:
            project_status = "N/A"
            print("Project Status not found.")

        video_count = 0
        try:
            badge_video_text = driver.find_element(By.CSS_SELECTOR, ".npFigure.video .badge").text
            if 'Video' in badge_video_text:
                video_count = 1
            if '+' in badge_video_text and 'Video' in badge_video_text:
                video_count = int(badge_video_text.split('+')[1].split()[0])
        except:
            pass  # no video badge

        # Extract photo count
        
        
        csv_filename = "squareyards_21.csv"
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "XID","URL", "Project Name","Project Status","Video Count"
                   
                ])
            writer.writerow([
                xid,url, project_name,project_status,video_count
               
            ])

        print(f"Data saved to {csv_filename}")

    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Close the browser
driver.quit()

