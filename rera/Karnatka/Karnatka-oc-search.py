from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import re, os, time, datetime, shutil
from selenium.webdriver.support.select import Select
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import openpyxl
from openpyxl.workbook import Workbook
from selenium.common.exceptions import NoSuchElementException
import csv
from io import BytesIO
import re, os, time, datetime

from datetime import date

import json

import sys,os,pdb


Attempted_date_var = 'Date'+str(date.today())
maindirectory = os.path.abspath(os.getcwd())
HTML = os.path.join(maindirectory, 'OC')
if not os.path.isdir(HTML):
    os.makedirs(HTML)
HTML_PAGE_make_dir = os.path.join(HTML, str(Attempted_date_var))
 
            
if not os.path.isdir(HTML_PAGE_make_dir):
    os.makedirs(HTML_PAGE_make_dir)
chrome_options = webdriver.ChromeOptions() 
 
settings = {"recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF", "version": 2,"isCssBackgroundEnabled": True,"margins":0  }
prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings),
         "savefile.default_directory": HTML_PAGE_make_dir}
chrome_options.add_experimental_option('prefs', prefs)

chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--kiosk-printing') 

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://rera.karnataka.gov.in/viewAllProjects")
driver.maximize_window()
ids_group = []
cnt = 0
cc="NO"
c=0
#driver.find_element(By.ID,'compliant_hearing_next').click()
with open("karnatka_oc.csv","r") as csvfile:
    records  = csv.reader(csvfile,delimiter=",")
    next(records)

    for row in records:
        xid = row[0]
        print(xid)
                
        try:
            driver.find_element(By.ID, 'regNo2').send_keys(Keys.CONTROL, 'a')
            driver.find_element(By.ID, 'regNo2').send_keys(xid)
            driver.find_element(By.NAME, 'btn1').click()
            time.sleep(3) 
            filename = xid.replace('/', '-')
            try:
                #driver.switch_to.window(driver.window_handles[0])
                driver.find_element(By.XPATH, "//a[@onclick]").click()
                
                #driver.find_element(By.XPATH, '//*[@id="approvedTable"]/tbody/tr/td[4]/a').click()
                 
                time.sleep(10)
            except:
                continue
            try:
                # Find the element containing the text "Completion Details"
                element = driver.find_element(By.XPATH, '//*[text()="Completion Details"]')
                
                # Click the element
                element.click()
                time.sleep(5) 
                #ele3 = driver.find_element(By.XPATH, '//*[@href="#completion"]')
                #ele3.click()
                #exit()
            except:
                
                driver.back()
                continue
            time.sleep(3)

            #ele1 = driver.find_element(By.XPATH, "//*[text()='possession certificate.pdf']")
            #ele2 = driver.find_element(By.XPATH, "//*[text()='completion certificate.jpeg']")
            #print(ele1.text)
            #print(ele2.text)
               
            if driver.find_element(By.PARTIAL_LINK_TEXT, 'Occupancy Certificate'):
                print("pdf")
                txtName = "-oc.pdf"
                driver.find_element(By.PARTIAL_LINK_TEXT, 'Occupancy Certificate').click()
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(1)
                driver.execute_script('window.print();')
                time.sleep(5)
                files = os.listdir(HTML_PAGE_make_dir)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(HTML_PAGE_make_dir, x)), reverse=True)


                pdf_filename = files[0]
                time.sleep(5)
                new_file_name = filename+txtName
                print(new_file_name)
                old_file = os.path.join(HTML_PAGE_make_dir, pdf_filename)
                new_file = os.path.join(HTML_PAGE_make_dir, new_file_name)

                os.rename(old_file, new_file)
                driver.close()
                time.sleep(2)
                driver.switch_to.window(driver.window_handles[0])
            else:
                try:
                    print('pp')
                    ocLINK = driver.find_element(By.CSS_SELECTOR, '#completion > div > div:nth-child(9) > div:nth-child(5) > div:nth-child(4) > p > a')
                    txtName = ocLINK.text
                    print(txtName)
                    ocLINK.click()
                    
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(1)
                    driver.execute_script('window.print();')
                    time.sleep(5)
                    files = os.listdir(HTML_PAGE_make_dir)
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(HTML_PAGE_make_dir, x)), reverse=True)


                    pdf_filename = files[0]
                    time.sleep(5)
                    new_file_name = filename+txtName
                    print(new_file_name)
                    old_file = os.path.join(HTML_PAGE_make_dir, pdf_filename)
                    new_file = os.path.join(HTML_PAGE_make_dir, new_file_name)

                    os.rename(old_file, new_file)
                    driver.close()
                    time.sleep(2)
                    driver.switch_to.window(driver.window_handles[0])
                    print(txtName)
                
                except:
                    print('HHH')
                    pass
            if driver.find_element(By.XPATH, '//*[@id="completion"]/div/div[4]/div[4]/p/a').text == 'possession certificate.pdf':
                print("pdf")
                driver.find_element(By.XPATH, '//*[@id="completion"]/div/div[4]/div[4]/p/a').click()
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(1)
                driver.execute_script('window.print();')
                time.sleep(5)
                files = os.listdir(HTML_PAGE_make_dir)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(HTML_PAGE_make_dir, x)), reverse=True)


                pdf_filename = files[0]
                time.sleep(5)
                new_file_name = filename+"-oc.pdf"
                print(new_file_name)
                old_file = os.path.join(HTML_PAGE_make_dir, pdf_filename)
                new_file = os.path.join(HTML_PAGE_make_dir, new_file_name)

                os.rename(old_file, new_file)
                driver.close()
                time.sleep(2)
                driver.switch_to.window(driver.window_handles[0])
            else:
                pass
            try:
                '''
                completion_text = driver.find_element(By.XPATH, "//p[contains(text(), 'Completion Certificate')]")

                if completion_text:
                    link = completion_text.find_element(By.XPATH, "following-sibling::div//a")

                    # Step 3: Click the <a> link
                    link.click()
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(1)
                    driver.execute_script('window.print();')
                    time.sleep(5)
                    files = os.listdir(HTML_PAGE_make_dir)
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(HTML_PAGE_make_dir, x)), reverse=True)


                    pdf_filename = files[0]
                    time.sleep(5)
                    new_file_name = filename+"-cc.pdf"
                    print(new_file_name)
                    old_file = os.path.join(HTML_PAGE_make_dir, pdf_filename)
                    new_file = os.path.join(HTML_PAGE_make_dir, new_file_name)

                    os.rename(old_file, new_file)
                    driver.close()
                    time.sleep(2)
                    driver.switch_to.window(driver.window_handles[0])
                '''
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find all rows that may contain the document links (looking for the term "Completion Certificate")
                rows = soup.find_all('div', class_='row')
                
                # Loop through each row and find the document link related to Completion Certificate
                for row in rows:
                    # Check if the text "Completion Certificate" is in the row (you can adjust this as needed)
                    if "Completion Certificate" in row.text:
                        # Find the anchor tag with the document link (href contains 'reraDocument?DOC=')
                        link = row.find('a', href=True, string=lambda text: text and 'reraDocument?DOC=' in text)
                        
                        if link:
                            # Construct the full URL for the document
                            full_url = "https://rera.karnataka.gov.in" + link['href']

                            # Send a GET request to download the document
                            certificate_response = requests.get(full_url)

                            if certificate_response.status_code == 200:
                                # Save the document as a PDF (or whatever file type it is)
                                file_name = f"certificate_{registration_number}.pdf"
                                with open(file_name, 'wb') as file:
                                    file.write(certificate_response.content)
                                print(f"Certificate for {registration_number} downloaded successfully!")
                            else:
                                print(f"Failed to download the certificate for {registration_number}.")
                            

                
            except:
                
                pass
            
            driver.back()
            time.sleep(4)

     
          
        except:
            print("ALL CLEAR")
            driver.back()
            driver.switch_to.window(driver.window_handles[0])
            continue
