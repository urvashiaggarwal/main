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

# Setup Selenium WebDriver
options = Options()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Input and Output File Paths
input_xid_file = "missing_xids_manual.csv"
project_links_file = "Copy of XID URL Data.xlsx"
floor_plans_csv = "missing_floorplans_manual_phases.csv"

# Read input XIDs
xids = []
with open(input_xid_file, mode="r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header
    for row in reader:
        xid = row[0].strip()
        if xid:
            xids.append(xid)

# Read the Excel file with all project links
df_links = pd.read_excel(project_links_file)

# List of MagicBricks Phase columns to search
magicbricks_phases = [
    "Magic Bricks Phase 1", "Magic Bricks Phase 2",
    "Magic Bricks Phase 3", "Magic Bricks Phase 4"
]

# Function to extract floor plans
def extract_floor_plans(xid, url, phase):
    floor_plans = []
    print(f"\nOpening URL: {url} for XID: {xid} | Phase: {phase}")
    driver.get(url)
    time.sleep(3)

    try:
        print("Extracting Floor Plans...")
        try:
            floor_plan_container = driver.find_element(By.CLASS_NAME, "pdp__florpripln__cards")
            floor_plan_cards = floor_plan_container.find_elements(By.CSS_SELECTOR, ".swiper-slide")

            for index, card in enumerate(floor_plan_cards):
                try:
                    unit_details = card.find_elements(By.CSS_SELECTOR, "div.pdp__florpripln--bhk span")
                    unit_size = unit_details[0].text.strip() if len(unit_details) > 0 else None
                    unit_type = unit_details[1].text.strip() if len(unit_details) > 1 else None

                    try:
                        area_type = card.find_element(By.CLASS_NAME, "pdp__florpripln--superArea").text.strip()
                    except:
                        area_type = None

                    try:
                        price = card.find_element(By.CLASS_NAME, "fullPrice__amount").text.strip()
                    except:
                        price = None

                    try:
                        possession_date = card.find_element(By.CLASS_NAME, "pdp__florpripln--possDate").text.strip()
                    except:
                        possession_date = None

                    if any([unit_size, unit_type, area_type, price, possession_date]):
                        floor_plans.append([xid, phase, unit_type or "N/A", unit_size or "N/A", area_type or "N/A", price or "N/A", possession_date or "N/A"])

                except Exception as e:
                    print(f"Skipping a card due to error: {e}")

                if (index + 1) % 2 == 0:
                    try:
                        next_button = driver.find_element(By.ID, "fp-arrow-next")
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                    except:
                        break

        except:
            print("Primary floor plan container not found. Trying alternative layout...")
            try:
                alt_cards = driver.find_elements(By.CSS_SELECTOR, "div.pdp__prop__card")
                for card in alt_cards:
                    try:
                        unit_details = card.find_element(By.CSS_SELECTOR, "div.pdp__prop__card__bhk span").text.strip()
                        unit_type, unit_size = unit_details.split(" ", 1) if " " in unit_details else (unit_details, "N/A")
                        try:
                            price = card.find_element(By.CLASS_NAME, "pdp__prop__card__price").text.strip()
                        except:
                            price = "N/A"
                        try:
                            possession_date = card.find_element(By.CLASS_NAME, "pdp__prop__card__cons").text.strip()
                        except:
                            possession_date = "N/A"
                        floor_plans.append([xid, phase, unit_type, unit_size, "N/A", price, possession_date])
                    except Exception as e:
                        print(f"Skipping an alternative card due to error: {e}")
            except:
                print("No alternative floor plan section found.")
    except Exception as e:
        print(f"Error processing URL: {e}")

    return floor_plans

# Output file setup
with open(floor_plans_csv, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["XID", "Phase", "Unit Type", "Unit Size", "Area Type", "Price", "Possession Date"])

    # Iterate over input XIDs
    for xid in xids:
        matching_rows = df_links[df_links["XID Number"].astype(str) == xid]
        if not matching_rows.empty:
            for _, row in matching_rows.iterrows():
                for phase_col in magicbricks_phases:
                    url = row.get(phase_col)
                    if pd.notna(url) and isinstance(url, str) and 'pdpid' in url:
                        plans = extract_floor_plans(xid, url.strip(), phase_col)
                        writer.writerows(plans)
        else:
            print(f"XID {xid} not found in project_links.xlsx")

print(f"\n✅ Data extraction complete. Results saved to {floor_plans_csv}")
driver.quit()
