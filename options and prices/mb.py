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
input_file = "new21.csv"
output_file = "magicbricks_further_21.csv"
floor_plans_csv = "floor_magicbricks_21.csv"

# Read the input CSV and extract XID and Square Yards Phase URLs

urls_xids = []

# Read the input CSV and extract XID and Square Yards Phase URLs
with open(input_file, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        xid = row["XID"]
        
        url = row["Comp 1"]
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url  # Add http:// if missing
            if 'pdpid' in url:
                urls_xids.append((xid, url))

urls_xids=urls_xids[:]

# # Option to start from a specific index
# urls_xids = urls_xids[102:]
# urls_xids = [("XID123", "https://www.magicbricks.com/siddha-galaxia-phase-2-rajarhat-kolkata-pdpid-4d4235303735303039", "1")]
# Prepare output data list
data_list = []

# Iterate over each XID and its corresponding Square Yards Phase URLs
for xid, url in urls_xids:
    floor_plans = []
    print(f"Opening URL: {url} for XID: {xid} ")
    driver.get(url)
    time.sleep(3)  # Wait for elements to load

    operating_cities = "N/A"
    experience = "N/A"
    deals_property = "N/A"
    office_address = "N/A"
    total_projects = "N/A"
    completed_projects = "N/A"
    projects_ongoing = "N/A"
    builder_info = "N/A"
    joined_usps = "N/A"
    joined_location_advantages = "N/A"
    specifications_text = "N/A"

    # Extracting data
    try:
        project_name = driver.find_element(By.CSS_SELECTOR, ".pdp__name h1").text.strip()
    except:
        project_name = "N/A"

    # Extract image count
    try:
          
        img_count = driver.find_element(By.CSS_SELECTOR, ".pdp__imgcount").get_attribute("textContent").strip()
        print("Image Count:", img_count)
    except:
        img_count = "N/A"

    

    try:
        builder = driver.find_element(By.CSS_SELECTOR, "div.pdp__developerName").text.replace("By ", "").strip()
    except:
        builder = "N/A"

    try:
        developer_link_element = driver.find_element(By.CSS_SELECTOR, "div.about-developer__builder__heading a")
        developer_link = developer_link_element.get_attribute("href")
    except:
        developer_link = "N/A"

    try:
        total_projects_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Total Projects')]/following-sibling::div")
        total_projects = total_projects_element.text.strip()
        print(total_projects)
    except:
        total_projects = "N/A"

    try:
        completed_projects_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Projects Completed')]/following-sibling::div")
        completed_projects = completed_projects_element.text.strip()
        print(completed_projects)
    except:
        completed_projects = "N/A"

    try:
        projects_ongoing_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Projects Ongoing')]/following-sibling::div")
        projects_ongoing = projects_ongoing_element.text.strip()  
        print(projects_ongoing)  
    except:
        projects_ongoing = "N/A"

    try:
        
        driver.execute_script("arguments[0].click();", developer_link_element)
        time.sleep(3)  # Wait for builder section to load
        print("Clicked 'Explore Builder' successfully.")
        # Switch to the new tab
        driver.switch_to.window(driver.window_handles[1])
        
        try:
            operating_cities_element = driver.find_element(By.CLASS_NAME, "dev-detail__overview__operating--less-content")
            operating_cities = operating_cities_element.text.strip()
        except:
            operating_cities = "N/A"

        try:
            # Get all label-value item pairs
            items = driver.find_elements(By.CSS_SELECTOR, ".dev-detail__overview__deals__list--item")

            experience_text = "N/A"
            for item in items:
                label = item.find_element(By.CSS_SELECTOR, ".dev-detail__overview__deals__list--item--label").text.strip()
                value = item.find_element(By.CSS_SELECTOR, ".dev-detail__overview__deals__list--item--value").text.strip()
                if "experience" in label.lower():
                    experience_text = value
                    break

        except Exception as e:
            experience_text = "N/A"
            print("Error:", e)



        try:
            deals_property_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Deals in Property Type')]/following-sibling::div")
            deals_property = deals_property_element.text.strip()
        except:
            deals_property = "N/A"

        try:
            office_address_element = driver.find_element(By.CSS_SELECTOR, "div.dev-detail__overview__address--value")
            office_address = office_address_element.text.strip()
        except:
            office_address = "N/A"


        # Close the new tab and switch back to the original tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        print(f"Operating in Cities: {operating_cities}")
    except:
        print("'Explore Builder' link not found or could not be clicked.")

    try:
        address = driver.find_element(By.CSS_SELECTOR, "div.pdp__location").text.strip()
    except:
        address = "N/A"

    try:
        # price_range_element = driver.find_element(By.CSS_SELECTOR, "div.pdp__pricecard--price")
        # price_range = price_range_element.text.strip()
        # price_range = price_range.replace("₹", "Rs").strip()
        # print(price_range)
        price = driver.find_element(By.XPATH, '//*[@id="nav-overview"]/div[2]/div[1]/div[1]/div').text.strip()
        price = price.replace("₹", "Rs").strip()
        print(price)
    except:
        price = "N/A"

    try:
        flat_type = driver.find_element(By.CSS_SELECTOR, "div.pdp__bhkposs--data span.pdp__bhkposs--bhk").text.strip()
    except:
        flat_type = "N/A"

    # Extracting additional property details
    property_details = {
        "Price/sq.ft": "N/A",
        "Total Units": "N/A",
        "Project Size": "N/A",
        #"Launch Date": "N/A",
        "BHK": "N/A"
    }

    try:
        items = driver.find_elements(By.CSS_SELECTOR, "div.pdp__prunitar--item")
        for item in items:
            try:
                label = item.find_element(By.CLASS_NAME, "pdp__prunitar--label").text.strip()
                value = item.find_element(By.CLASS_NAME, "pdp__prunitar--data").text.strip()
                if label in property_details:
                    if(label == "Price/sq.ft"):
                        value = value.replace("₹", "Rs").strip()
                    property_details[label] = value
            except:
                continue  # Skip if elements not found
    except:
        pass  # If no property details found, continue with "N/A"

    try:
        super_area_element = driver.find_element(By.CSS_SELECTOR, "div.pdp__florpripln--brief span.text-semibold")
        super_area = super_area_element.text.strip()
    except:
        try:
            super_area_element = driver.find_element(By.CSS_SELECTOR, "span.pdp__prop__card__bhk")
            super_area_text = super_area_element.text.strip()
            super_area = super_area_text.split()[-2] + " " + super_area_text.split()[-1]  # Extract the sq.ft part
        except:
            super_area = "N/A"



    try:
        view_amenities = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'View Amenities')]"))
        )
        driver.execute_script("arguments[0].click();", view_amenities)
        time.sleep(3)  # Wait for amenities section to load
    except:
        print("View Amenities' button not found or could not be clicked.")
    

    amenities = []
    try:
        amenities_elements = driver.find_elements(By.CSS_SELECTOR, "div.pdp__maproject__amentext")
        amenities = [amenity.text.strip() for amenity in amenities_elements if amenity.text.strip()]
    except:
        pass

    amenity_count = len(amenities)

    try:
        back_button = driver.find_element(By.XPATH, '//*[@id="moredetails"]/div[6]/div[1]/div[1]')
        driver.execute_script("arguments[0].click();", back_button)
        print(" Back button clicked successfully.")
    except:
        print(" Back button not found.")

    try:
        usp_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Why Buy in')]"))
        )

        # Locate the parent div that contains the USPs
        usp_section = usp_header.find_element(By.XPATH, "./following-sibling::div")

        # Extract all list items (USPs + Location Advantages)
        usp_elements = usp_section.find_elements(By.TAG_NAME, "li")

        usps = []

        for li in usp_elements:
            text = li.text.strip()
            if text:
                usps.append(text)

        # Join all USPs including location advantages into a single string
        joined_usps = " | ".join(usps)
        print(f"USPs: {joined_usps}")
    except:
        joined_usps = "N/A"

    try:
        print("Extracting Specifications...")

        # Locate the specification section
        try:
            spec_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'pdp__maproject__spaecdd')]/div[contains(@class, 'pdp__maproject__spaceContent')]"))
            )
            print(" Specifications section found.")
            specifications = []

            # Case 1: UL with <br> separators
            try:
                all_ul_elements = spec_section.find_elements(By.XPATH, ".//ul")
                for ul in all_ul_elements:
                    parent_text = ul.find_element(By.XPATH, "./preceding-sibling::text()").strip() if ul.find_elements(By.XPATH, "./preceding-sibling::text()") else ""
                    li_elements = ul.find_elements(By.TAG_NAME, "li")
                    
                    if li_elements:
                        section_title = parent_text 
                        if section_title:
                            extracted_text = [f"{section_title}: {li.text.strip()}" for li in li_elements if li.text.strip()]
                        else:
                            extracted_text = [li.text.strip() for li in li_elements if li.text.strip()]
                        specifications.extend(extracted_text)
                        break  # Stop checking other cases if extraction is successful

            except Exception as e:
                print(f"Error in Nested UL Extraction: {str(e)}")

        # Case 2: Extract specifications from <ul> with <br> separators (if UL exists and Case 1 failed)
            if not specifications:
                try:
                    ul_element = spec_section.find_element(By.TAG_NAME, "ul")
                    raw_text = ul_element.get_attribute("innerHTML")
                    if "<br>" in raw_text:
                        extracted_text = [line.strip() for line in raw_text.split("<br>") if line.strip()]
                        specifications.extend(extracted_text)
        
                except:
                    pass  # If not found, move to next case

            if not specifications:
                try:
                    ul_element = spec_section.find_element(By.TAG_NAME, "ul")  # Find UL containing divs
                    div_elements = ul_element.find_elements(By.TAG_NAME, "div")  # Get all divs inside UL

                    current_category = None
                    current_subcategory = None

                    for div in div_elements:
                        text = div.text.strip()

                        if text:
                            if not current_category:
                                current_category = text  # First div is main category
                            elif not current_subcategory:
                                current_subcategory = text  # Second div is subcategory
                            else:
                                # Third div onwards is the value
                                formatted_entry = f"{current_category} → {current_subcategory} → {text}"
                                specifications.append(formatted_entry)
                                current_subcategory = None  # Reset for the next subcategory
                except Exception as e:
                    print(f"Error in UL with Div Extraction: {str(e)}")


            

            # Convert list to a single string with newlines
            specifications_text = "\n".join(specifications) if specifications else "N/A"

        except:
            specifications_text = "N/A"

    except:
        specifications = "N/A"

    try:
        read_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "readmore"))
        )
        driver.execute_script("arguments[0].click();", read_more_button)
        time.sleep(2)  # Wait for expanded content to load
        print("Clicked 'Read More' successfully.")
        try:
            builder_info_element = driver.find_element(By.CSS_SELECTOR, "div.popup__body.aboutdeveloper")
            builder_info = builder_info_element.text.strip()
        except:
            builder_info = "N/A"
        try:
            back_button = driver.find_element(By.CSS_SELECTOR, "div.popup__header__back")
            driver.execute_script("arguments[0].click();", back_button)
            print("Back button clicked successfully.")
        except:
            print("Back button not found.")
    except:
        builder_info = "N/A"
        print("'Read More' button not found or could not be clicked.")


    try:
        read_more = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Read More')]"))
        )
        driver.execute_script("arguments[0].click();", read_more)
        time.sleep(2)  # Wait for expanded content to load
        print(" Clicked 'Read More' successfully.")
    except:
        print(" 'Read More' button not found or could not be clicked.")

    property_details2 = {
    "Project Type": "N/A",
    "Property Type": "N/A",
    "Status": "N/A",
    "Launch Date": "N/A",
    "Possession Date": "N/A",
    "Total Towers": "N/A",
    }

    try:
        table_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in table_rows:
            try:
                key = row.find_element(By.TAG_NAME, "td").text.strip()
                value = row.find_elements(By.TAG_NAME, "td")[1].text.strip()
            
                if "Project Type" in key:
                    property_details2["Project Type"] = value
                elif "Property Types" in key:
                    property_details2["Property Type"] = value
                elif "Status" in key:
                    property_details2["Status"] = value
                elif "Launch Date" in key:
                    property_details2["Launch Date"] = value
                elif "Possession Date" in key:
                    property_details2["Possession Date"] = value
                elif "Towers" in key:
                    property_details2["Total Towers"] = value
            except:
                continue
    except:
        print(" Table data not found.")


    # Click Back Button After "Read More"
    try:
        back_button = driver.find_element(By.CSS_SELECTOR, "div.popup__header__back")
        driver.execute_script("arguments[0].click();", back_button)
    
        print(" Back button clicked successfully.")
    except:
        print(" Back button not found.")

    try:
        
        print("Extracting Floor Plans...")
