import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup Selenium WebDriver
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Input and output CSV files
input_file = "new21.csv"
output_file = "mb_final.csv"

# Read the input CSV and extract XID and URLs
urls_xids = []
with open(input_file, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        xid = row["XID"]
        url = row["Comp 1"]
        if url and 'pdpid' in url:
            urls_xids.append((xid, url))

# Open output CSV and write header
with open(output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["XID", "Floor Plan"])

# Extract floor plans for each URL
for xid, url in urls_xids:
    print(f"Processing XID: {xid}, URL: {url}")
    driver.get(url)
    time.sleep(3)  # Wait for the page to load

    floor_plans = []
    try:
        
        print("Extracting Floor Plans...")
# Locate the main container with class 'pdp__florpripln__cards'
        try:
            heading = driver.find_element(By.CLASS_NAME, "pdp__florpripln--heading").text.strip()
            if "Floor Plans" not in heading:
                print("Floor Plans not present in heading. Skipping this URL.")
                continue
            floor_plan_container = driver.find_element(By.CLASS_NAME, "pdp__florpripln__cards")
            
            # Find all floor plan cards inside the container
            floor_plan_cards = floor_plan_container.find_elements(By.CSS_SELECTOR, ".swiper-slide, .swiper-slide swiper-slide-next , .swiper-slide swiper-slide-prev, .swiper-slide swiper-slide-active")

            for index, card in enumerate(floor_plan_cards):
                try:
                    # Extract unit size and type
                    unit_details = card.find_elements(By.CSS_SELECTOR, "div.pdp__florpripln--bhk span")
                    unit_size = unit_details[0].text.strip() if len(unit_details) > 0 else None
                    unit_type = unit_details[1].text.strip() if len(unit_details) > 1 else None

                    # Extract area type
                    try:
                        area_type = card.find_element(By.CLASS_NAME, "pdp__florpripln--superArea").text.strip()
                    except:
                        area_type = None

                    # Extract price
                    try:
                        price = card.find_element(By.CLASS_NAME, "fullPrice__amount").text.strip()
                    except:
                        price = None

                    # Extract possession date
                    try:
                        possession_date = card.find_element(By.CLASS_NAME, "pdp__florpripln--possDate").text.strip()
                    except:
                        possession_date = None

                    if any([unit_size, unit_type, area_type, price, possession_date]):
                        floor_plans.append([ unit_type or "Type Not Available",area_type or "Area Not Available", unit_size or "Size Not Available", price or "Price Not Available"])

                    
                    
                    # Only append if at least one of the key details is present
                
                except Exception as e:
                    print(f"Skipping a card due to error: {e}")

                # Click the next button after every 2 records
                if (index + 1) % 2 == 0:
                    try:
                        next_button = driver.find_element(By.ID, "fp-arrow-next")
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)  # Wait for the next set of floor plans to load
                    except:
                        print("Next button not found or could not be clicked.")
                        break

        except:
            # If no floor plan cards are found, try extracting from the alternative section
            if not floor_plans:
                try:
                    print("hi")
                    alternative_floor_plan_cards = driver.find_elements(By.CSS_SELECTOR, "div.pdp__prop__card")
                    for card in alternative_floor_plan_cards:
                        try:
                            # Extract unit type and size
                            unit_details = card.find_element(By.CSS_SELECTOR, "div.pdp__prop__card__bhk span").text.strip()
                            unit_type, unit_size = unit_details.split(" ", 1) if " " in unit_details else (unit_details, "Size Not Available")

                            # Extract price
                            try:
                                price = card.find_element(By.CLASS_NAME, "pdp__prop__card__price").text.strip()
                            except:
                                price = "Price Not Available"

                            # Extract possession date
                            try:
                                possession_date = card.find_element(By.CLASS_NAME, "pdp__prop__card__cons").text.strip()
                            except:
                                possession_date = "Possession Not Available"

                            # Append extracted details
                            floor_plans.append([ unit_type, "Area Not Available", unit_size, price])
                        except Exception as e:
                            print(f"Skipping an alternative card due to error: {e}")
                except:
                    print("No alternative floor plan section found.")
            print("No floor plan container found on this page.")


        # Print extracted floor plans for debugging
        for plan in floor_plans:
            print(plan)

    except Exception as e:
        print(f"Error extracting floor plans: {e}")

    # Write the extracted floor plans to the CSV
    with open(output_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if floor_plans:
            combined_floor_plans = " | ".join(
            [", ".join(plan) for plan in floor_plans]
            )
            writer.writerow([xid, combined_floor_plans])
        else:
            writer.writerow([xid, "No Floor Plans Available"])

print(f"Floor plan extraction complete. Results saved to {output_file}")
driver.quit()