from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Selenium WebDriver
driver = webdriver.Chrome()

# Open Square Yards property URL (Replace with actual URL)
url = "https://www.squareyards.com/gurgaon-residential-property/smart-world-orchard/103238/project"
xid="2"
driver.get(url)

# Allow page to load
time.sleep(3)

# Extract project name
try:
    project_name = driver.find_element(By.CSS_SELECTOR, "h1.npMainHeading strong").text.strip()
except:
    project_name = "N/A"

# Extract location
try:
    location = driver.find_element(By.CSS_SELECTOR, "h1.npMainHeading .location").text.strip()
except:
    location = "N/A"

# Extract price range
try:
    price_range = driver.find_element(By.CSS_SELECTOR, "div.npPriceBox").text.strip()
    price_range = price_range.replace("₹", "Rs").strip()
except:
    price_range = "N/A"

# Extract price per square foot
try:
    price_per_sqft = driver.find_element(By.CSS_SELECTOR, "div.npPerSqft").text.strip()
    price_per_sqft = price_per_sqft.replace("₹", "Rs").strip()
except:
    price_per_sqft = "N/A"

try:
    view_more_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-link")
    driver.execute_script("arguments[0].click();", view_more_button)
    time.sleep(2)
    # Extract "Why Consider" list items
    try:
        why_consider_list = driver.find_elements(By.CSS_SELECTOR, "ul.whyConsiderList ul li")
        why_consider_texts = [item.text.strip() for item in why_consider_list if item.text.strip()]
    except:
        why_consider_texts = []

    # Add "Why Consider" list to data_dict
    usp = ",".join(why_consider_texts)
    close_button = driver.find_element(By.CSS_SELECTOR, "button.rightCloseButton")
    driver.execute_script("arguments[0].click();", close_button)

except:
    pass

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

# Find all table cells
try:
    table_cells = driver.find_elements(By.CSS_SELECTOR, "tbody td")
    for cell in table_cells:
        try:
            label = cell.find_element(By.TAG_NAME, "span").text.strip()
            value_element = cell.find_element(By.TAG_NAME, "strong")

            # Check if the value is a button (for Launch Date & Completion Date)
            if value_element.find_elements(By.TAG_NAME, "button"):
                value = "Ask for Details"
            else:
                value = value_element.text.strip()

            if label == "Builder":
                try:
                    builder_link_element = value_element.find_element(By.TAG_NAME, "a")
                    data_dict["Builder URL"] = builder_link_element.get_attribute("href")
                except:
                    pass  # No link found

            data_dict[label] = value
        except:
            pass
except:
    pass

if data_dict["Builder URL"] != "N/A":
    try:
        # Open builder page in new window
        driver.execute_script("window.open(arguments[0]);", data_dict["Builder URL"])
        time.sleep(2)

        # Switch to new window
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)

        # Extract builder experience
        try:
            builder_experience = driver.find_element(By.CSS_SELECTOR, "div.totalExperience").text.strip()
        except:
            builder_experience = "N/A"

        # Extract ongoing projects
        try:
            ongoing_projects = driver.find_elements(By.XPATH, "//div[@class='totalProjectLi']/strong")[0].text.strip()
        except:
            ongoing_projects = "N/A"

        # Extract past projects
        try:
            past_projects = driver.find_elements(By.XPATH, "//div[@class='totalProjectLi']/strong")[1].text.strip()
        except:
            past_projects = "N/A"

        # Close new window and switch back
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    except:
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
    time.sleep(3)
except:
    print("Price List tab not found.")

try:
    price_table = driver.find_element(By.CSS_SELECTOR, ".npTableBox.scrollBarHide.active")
    rows = price_table.find_elements(By.CSS_SELECTOR, "tbody tr")
except:
    print("No active price table found.")
    rows = []

# Extract all floor plan details from this table
floor_plans = []
for row in rows:
    try:
        unit_type = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) strong").text.strip()
        area = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) span").text.strip()
        price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
        price = price.replace("₹", "Rs").strip()
        floor_plans.append((unit_type, area, price))
    except:
        continue


