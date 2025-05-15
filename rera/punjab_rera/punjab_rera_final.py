import time
import cv2
import pytesseract
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

# Set up Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\urvashi.aggarwal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Read Registration Numbers from CSV
input_csv = "input.csv"
output_csv = "output.csv"

with open(input_csv, "r") as file:
    reader = csv.reader(file)
    registration_numbers = [row[0] for row in reader]
# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://rera.punjab.gov.in/reraindex/publicview/projectinfo")

# Enter Registration Number
for reg_number in registration_numbers:

    reg_input = driver.find_element(By.ID, "Input_RegdProject_RERAnumberRegistration")  
    reg_input.send_keys(reg_number)  

    # Find CAPTCHA refresh button
    refresh_button = driver.find_element(By.CLASS_NAME, "capcha-refresh")

    # Retry CAPTCHA up to 5 times
    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        print(f"\nAttempt {attempt} of {max_attempts}")

        # Wait for CAPTCHA to Load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "capcha-badge")))
        captcha_element = driver.find_element(By.CLASS_NAME, "capcha-badge")

        #  Take Screenshot of CAPTCHA
        captcha_element.screenshot("captcha.png")
        print(" Screenshot taken for CAPTCHA.")

        # Process CAPTCHA Image for OCR
        image = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
        _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # Improve clarity
        cv2.imwrite("processed_captcha.png", thresh)  # Save processed image for debugging

        #  Extract CAPTCHA Text using OCR
        raw_captcha_text = pytesseract.image_to_string(thresh, config="--psm 6").strip()
        print("🔍 Raw OCR Output:", raw_captcha_text)

        #  Ensure CAPTCHA is exactly 6 characters long
        captcha_text = raw_captcha_text.replace(" ", "")  # Remove spaces
        if len(captcha_text) == 6:  
            print(" Valid CAPTCHA Extracted:", captcha_text)
        else:
            print("OCR Failed: Extracted CAPTCHA is invalid. Refreshing CAPTCHA...")
            refresh_button.click()  # Click the refresh button
            time.sleep(2)  # Wait for new CAPTCHA to load
            continue  # Retry with new CAPTCHA

        #  Enter CAPTCHA Text
        captcha_input = driver.find_element(By.ID, "Input_RegdProject_CaptchaText")
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        #  Click Search Button
        search_button = driver.find_element(By.ID, "btn_SearchProjectSubmit")
        driver.execute_script("arguments[0].click();", search_button)

        time.sleep(5)

        # Check for CAPTCHA failure pop-up
        try:
            pop_up = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "confirm")))
            print("Invalid CAPTCHA detected. Clicking OK and retrying...")
            pop_up.click()  # Click "OK" button to retry
            time.sleep(2)  # Short delay before retrying
            refresh_button.click()  # Click refresh to get a new CAPTCHA
            time.sleep(2)  # Wait for new CAPTCHA
        except:
            print("CAPTCHA Accepted! Proceeding...")
            break  # No pop-up means CAPTCHA was correct

    # Click the "View" button
    try:
        print("\nWaiting for 'View' button to appear...")
        view_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "modalOpenerButtonRegdProject"))
        )
        print(" 'View' button found! Clicking now...")
        driver.execute_script("arguments[0].click();", view_button)
    except:
        print(" 'View' button not found or not clickable. Moving to next registration number.")
         # Move to the next registration number
        # Click the "Clear" button to reset the form
        try:
            clear_button = driver.find_element(By.ID, "btnProjectClear")
            print("Clicking 'Clear' button to reset form...")
            driver.execute_script("arguments[0].click();", clear_button)
            time.sleep(2)  # Allow form reset
        except Exception as e:
            print("Failed to click 'Clear' button:", e)
        continue


    # Wait for the new page to load
    time.sleep(5)

    # Click the "Project Details" tab
    try:
        print("\n Waiting for 'Project Details' tab...")
        project_details_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#Projects']"))
        )
        print("'Project Details' tab found! Clicking now...")
        driver.execute_script("arguments[0].click();", project_details_tab)
    except:
        print(" 'Project Details' tab not found or not clickable. Exiting.")
        continue

    # Wait for the Project Details to load
    time.sleep(3)

    try:
            project_address_label = driver.find_element(By.XPATH, "//td[span[contains(text(), 'Project Address')]]/following-sibling::td/span")
            raw_address = project_address_label.get_attribute("innerHTML")
            project_address = raw_address.replace("<br>", ", ").strip()
            print(f" Project Address: {project_address}")
    except:
            project_address = "N/A"

    try:
        completion_date_label = driver.find_element(By.XPATH, "//td[span[contains(text(), 'Proposed/ Expected Date of Project Completion as specified in Form B')]]/following-sibling::td/span")
        completion_date = completion_date_label.get_attribute("innerHTML").strip()
        print(f" Expected Completion Date: {completion_date}")
    except:
        completion_date = "N/A"

    try:
        #  Locate the label for "Total Area of Land Proposed to be developed (in sqr mtrs)"
        land_area_label = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Total Area of Land Proposed to be developed (in sqr mtrs)')]]"))
        )

        try:
            #  Locate the next sibling <td> containing the actual land area value (no <span> inside)
            land_area_value = land_area_label.find_element(By.XPATH, "./following-sibling::td")

            #  Extract and clean the text
            land_area = land_area_value.text.strip()
            print(f" Total Area Proposed: {land_area} sqr mtrs")

        except Exception as e:
            print(" Could not find the land area value:", e)

    except Exception as e:
        print(" Could not locate the label for 'Total Area of Land Proposed to be developed':", e)

    try:
            # Locate the label for "Area under group housing development excluding common areas and amenities"
            group_housing_area_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Area under group housing development excluding common areas and ameneties')]]"))
            )
            

            try:
                # Locate the next sibling <td> containing the actual group housing area value
                group_housing_area_value = group_housing_area_label.find_element(By.XPATH, "./following-sibling::td")
            
                # Extract and clean the text
                group_housing_area = group_housing_area_value.text.strip()
                print(f" Group Housing Area: {group_housing_area} sqr mtrs")

            except Exception as e:
                print(" Could not find the group housing area value:", e)
                group_housing_area = "N/A"

    except Exception as e:
            print(" Could not locate the label for 'Area under group housing development excluding common areas and amenities':", e)
            group_housing_area = "N/A"

    
    try:
            #  Locate the label for "Area under residential plotted development excluding common areas and amenities"
            residential_plotted_area_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Area under residential plotted development excluding common areas and ameneties')]]"))
            )

            try:
                #  Locate the next sibling <td> containing the actual residential plotted area value
                residential_plotted_area_value = residential_plotted_area_label.find_element(By.XPATH, "./following-sibling::td")

                residential_plotted_area = residential_plotted_area_value.text.strip()
                print(f" Residential Plotted Area: {residential_plotted_area} sqr mtrs")

            except Exception as e:
                print(" Could not find the residential plotted area value:", e)

    except Exception as e:
            print("Could not locate the label for 'Area under residential plotted development excluding common areas and amenities':", e)

    try:
            # Locate the label for "Area under commercial development excluding common areas and amenities"
            commercial_area_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Area under commercial development excluding common areas and ameneties')]]"))
            )

            try:
                # Locate the next sibling <td> containing the actual commercial area value
                commercial_area_value = commercial_area_label.find_element(By.XPATH, "./following-sibling::td")

                # Extract and clean the text
                commercial_area = commercial_area_value.text.strip()
                print(f" Commercial Area: {commercial_area} sqr mtrs")

            except Exception as e:
                print(" Could not find the commercial area value:", e)

    except Exception as e:
            print(" Could not locate the label for 'Area under commercial development excluding common areas and amenities':", e)

    try:
            #  Locate the label for "Area under common amenities servicing the entire project"
            common_amenities_area_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Area under common amenties servicing the entire project')]]"))
            )

            try:
                #  Locate the next sibling <td> containing the actual common amenities area value
                common_amenities_area_value = common_amenities_area_label.find_element(By.XPATH, "./following-sibling::td")

                # Extract and clean the text
                common_amenities_area = common_amenities_area_value.text.strip()
                print(f" Open Area(Common Amenities Area): {common_amenities_area} sqr mtrs")

            except Exception as e:
                print(" Could not find the open area value:", e)

    except Exception as e:
            print(" Could not locate the label for 'Area under common amenities servicing the entire project':", e)

    try:
        print("\n Waiting for 'Project Plan & Facilities' tab...")
        project_plan_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='#Project-plan-facilities']"))
        )
        print(" 'Project Plan & Facilities' tab found! Clicking now...")
        driver.execute_script("arguments[0].click();", project_plan_tab)
    except:
        print(" 'Project Plan & Facilities' tab not found or not clickable.")
        continue

    # Wait for the Project Plan & Facilities details to load
    time.sleep(3)

    # Extract Tower Details
    try:
        div1 = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Project Building/ Tower/ Block Construction & Inventory Details')]"))
        )
        table = div1.find_element(By.XPATH, "./following-sibling::table")

        # Locate the tbody and the first tr
        tbody = table.find_element(By.TAG_NAME, "tbody")
       
        seen_sr_no = set()
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        print(f" Found {len(rows)} rows in the table.")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 1 and cols[0].text.strip().isdigit():
                    sr_no = cols[0].text.strip()

                                # Avoid processing duplicate Sr. No. values (likely sub-rows)
                    if sr_no in seen_sr_no:
                        print(f"Skipping inner sub-row with duplicate Sr. No.: {sr_no}")
                        continue
                            
                   
   
                    try:
                        building_name = cols[1].find_element(By.TAG_NAME, "span").text.strip()
                    except:
                        building_name = "N/A"
                    try:
                        floor_details = cols[2].text.strip()
                    except:
                        floor_details = "N/A"
                    if(building_name !='N/A' ):
                        seen_sr_no.add(sr_no) # Mark this Sr. No. as processed
                        print(f"Extracted: {building_name}, {floor_details}")
                    # Write to the new CSV file
                        # Write headers to the tower details CSV if the file is empty
                    try:
                            with open("tower_details.csv", "r", newline="", encoding="utf-8") as tower_file:
                                if not tower_file.read(1):
                                    with open("tower_details.csv", "w", newline="", encoding="utf-8") as tower_file:
                                        tower_writer = csv.writer(tower_file)
                                        tower_writer.writerow(["Registration Number", "Building Name", "Floor Details"])
                    except FileNotFoundError:
                            with open("tower_details.csv", "w", newline="", encoding="utf-8") as tower_file:
                                tower_writer = csv.writer(tower_file)
                                tower_writer.writerow(["Registration Number", "Building Name", "Floor Details"])

                        # Append data to the tower details CSV
                    if building_name != "N/A":
                        with open("tower_details.csv", "a", newline="", encoding="utf-8") as tower_file:
                                tower_writer = csv.writer(tower_file)
                                tower_writer.writerow([reg_number, building_name, floor_details])
                                print(f"Data Saved to tower_details.csv: {reg_number}, {building_name}, {floor_details}")

    except Exception as e:
        print(" Error while extracting tower details:", e)
        
    # Write headers to the output CSV if the file is empty
    try:
        with open(output_csv, "r", newline="", encoding="utf-8") as file:
            if not file.read(1):
                with open(output_csv, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Registration Number", "Project Address", "Expected Completion Date", "Total Area Proposed", "Group Housing Area", "Residential Plotted Area", "Commercial Area", "Common Amenities Area"])
    except FileNotFoundError:
        with open(output_csv, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Registration Number", "Project Address", "Expected Completion Date", "Total Area Proposed", "Group Housing Area", "Residential Plotted Area", "Commercial Area", "Common Amenities Area"])

    # Write data to the output CSV
    with open(output_csv, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([reg_number, project_address, completion_date, land_area, group_housing_area, residential_plotted_area, commercial_area, common_amenities_area])
    print(f"Data Saved: {reg_number}, {project_address}, {completion_date}, {land_area}, {group_housing_area}, {residential_plotted_area}, {commercial_area}, {common_amenities_area}")

    try:
            close_button = driver.find_element(By.XPATH, "//button[@class='close' and @data-dismiss='modal']")
            close_button.click()
            time.sleep(2)  # Allow modal to close
    except:
            print("Failed to close details popup.")

    try:
           
            clear_button = driver.find_element(By.ID, "btnProjectClear")
            print(" Clicking 'Clear' button to reset form...")
            driver.execute_script("arguments[0].click();", clear_button)
            time.sleep(2)  # Allow form reset
    except:
            print(" Failed to click 'Clear' button.")

    print("\n Process completed for Registration Number:", reg_number)


    

print("\n Process completed successfully!")


time.sleep(10) # Allow user to view the final page
driver.quit()
