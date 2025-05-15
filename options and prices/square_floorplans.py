from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time

# Setup Selenium WebDriver
driver = webdriver.Chrome()
driver.set_page_load_timeout(5)  # Set timeout to 5 seconds

# Read URLs and XIDs from CSV
input_csv_filename = "new21.csv"
urls_xids = []

# Read the input CSV and extract XID and Square Yards Phase URLs
with open(input_csv_filename, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        xid = row["XID"]
        #phase = row["phase"]
        url = row["Comp 3"]
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url  # Add http:// if missing
            urls_xids.append((xid, url))

# Open each URL and extract floor plans
for xid, url in urls_xids:
    try:
        print(f"Loading URL: {url}")
        driver.get(url)
        time.sleep(3)

        # Navigate to the price list tab
        try:
            price_list_tab = driver.find_element(By.XPATH, "//li[@data-tab='npPriceList']")
            driver.execute_script("arguments[0].click();", price_list_tab)
            time.sleep(3)
        except Exception:
            print("Price List tab not found.")
            continue

        # Extract floor plans
        try:
            price_table = driver.find_element(By.CSS_SELECTOR, ".npTableBox.scrollBarHide.active")
            rows = price_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        except Exception:
            print("No active price table found.")
            rows = []

        
        # Extract area type1 (e.g., Saleable)
        try:
            unit_size_element = driver.find_element(By.XPATH, "//table[@class='npOverViewTable']//span[text()='Unit Sizes']/following-sibling::strong")
            unit_size_text = unit_size_element.text.strip()
         
            # Extract area type and range from unit size text
            if "(" in unit_size_text and ")" in unit_size_text:
                area_type1 = unit_size_text[unit_size_text.find("(") + 1:unit_size_text.find(")")]
                
            else:
                area_type1 = "N/A"
             

            print("Area Type:", area_type1)
           
        except Exception:
            unit_size_text = "N/A"
            area_type1 = "N/A"
            print("Unit size or area type not found.")



        floor_plans = []
        for row in rows:
            
            try:
                unit_type = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) strong").text.strip()
                print(unit_type)
                area_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) .bhkSqFt.Detail_NewProject_D11")
                area = area_element.find_element(By.CSS_SELECTOR, "span").text.strip()
                print(area)
                try:
                    area_type = area_element.find_element(By.CSS_SELECTOR, ".saleable.Detail_NewProject_D11").text.strip()
                    print(area_type)
                except Exception:
                    area_type = "N/A"
                # area = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) span").text
                # print(area)
                price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                price = price.replace("₹", "Rs").strip()
                print(price)
                
                floor_plans.append((area_type1,unit_type, area_type, area, price))
                
               
            except Exception:
                continue

        # Append floor plans to CSV
        print(f"Found {len(floor_plans)} floor plans for XID: {xid}")
        print(floor_plans)
        # for plan in floor_plans:
        #     print(f"Unit Type: {plan[0]}, Area: {plan[1]}, Price: {plan[2]}, Area Type: {plan[3]}")
        floor_plan_csv_filename = "square_final.csv"
        with open(floor_plan_csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for plan in floor_plans:
                writer.writerow([xid, floor_plans])

        print(f"Floor plan data saved to {floor_plan_csv_filename}")

    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Close the browser
driver.quit()