floor_plan_csv_filename = "square_yards_floor_plans.csv"
with open(floor_plan_csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["XID","Project Name", "Unit Type", "Area", "Price"])
    for plan in floor_plans:
        writer.writerow([xid,project_name, *plan])

print(f"Floor plan data saved to {floor_plan_csv_filename}")

try:
    rera_text = driver.find_element(By.CSS_SELECTOR, ".npQrBox .qrContent ul li").text.strip()
    rera_number = rera_text.split()[-1]  # Extract last part (RERA number)
except:
    rera_number = "N/A"

specifications = []
try:
    spec_rows = driver.find_elements(By.CSS_SELECTOR, "#specifications .npSpecificationTable tbody tr")
    for row in spec_rows:
        try:
            spec_name = row.find_element(By.CSS_SELECTOR, ".npSpecificationHeading strong").text.strip()
            spec_value = row.find_element(By.CSS_SELECTOR, ".npSpecificationValue span").text.strip()
            specifications.append(f"{spec_name}: {spec_value}")
        except:
            pass
except:
    pass

# Convert specifications list to a single string
specifications_text = "; ".join(specifications) if specifications else "N/A"


# Extract Sports Amenities
# try:
#     sports_panel = driver.find_element(By.CSS_SELECTOR, ".panelHeader strong")
#     if sports_panel.text.strip() == "Sports":
#         driver.execute_script("arguments[0].click();", sports_panel)
#         time.sleep(2)  # Wait for panel to expand
# except Exception as e:
#     print("Sports panel not found or could not be clicked:", e)


# sports_amenities = []
# try:
#     sports_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
#     for element in sports_elements:
#         if element.text.strip():
#             sports_amenities.append(element.text.strip())
# except Exception as e:
#     print("Error extracting sports amenities:", e)

# # Convert amenities list to a single string
# sports_amenities_text = "; ".join(sports_amenities) if sports_amenities else "N/A"

# print("Sports Amenities:", sports_amenities_text)

sports_amenities = []

try:
    # Locate the "Sports" panel header
    sports_panel_xpath = "//div[@class='panelHeader']/strong[text()='Sports']"
    sports_panel_elements = driver.find_elements(By.XPATH, sports_panel_xpath)
    
    if sports_panel_elements:
        sports_panel = sports_panel_elements[0]
        
        # Check if panel is already expanded (has "active" class)
        panel_body = sports_panel.find_element(By.XPATH, "following-sibling::div[contains(@class, 'panelBody')]")
        if "active" not in panel_body.get_attribute("class"):
            driver.execute_script("arguments[0].click();", sports_panel)
            time.sleep(2)  # Wait for panel to expand
        
        # Wait for amenities to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span"))
        )
        
        # Extract sports amenities
        amenity_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
        for element in amenity_elements:
            text = element.text.strip()
            if text:
                sports_amenities.append(text)
    else:
        print("Sports panel not found.")

except Exception as e:
    print("Error extracting sports amenities:", e)

# Convert amenities list to a single string
sports_amenities_text = "; ".join(sports_amenities) if sports_amenities else "N/A"

# Print extracted sports amenities
print(f"Sports Amenities: {sports_amenities_text}")

# Extract Convenience Amenities
convenience_amenities_text = "N/A"
convenience_panels = driver.find_elements(By.XPATH, "//div[@class='panelHeader']/strong[text()='Convenience']")
if convenience_panels:
    try:
        convenience_panel = convenience_panels[0]
        driver.execute_script("arguments[0].click();", convenience_panel)
        time.sleep(2)  # Wait for panel to expand
        convenience_amenities = []
        try:
            convenience_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
            for element in convenience_elements:
                if element.text.strip():
                    convenience_amenities.append(element.text.strip())
        except Exception as e:
            print("Error extracting convenience amenities:", e)
        convenience_amenities_text = "; ".join(convenience_amenities) if convenience_amenities else "N/A"
    except Exception as e:
        print("Convenience panel could not be clicked:", e)
else:
    print("Convenience panel not found.")
