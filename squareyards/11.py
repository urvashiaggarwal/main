from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time
import os
import validators

# Setup Selenium WebDriver
driver = webdriver.Chrome()
driver.set_page_load_timeout(180)  # Set timeout to 180 seconds

# Read URLs and XIDs from CSV
input_csv_filename = "workable_links.csv"
urls_xids = []

with open(input_csv_filename, "r", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)
    # next(reader)  # Skip header row
    for row in reader:
        xid = row[0]
        url = row[3]
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url  # Add http:// if missing
        if url.endswith("/project"):
            urls_xids.append((url, xid))

# Option to start from a specific index
# Create a set to track processed XIDs to avoid duplicates
processed_xids = set()

# Read existing XIDs from the output CSV if it exists
output_csv_filename = "cleaned_squareyards_by_first_two_columns.csv"
if os.path.isfile(output_csv_filename):
    with open(output_csv_filename, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            if not row or len(row) < 1:  # Skip empty rows
                continue
            processed_xids.add(row[0])  # Assuming XID is the first column

# Filter URLs and XIDs to exclude already processed ones
urls_xids = [(url, xid) for url, xid in urls_xids if xid not in processed_xids]


def extract_amenities(panel_name):
    amenities = []
    try:
        panel_xpath = f"//div[contains(@class, 'panelHeader')]/strong[text()='{panel_name}']"
        panel_elements = driver.find_elements(By.XPATH, panel_xpath)

        if not panel_elements:
            print(f"Panel '{panel_name}' not found on the page.")
            return "N/A"

        panel_element = panel_elements[0]

        # Check if panel is already expanded
        panel_body_xpath = f"//div[contains(@class, 'panelHeader')]/strong[text()='{panel_name}']/parent::div/following-sibling::div[contains(@class, 'panelBody')]"
        panel_body_elements = driver.find_elements(By.XPATH, panel_body_xpath)

        if not panel_body_elements:
            print(f"Panel body for '{panel_name}' not found.")
            return "N/A"

        panel_body = panel_body_elements[0]
        is_expanded = "active" in panel_body.get_attribute("class")

        # Click only if it's not already expanded
        if not is_expanded:
            driver.execute_script("arguments[0].click();", panel_element)
            time.sleep(1)  # Wait for panel to expand

        # Extract amenities
        amenity_elements = panel_body.find_elements(By.CSS_SELECTOR, ".npAmenitiesTable tbody tr td span")
        for element in amenity_elements:
            text = element.text.strip()
            if text:
                amenities.append(text)

    except Exception as e:
        print(f"Error extracting {panel_name} amenities: {e}")

    return "; ".join(amenities) if amenities else "N/A"

# Open each URL and extract data
for url, xid in urls_xids:
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
            time.sleep(1)
            try:
                why_consider_list = driver.find_elements(By.CSS_SELECTOR, "ul.whyConsiderList ul li")
                why_consider_texts = [item.text.strip() for item in why_consider_list if item.text.strip()]
            except Exception:
                why_consider_texts = []

            usp = ",".join(why_consider_texts)
            close_button = driver.find_element(By.CSS_SELECTOR, "button.rightCloseButton")
            driver.execute_script("arguments[0].click();", close_button)
        except Exception:
            usp = "N/A"

        try:
            time.sleep(4)  # Wait for the popup to appear
            popup_div = driver.find_element(By.ID, "ClientInfoForm_projectpopup_formbox")
            close_button = popup_div.find_element(By.CSS_SELECTOR, "button.closeButton")
            driver.execute_script("arguments[0].click();", close_button)
            print("Popup closed.")
        except Exception:
            print("No popup appeared.")

        try:
            price_per_sqft = driver.find_element(By.CSS_SELECTOR, "div.npPerSqft").text.strip()
            price_per_sqft = price_per_sqft.replace("₹", "Rs").strip()
        except Exception:
            price_per_sqft = "N/A"
        
        

       

        #input("Press Enter to continue...")
        # Extract details dynamically from the table
        data_dict = {
            "Project Status": "N/A",
            "Configurations": "N/A",
            "Unit Sizes": "N/A",
            "Builder": "N/A",
            "Total Number of Units": "N/A",
            "Project Size": "N/A",
            "Launch Date": "N/A",
            "Completion Date": "N/A",
            "Locality": "N/A",
            "Micro Market": "N/A",
            "Builder Experience": "N/A",
            "Ongoing Projects": "N/A",
            "Past Projects": "N/A",
            "Builder URL": "N/A"
        }

        try:
            table_cells = driver.find_elements(By.CSS_SELECTOR, "tbody td")
            for cell in table_cells:
                try:
                    label = cell.find_element(By.TAG_NAME, "span").text.strip()
                    value_element = cell.find_element(By.TAG_NAME, "strong")

                    if value_element.find_elements(By.TAG_NAME, "button"):
                        value = "Ask for Details"
                    else:
                        value = value_element.text.strip()

                    if label == "Builder":
                        try:
                            builder_link_element = value_element.find_element(By.TAG_NAME, "a")
                            data_dict["Builder URL"] = builder_link_element.get_attribute("href")
                        except Exception:
                            pass

                    data_dict[label] = value
                except Exception:
                    pass
        except Exception:
            pass

        if data_dict["Builder URL"] != "N/A":
            try:
                driver.execute_script("window.open(arguments[0]);", data_dict["Builder URL"])
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(1)

                try:
                    builder_experience = driver.find_element(By.CSS_SELECTOR, "div.totalExperience").text.strip()
                except Exception:
                    builder_experience = "N/A"

                try:
                    ongoing_projects = driver.find_elements(By.XPATH, "//div[@class='totalProjectLi']/strong")[0].text.strip()
                except Exception:
                    ongoing_projects = "N/A"

                try:
                    past_projects = driver.find_elements(By.XPATH, "//div[@class='totalProjectLi']/strong")[1].text.strip()
                except Exception:
                    past_projects = "N/A"

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                builder_experience = "N/A"
                ongoing_projects = "N/A"
                past_projects = "N/A"
        else:
            builder_experience = "N/A"
            ongoing_projects = "N/A"
            past_projects = "N/A"

        try:
            price_list_tab = driver.find_element(By.XPATH, "//li[@data-tab='npPriceList']")
            driver.execute_script("arguments[0].click();", price_list_tab)
            time.sleep(2)
        except Exception:
            print("Price List tab not found.")

        try:
            price_table = driver.find_element(By.CSS_SELECTOR, ".npTableBox.scrollBarHide.active")
            rows = price_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        except Exception:
            print("No active price table found.")
            rows = []

        floor_plans = []
        for row in rows:
            try:
                unit_type = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) strong").text.strip()
                area = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) span").text.strip()
                price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                price = price.replace("₹", "Rs").strip()
                floor_plans.append((unit_type, area, price))
            except Exception:
                continue

        floor_plan_csv_filename = "square_yards_floor_plans.csv"
        with open(floor_plan_csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for plan in floor_plans:
                writer.writerow([xid, project_name, *plan])

        print(f"Floor plan data saved to {floor_plan_csv_filename}")

        try:
            rera_text = driver.find_element(By.CSS_SELECTOR, ".npQrBox .qrContent ul li").text.strip()
            rera_number = rera_text.split()[-1]
        except Exception:
            rera_number = "N/A"

        specifications = []
        try:
            # Locate the specifications table
            spec_rows = driver.find_elements(By.CSS_SELECTOR, "#specifications .npSpecificationTable tbody tr")

            for row in spec_rows:
                try:
                    # Extract heading
                    heading_element = row.find_element(By.CSS_SELECTOR, ".npSpecificationHeading strong")
                    heading = heading_element.text.strip() if heading_element else "N/A"

                    # Extract value
                    value_element = row.find_element(By.CSS_SELECTOR, ".npSpecificationValue span")
                    value = value_element.text.strip() if value_element else "N/A"

                    # Append to list only if value is not empty
                    if heading and value:
                        specifications.append(f"{heading}: {value}")
                except Exception as row_error:
                    print("Error processing row:", row_error)

        except Exception as e:
            print("Error extracting specifications:", e)

        # Convert list to a string format
        specifications_text = "; ".join(specifications) if specifications else "N/A"

        print("Specifications:", specifications_text)

        sports_amenities = []
        try:
            # Locate the Sports panel
            sports_panel = driver.find_element(By.XPATH, "//div[contains(@class, 'panel')]/div[@class='panelHeader']/strong[text()='Sports']")
            
            # Get the parent panel div
            parent_panel = sports_panel.find_element(By.XPATH, "./ancestor::div[contains(@class, 'panel')]")
            
            # Check if the panel is already expanded (has 'active' class)
            is_expanded = "active" in parent_panel.get_attribute("class")
            
            # Click only if not expanded
            if not is_expanded:
                driver.execute_script("arguments[0].click();", sports_panel)
                time.sleep(1)  # Allow time for expansion
            
            # Now locate amenities inside the specific "Sports" panel
            sports_amenity_elements = parent_panel.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
            
            for element in sports_amenity_elements:
                text = element.text.strip()
                if text:
                    sports_amenities.append(text)

        except Exception as e:
            print("Error extracting sports amenities:", e)

        # Convert amenities list to a string
        sports_amenities_text = "; ".join(sports_amenities) if sports_amenities else "N/A"

        print("Sports Amenities:", sports_amenities_text)


        # sports_amenities_text = extract_amenities("Sports")
        # print("Sports Amenities:", sports_amenities_text)

        convenience_amenities_text = extract_amenities("Convenience")
        print("Convenience Amenities:", convenience_amenities_text)

        safety_amenities_text = extract_amenities("Safety")
        print("Safety Amenities:", safety_amenities_text)

        leisure_amenities_text = extract_amenities("Leisure")
        print("Leisure Amenities:", leisure_amenities_text)

        environment_amenities_text = extract_amenities("Environment")
        print("Environment Amenities:", environment_amenities_text)

        csv_filename = "cleaned_squareyards_by_first_two_columns.csv"
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "XID", "Project Name", "Location", "Price Range", "Price per Sqft",
                    "Project Status", "Configurations", "Unit Sizes",
                    "Builder", "Total Number of Units", "Project Size",
                    "Launch Date", "Completion Date",
                    "Locality", "Micro Market", "USP", "Builder URL", "Builder Experience", 
                    "Ongoing Projects", "Past Projects", "RERA Number", "Specifications", 
                    "Sports Amenities", "Convenience Amenities", "Safety Amenities", 
                    "Environment Amenities", "Leisure Amenities"
                ])
            writer.writerow([
                xid, project_name, location, price_range, price_per_sqft,
                data_dict["Project Status"], data_dict["Configurations"], data_dict["Unit Sizes"],
                data_dict["Builder"], data_dict["Total Number of Units"], data_dict["Project Size"],
                data_dict["Launch Date"], data_dict["Completion Date"],
                data_dict["Locality"], data_dict["Micro Market"], usp, data_dict["Builder URL"], 
                builder_experience, ongoing_projects, past_projects, rera_number, 
                specifications_text, sports_amenities_text, convenience_amenities_text, 
                safety_amenities_text, environment_amenities_text, leisure_amenities_text
            ])

        print(f"Data saved to {csv_filename}")

    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Close the browser
driver.quit()