# Locate the main container with class 'pdp__florpripln__cards'
        try:
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
                        floor_plans.append([xid, unit_type or "Type Not Available", unit_size or "Size Not Available", area_type or "Area Not Available", price or "Price Not Available", possession_date or "Possession Not Available"])

                    
                    
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
                            floor_plans.append([xid,  unit_type, unit_size, "Area Not Available", price, possession_date])
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

    

    # Extract review count and rating
    try:
        review_section = driver.find_element(By.CSS_SELECTOR, "div.pdp__review")
        review_count_element = review_section.find_element(By.CSS_SELECTOR, "a.pdp__review--count")
        review_count = review_count_element.text.split()[0]  # Extract the number of reviews
        print(f"Review Count: {review_count}")

    except:
        review_count = "N/A"
        
    landmarks_dict = {}

    try:
        landmark_section = driver.find_element(By.ID, "nearbylandmarksWeb")
        cards = landmark_section.find_elements(By.CLASS_NAME, "pdp__landmarks__card")
        
        for card in cards:
            try:
                category = card.find_element(By.CLASS_NAME, "pdp__landmarks__card__head").text.strip()
                wraps = card.find_elements(By.CLASS_NAME, "pdp__landmarks__card--wrap")
                
                landmarks = []
                for wrap in wraps:
                    name = wrap.find_element(By.CLASS_NAME, "pdp__landmarks__card__item").text.strip()
                    distance = wrap.find_element(By.CLASS_NAME, "pdp__landmarks__card__item--bold").text.strip()
                    landmarks.append(f"{name} {distance}")
                
                landmarks_dict[category] = ", ".join(landmarks)
            except:
                continue
    except Exception as e:
        print("❌ Error extracting landmarks:", e)

    # Format into single string: Category: landmarks...
    formatted_landmarks = " | ".join([f"{cat}: {places}" for cat, places in landmarks_dict.items()])
    print("Landmarks:", formatted_landmarks)

  
    try:
        # Wait for presence of multiple FAQ answer elements
        faq_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "pdp__faq__ans"))
        )

        rera_number = "Not found"

        # Loop through each element and find the one with RERA info
        for elem in faq_elements:
            text = elem.text.strip()
            if "RERA number" in text:
                match = re.search(r'\[([A-Z0-9/\-]+)', text)
                if match:
                    rera_number = match.group(1)
                    break  # Exit after finding the first valid RERA number

    except Exception as e:
        rera_number = "N/A"
        print("Error:", e)

    print("RERA Number:", rera_number)

    try:
    # Wait until the span with class 'sarange' is available
        super_area_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sarange"))
        )

        # Extract the inner span that contains the value
        area_text = super_area_element.find_element(By.CLASS_NAME, "text-semibold").text.strip()

    except Exception as e:
        area_text = "N/A"
        print("Error:", e)


    # Append data to list
    data_list.append([
        xid, url, project_name, builder,address,price,property_details["Price/sq.ft"],property_details2["Property Type"],property_details2["Possession Date"],formatted_landmarks,property_details["Project Size"],area_text,property_details2["Launch Date"],rera_number,property_details2["Total Towers"], property_details["Total Units"],joined_usps,flat_type, amenity_count,", ".join(amenities),img_count,specifications_text,review_count,experience_text, total_projects, completed_projects, projects_ongoing, builder_info,property_details2["Status"] ])

    # Save to CSV simultaneously
    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Check if file is empty to write header
            writer.writerow([
                "XID", "URL", "Project Name", "Builder Name","Location","Price Range","Price psft","Property Type","Possesion Date","LandMarks","Project Size","Size Range","Launch Date","RERA Number","Tower Count","Unit Count","USP","BHK","Amenity Count","Amenities","Image Count","Specifications","Review Count","Builder Experience", "Builder Total Projects", "Builder Ready to Move Projects", "Builder Ongoing Projects", "Builder Info","Project Status"])
        writer.writerow(data_list[-1])

    with open(floor_plans_csv, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if file.tell() == 0:  # Check if file is empty to write header
            writer.writerow(["XID", "Unit Type", "Unit Size", "Area Type", "Price", "Possession Date"])
        # Write data
        writer.writerows(floor_plans)

print(f" Data extraction complete. Results appended in {output_file}")

driver.quit()
 
 