print("Convenience Amenities:", convenience_amenities_text)

# Extract Safety Amenities
safety_amenities_text = "N/A"
safety_panels = driver.find_elements(By.XPATH, "//div[@class='panelHeader']/strong[text()='Safety']")
if safety_panels:
    try:
        safety_panel = safety_panels[0]
        driver.execute_script("arguments[0].click();", safety_panel)
        time.sleep(2)  # Wait for panel to expand
        safety_amenities = []
        try:
            safety_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
            for element in safety_elements:
                if element.text.strip():
                    safety_amenities.append(element.text.strip())
        except Exception as e:
            print("Error extracting safety amenities:", e)
        safety_amenities_text = "; ".join(safety_amenities) if safety_amenities else "N/A"
    except Exception as e:
        print("Safety panel could not be clicked:", e)
else:
    print("Safety panel not found.")
print("Safety Amenities:", safety_amenities_text)

# Extract Leisure Amenities
leisure_amenities_text = "N/A"
leisure_panels = driver.find_elements(By.XPATH, "//div[@class='panelHeader']/strong[text()='Leisure']")
if leisure_panels:
    try:
        leisure_panel = leisure_panels[0]
        driver.execute_script("arguments[0].click();", leisure_panel)
        time.sleep(2)  # Wait for panel to expand
        leisure_amenities = []
        try:
            leisure_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
            for element in leisure_elements:
                if element.text.strip():
                    leisure_amenities.append(element.text.strip())
        except Exception as e:
            print("Error extracting leisure amenities:", e)
        leisure_amenities_text = "; ".join(leisure_amenities) if leisure_amenities else "N/A"
    except Exception as e:
        print("Leisure panel could not be clicked:", e)
else:
    print("Leisure panel not found.")

print("Leisure Amenities:", leisure_amenities_text)

#Extract Environment Amenities
environment_amenities_text = "N/A"
environment_panels = driver.find_elements(By.XPATH, "//div[@class='panelHeader']/strong[text()='Environment']")
if environment_panels:
    try:
        environment_panel = environment_panels[0]
        driver.execute_script("arguments[0].click();", environment_panel)
        time.sleep(2)  # Wait for panel to expand
        environment_amenities = []
        try:
            environment_elements = driver.find_elements(By.CSS_SELECTOR, ".panelBody .npAmenitiesTable tbody tr td span")
            for element in environment_elements:
                if element.text.strip():
                    environment_amenities.append(element.text.strip())
        except Exception as e:
            print("Error extracting environment amenities:", e)
        environment_amenities_text = "; ".join(environment_amenities) if environment_amenities else "N/A"
    except Exception as e:
        print("Environment panel could not be clicked:", e)
else:
    print("Environment panel not found.")
print("Environment Amenities:", environment_amenities_text)



# Save data to CSV
csv_filename = "test2.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "XID","Project Name", "Location", "Price Range", "Price Per Sq. Ft",
        "Project Status", "Configurations", "Unit Sizes", "Builder",
        "Total Number of Units", "Project Size", "Launch Date",
        "Completion Date", "Locality", "Micro Market","USP","Builder URL","Builder Experience","Ongoing Projects","Past Projects","RERA Number","Specifications","Sports Amenities","Convenience Amenities","Safety Amenities","Environment Amenities","Leisure Amenities"
    ])
    writer.writerow([
        xid,project_name, location, price_range, price_per_sqft,
        data_dict["Project Status"], data_dict["Configurations"], data_dict["Unit Sizes"],
        data_dict["Builder"], data_dict["Total Number of Units"], data_dict["Project Size"],
        data_dict["Launch Date"], data_dict["Completion Date"],
        data_dict["Locality"], data_dict["Micro Market"], usp, data_dict["Builder URL"], builder_experience, ongoing_projects, past_projects, rera_number, specifications_text, sports_amenities_text, convenience_amenities_text, safety_amenities_text, environment_amenities_text, leisure_amenities_text
    ])

print(f"Data saved to {csv_filename}")

# Close the browser
driver.quit()
