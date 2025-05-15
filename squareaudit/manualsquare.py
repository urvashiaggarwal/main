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
driver.set_page_load_timeout(5)  # Set timeout to 180 seconds

# Read URLs and XIDs from CSV
input_csv_filename = "further21.csv"
urls_xids = []

# Read the input CSV and extract XID and Square Yards Phase URLs
with open(input_csv_filename, "r", newline="", encoding="utf-8") as file:
    print("Reading CSV file...")
    reader = csv.DictReader(file)
    for row in reader:
        print(row)
        xid = row['XID']
        #phase=row["phase"]
        url=row["Comp 3"]    
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url  # Add http:// if missing
            if url.endswith("/project"):
                urls_xids.append((xid, url))

# Option to start from a specific index
urls_xids = urls_xids[:]
#urls_xids=[("XID123", "https://www.squareyards.com/noida-residential-property/aba-county-107/10931/project", "Phase 1"),]

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
            time.sleep(2)  # Wait for panel to expand

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
            price_per_sqft = driver.find_element(By.CSS_SELECTOR, "div.npPerSqft").text.strip()
            price_per_sqft = price_per_sqft.replace("₹", "Rs").strip()
        except Exception:
            price_per_sqft = "N/A"
        
        if usp == "N/A":
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
                    usp=[]

                usp = ",".join(usps)
                print("USP:", usp)
                close_button = driver.find_element(By.CSS_SELECTOR, "button.rightCloseButton")
                driver.execute_script("arguments[0].click();", close_button)

            except Exception:
                usp = "N/A"

       

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
                time.sleep(2)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(2)

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

                try:
                    # Scroll to the section to ensure it's visible
                    label = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='expendBox']"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView();", label)

                    # Click the label to expand
                    driver.execute_script("arguments[0].click();", label)
                    time.sleep(1)

                    # Wait and fetch the expanded description text
                    description = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".whiteBody .descriptionBox p"))
                    )
                    
                   
                    builder_info= description.text.strip()

                except Exception as e:
                    builder_info = "N/A"
                    print(f"Error: {e}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                builder_experience = "N/A"
                ongoing_projects = "N/A"
                past_projects = "N/A"
                builder_info = "N/A"
        else:
            builder_experience = "N/A"
            ongoing_projects = "N/A"
            past_projects = "N/A"
            builder_info = "N/A"

        try:
            price_list_tab = driver.find_element(By.XPATH, "//li[@data-tab='npPriceList']")
            driver.execute_script("arguments[0].click();", price_list_tab)
            time.sleep(3)
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

                try:
                    unit_type = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) strong").text.strip()
                except Exception:
                    unit_type = "N/A"


                try:
                    price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                    price = price.replace("₹", "Rs").strip()
                except Exception:
                    price = "N/A"

                area_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(2) .bhkSqFt.Detail_NewProject_D11")
                area = area_element.find_element(By.CSS_SELECTOR, "span").text.strip()
                print(area)
                try:
                    area_type = area_element.find_element(By.CSS_SELECTOR, ".saleable.Detail_NewProject_D11").text.strip()
                    print(area_type)
                except Exception:
                    area_type = "N/A"
                floor_plans.append((unit_type, area, price, area_type))
            except Exception:
                continue

        floor_plan_csv_filename = "fp.csv"
        with open(floor_plan_csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for plan in floor_plans:
                print("Floor Plan:", plan)
                writer.writerow([xid, project_name, *plan])

        print(f"Floor plan data saved to {floor_plan_csv_filename}")

        try:
            rera_panel = driver.find_element(By.CSS_SELECTOR, ".panelHeader[data-reraid]")
            rera_number = rera_panel.get_attribute("data-reraid").strip()
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
                time.sleep(2)  # Allow time for expansion
            
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

        
        convenience_amenities_text = extract_amenities("Convenience")
        

        safety_amenities_text = extract_amenities("Safety")
        

        leisure_amenities_text = extract_amenities("Leisure")
        

        environment_amenities_text = extract_amenities("Environment")
       


        amenities={sports_amenities_text, convenience_amenities_text, safety_amenities_text, environment_amenities_text, leisure_amenities_text}
        # Convert amenities set to a string
        amenities_text = "; ".join(amenities) if amenities else "N/A"
        print("Amenities:", amenities_text)
        

        amenity_count = len(amenities_text.split(";")) if amenities_text != "N/A" else 0
        print("Amenities Count:", amenity_count)

        # Count all visible image thumbnails
        all_images = driver.find_elements(By.CSS_SELECTOR, ".npMidBox .npFigure.loadGallery img")
        image_count = len(all_images)

        # Extract "+X Photos" from badge (if present)
        try:
            badge_photo_text = driver.find_element(By.CSS_SELECTOR, ".npFigure.moreImages .badge").text
            if '+' in badge_photo_text and 'Photos' in badge_photo_text:
                extra_photos = int(badge_photo_text.split('+')[1].split()[0])
                image_count += extra_photos
        except:
            pass  # No badge, just stick with found images

        # Include the main large image
        try:
            driver.find_element(By.CSS_SELECTOR, ".npLargeBox .npFigure img")
            image_count += 1
        except:
            pass  # main image not present

        video_count = 0
        try:
            badge_video_text = driver.find_element(By.CSS_SELECTOR, ".npFigure.video .badge").text
            if '+' in badge_video_text and 'Video' in badge_video_text:
                video_count = int(badge_video_text.split('+')[1].split()[0])
        except:
            pass  # no video badge

        print("Image Count:", image_count)
        print("Video Count:", video_count)

        
        market_supply_sections = driver.find_elements(By.CSS_SELECTOR, ".npPiBox")

        price_trend = None

        for section in market_supply_sections:
            # Make sure this section is for 'Market Supply'
            header = section.find_element(By.CLASS_NAME, "npPiHeader").text
            print("Header:", header)
            if "Market Supply" in header:
                items = section.find_elements(By.CLASS_NAME, "npPiItem")
                for item in items:
                    print("Item Text:", item.text)
                    if "₹" in item.text:
                        price_trend = item.text
                        break
                break

        print("Average Price (per sq.ft):", price_trend)

        try:
            # Wait until the rating section is present
            rating_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".ratingBox"))
            )
            rating_count = driver.find_element(By.CSS_SELECTOR, ".ratingBox .strong").text.strip()

            # Output
            
            print("Rating Count:", rating_count)

        except Exception as e:
            rating_count = "N/A"
            print("Error:", e)

            
        try:
            ul_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "nearLocation"))
            )

            # Get all <li> elements under the <ul>
            landmarks=[]
            landmark_list_items = ul_element.find_elements(By.TAG_NAME, "li")
            #landmark_rows = driver.find_elements(By.CSS_SELECTOR, ".nearLocation .npPiItem")
            # Extract the text from each <li> element
            for item in landmark_list_items:
                text = item.text.strip()
                if text:
                    print(text)
            c=0
            #Click on each landmark item to expand details (if clickable)
            processed_landmarks = set()  # Track processed landmark categories

            for item in landmark_list_items:
                try:
                    category = item.text.strip()
                    if category in processed_landmarks:
                        continue  # Skip if already processed

                    driver.execute_script("arguments[0].click();", item)
                    print("Clicked on landmark item.")
                    time.sleep(2)

                    # Extract details
                    item_rows = driver.find_elements(By.CSS_SELECTOR, ".nearDistanceBox.active tbody tr")
                    item_list = []
                    item_set = set()  # Track unique items in the current landmark

                    for row in item_rows:
                        try:
                            name = row.find_element(By.CSS_SELECTOR, ".distanceTitle").text.strip()
                            distance = row.find_element(By.CSS_SELECTOR, ".distance span").text.strip()
                            item_key = (name, distance)  # Use a tuple as a unique identifier
                            if item_key not in item_set:
                                item_list.append({"name": name, "distance": distance})
                                item_set.add(item_key)
                        except:
                            continue

                    if not any(l['category'] == category for l in landmarks):
                        landmarks.append({"category": category, "details": item_list})
                    processed_landmarks.add(category)  # Mark as processed

                    # Collapse the section
                    try:
                        view_less_button = driver.find_element(By.CSS_SELECTOR, ".nearDistanceBox.active .npBtnBox button")
                        driver.execute_script("arguments[0].click();", view_less_button)
                        print("Clicked on View Less button.")
                        time.sleep(2)
                    except Exception as e:
                        print(f"Error clicking on View Less button: {e}")

                except Exception as click_error:
                    print(f"Error clicking on landmark item: {click_error}")

            #print("Landmarks:", landmarks)
            # Convert landmarks list to a string format
            landmarks_text = "; ".join([f"{item['category']}: {', '.join([f'{detail['name']} ({detail['distance']})' for detail in item['details']])}" for item in landmarks]) if landmarks else "N/A"
            print("Landmarks:", landmarks_text)

        except Exception as e:
            print(f"An error occurred: {e}")
            landmarks_text = "N/A"
        try:
            # Locate the builder's total projects and experience
            total_projects_element = driver.find_element(By.XPATH, "//ul[@class='npTotalProjectList']/li[contains(text(), 'Total Projects')]/strong")
            total_projects = total_projects_element.text.strip()

           

            print("Total Projects:", total_projects)
           

        except Exception as e:
            total_projects = "N/A"
           
            print("Error extracting builder's total projects or experience:", e)

        try:
            # Wait until the "Configurations" section loads
            config = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//strong[text()='Configurations']/following-sibling::ol/li[1]/span"))
            )
            config=config.text.strip()

            print("Configurations:", config)  # Output: 2, 3 BHK Flats

        except Exception as e:
            config = "N/A"
            print("Error:", e)

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


        csv_filename = "squareyards_further_21.csv"
        file_exists = os.path.isfile(csv_filename)
        
        with open(csv_filename, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "XID","URL", "Project Name","Builder Name", "Location", "Price Range", "Price per Sqft"
                    , "Configurations","Completion Date", "Unit Size Range","LandMarks","Project Size",
                     "Launch Date","RERA Number","Total Number of Units","USP","BHK" ,"Amenity Count"
                     ,"Amenities", "Specifications","Photo Count","Video Count","Rating count","Price Trend"
                     , "Builder URL", "Builder Experience","Total Projects",
                    "Ongoing Projects", "Past Projects","Builder Info","Project Status"
                   
                ])
            writer.writerow([
                xid,url, project_name,data_dict["Builder"], location, price_range, price_per_sqft,
                 config,data_dict["Completion Date"], data_dict["Unit Sizes"],landmarks_text,data_dict["Project Size"]
                ,data_dict["Launch Date"],rera_number, data_dict["Total Number of Units"], usp,data_dict["Configurations"],amenity_count,amenities_text,specifications_text,image_count,video_count,
                rating_count,price_trend,  data_dict["Builder URL"],
                builder_experience,total_projects , ongoing_projects, past_projects,builder_info,project_status
               
            ])

        print(f"Data saved to {csv_filename}")

    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Close the browser
driver.quit()

