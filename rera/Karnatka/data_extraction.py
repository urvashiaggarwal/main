import glob
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import re, os, time, json
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv,os,requests
from pathlib import Path


HTML_PAGE_make_dir = os.path.expanduser("~/Downloads")
chrome_options = webdriver.ChromeOptions() 
settings = {"recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF", "version": 2,"isCssBackgroundEnabled": True,"margins":0  }
prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings),
         "savefile.default_directory": HTML_PAGE_make_dir}
chrome_options.add_experimental_option('prefs', prefs)
chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--kiosk-printing')
 
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

default_download_dir = str(Path.home() / "Downloads")  
destination_dir = "downloaded_pdfs"
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)
driver.get("https://rera.karnataka.gov.in/home?language=en")
time.sleep(1)
driver.maximize_window()
driver.find_element(By.XPATH, '//*[@id="main_nav"]/ul[2]/li[5]/a').click()
time.sleep(1)
driver.find_element(By.XPATH, '//*[@id="main_nav"]/ul[2]/li[5]/ul/li[1]/a').click()
ids_group = []
cnt = 0
cc="NO"
wait = WebDriverWait(driver, 10)
c=0
# Function to download files
target_texts= [
                    "Area Development Plan of Project Area",
                    "Brochure of Current Project",
                    "Project Specification",
                    "Project Photo Uploaded"
                ]
 
def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)  
 

def download_FP_with_ctrl_s(url, textName, reg_no):

    target_folder = os.path.abspath("downloaded_pdfs")
    target_file = f"{clean_filename(textName)} {clean_filename(reg_no)}.pdf"

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
   
    # Create a temporary download folder
    download_folder = os.path.abspath("temp_downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)  
   
    # Simulate Ctrl + S
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
    time.sleep(10)  
   
    driver.quit()
   
    # Find the most recently downloaded file
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
       
        # Move and rename the file
        new_path = os.path.join(target_folder, target_file)
        os.rename(latest_file, new_path)
        print(f"PDF downloaded and saved as {new_path}")
    else:
        print("No files were downloaded.")

    if os.path.exists(download_folder):
        os.rmdir(download_folder)

def download_image(url, file_path):
    response = requests.get(url,verify=False)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded and saved as {file_path}")
    else:
        print(f"Failed to download image from {url}. Status code: {response.status_code}")


with open("k-total-units (1).csv","r") as csvfile:
    records  = csv.reader(csvfile,delimiter=",")
    next(records)
    for row in records:
        if len(row) == 0:
            continue
        time.sleep(2)
        xid = row[0]
        
        print(xid)
        driver.find_element(By.ID, 'regNo2').send_keys(Keys.CONTROL, 'a')
        driver.find_element(By.ID, 'regNo2').send_keys(xid)
        driver.find_element(By.NAME, 'btn1').click()
        time.sleep(4)
        fileName = xid.replace(r'/', '-')
        time.sleep(3)
        proj_name = driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[6]').text
        prom_name = driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[5]').text
        proj_status = driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[7]').text
        proj_district = driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[8]').text
        try:
            driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[4]/b/a').click()
            time.sleep(1)
        except:
            continue
        time.sleep(3)
        try:
            driver.find_element(By.XPATH, "//a[contains(text(), 'Promoter Details')]").click()
        except:
            pass
        try:
            promtor_type_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class, "row") and contains(., "Promoter Type")]/div[2]/p')
                )
            )
            promoter_type = promtor_type_element.text.strip()
        except:
            promtor_type_element = driver.find_element(By.XPATH, '//div[contains(@class, "row") and (contains(., "Type of Firm") or contains(.,"Firm Type"))]/div[2]/p')
                
            promoter_type = promtor_type_element.text.strip()
        
        driver.find_element(By.XPATH, "//a[contains(text(), 'Project Details')]").click()
        time.sleep(1)

        project_type_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class, "row") and contains(., "Project Type")]/div[2]/p')
            )
        )
        project_type = project_type_element.text.strip()

        project_status_element = driver.find_element(
            By.XPATH, '//div[contains(@class, "row") and contains(., "Project Status")]/div[4]/p'
        )
        project_status = project_status_element.text.strip()

        try:
            project_propCOmp_element = driver.find_element(
                By.XPATH, '//div[contains(@class, "row") and contains(., "Proposed Project Completion Date")]/div[4]/p'
            )
        except:
            project_propCOmp_element = driver.find_element(
                By.XPATH, '//div[contains(@class, "row") and contains(., "Proposed Completion Date")]/div[4]/p'
            )
        project_comp_date = project_propCOmp_element.text.strip()

        project_address_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class, "row") and contains(., "Project Address")]/div[2]/p')
            )
        )
        project_address = project_address_element.text.strip()
    
        try:
            inventory_type = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[contains(@class, "row") and contains(., "Type of Inventory")]/div[2]/p')
                )
            ).text.strip()
        except:
            inventory_type = ""
        
        try:
            no_of_inventory = driver.find_element(
                By.XPATH, '//div[contains(@class, "row") and contains(., "No of Inventory")]/div[4]/p'
            ).text.strip()
        except:
            no_of_inventory = ""
        
        try:
            carpet_area = driver.find_element(
            By.XPATH, '//div[contains(@class, "row") and contains(., "Carpet Area (Sq Mtr)")]/div[2]/p'
            ).text.strip()
        except:
           carpet_area = ""
       
        try:
            total_open_area = driver.find_element(
            By.XPATH, '//div[contains(@class, "row") and contains(., "Total Open Area (Sq Mtr)")]/div[2]/p'
            ).text.strip()
        except:
           total_open_area = ""
     
        try:
            total_area_land = driver.find_element(
            By.XPATH, '//div[contains(@class, "row") and contains(., "Total Area Of Land (Sq Mtr)")]/div[2]/p'
            ).text.strip()
        except:
           total_area_land = ""
        

        try:
            balcony_area = driver.find_element(
                By.XPATH, '//div[contains(@class, "row") and contains(., "Area of exclusive balcony/verandah")]/div[4]/p'
            ).text.strip()
        except:
            balcony_area = ''

        try:
            terrace_area = driver.find_element(
                By.XPATH, '//div[contains(@class, "row") and contains(., "Area of exclusive open terrace if any")]/div[2]/p'
            ).text.strip()
        except:
            terrace_area = ""
       
        try:
           
            section_title = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[contains(text(), "Architects")]')
                )
            )
            print("Architects section found!")
            
            
            arch_name = driver.find_element(
                By.XPATH, '//*[contains(text(), "Architects")]/../../following-sibling::div//div[contains(@class, "row") and contains(., "Name")]/div[2]/p'
            ).text.strip()
            print(f"Architect's name: {arch_name}")
        except:
            arch_name = ""
        try:    
            num_projects_completed = driver.find_element(
                By.XPATH, '../../following-sibling::div//div[contains(@class, "row") and contains(., "Number of Project Completed")]/div[4]/p'
            ).text.strip()
        except:
            num_projects_completed = "" 

        try:
            driver.find_element(By.XPATH, "//a[contains(text(), 'Uploaded Documents')]").click()
            time.sleep(1)
            try:
                for target_text in target_texts:
                    try:
                      
                        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
                        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{target_text}')]")
                        
                        if elements:
                            print(f"Text '{target_text}' found!")

                            # Find the next link and simulate a click
                            next_link = elements[0].find_element(By.XPATH, ".//following::a[1]")
                            pdf_url = next_link.get_attribute("href")
                            print(f"Clicking link for '{target_text}'...")
                            if target_text == "Project Photo Uploaded":
                                    file_extension = ".jpg" 
                                    file_name = f"{clean_filename(xid)}_Project_Photo{file_extension}"
                                    file_path = os.path.join(destination_dir, file_name)
                                    download_image(pdf_url, file_path)
                            else:
                                download_FP_with_ctrl_s(pdf_url, target_text, xid)
                            
                            driver.switch_to.window(driver.window_handles[0])
                        else:
                            print(f"Text '{target_text}' not found on the page.")

                    except Exception as e:
                        print(f"An error occurred while processing '{target_text}':", e)

            except Exception as e:
                print("An error occurred:", e)

                
        except:
            pass
        time.sleep(5)
        
        
         
        try:

            total_flats_value = ""
            occupancy_date_value = ""
            tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Completion Details')]")
            
            if tab.is_displayed():
           
                tab.click()
                print("Tab clicked successfully!")
                try:
                    total_flats_label = driver.find_element(By.XPATH, "//p[contains(text(), 'Total number of Flats/Apartments of the Project')]")
                    total_flats_value = total_flats_label.find_element(By.XPATH, "following::p[1]").text
                except Exception as e:
                    total_flats_value = "Not found"

                # Locate and extract "Occupancy certificate received date"
                try:
                    occupancy_date_label = driver.find_element(By.XPATH, "//p[contains(text(), 'Occupancy certificate received date')]")
                    occupancy_date_value = occupancy_date_label.find_element(By.XPATH, "following::p[1]").text
                except Exception as e:
                    occupancy_date_value = "Not found"
            else:
                print("Tab exists but is not visible.")
        except NoSuchElementException:
            print("The tab with href='#completion' does not exist on this page.")
        try:

            csv_file = "karnatka_project_details_new.csv"
            file_exists = os.path.isfile(csv_file)

            # Define headers
            headers = [
                "Regno", "proj_name", "promoter_type", "proj_district", "prom_name", "project_type",
                "project_comp_date", "proj_status", "project_address", "inventory_type",
                "carpet_area","open_area","total_area", "terrace_area", "no_of_inventory", "balcony_area", "arch_name",
                "num_projects_completed", "total_flats_value", "occupancy_date_value"
            ]

            # Data to append
            row_data = [
                xid, proj_name, promoter_type, proj_district, prom_name, project_type,
                project_comp_date, proj_status, project_address, inventory_type,
                carpet_area,total_open_area,total_area_land, terrace_area, no_of_inventory, balcony_area, arch_name,
                num_projects_completed, total_flats_value, occupancy_date_value
            ]
            print(row_data)

            # Open the CSV file in append mode
            with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                
                if not file_exists:
                    writer.writerow(headers)

                writer.writerow(row_data)

            print(f"Data successfully saved to {csv_file}")
            driver.back()
                  
        except:
            continue

        
        
          
              
                   

 
         

