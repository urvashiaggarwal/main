from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import pdb
from datetime import datetime

driver = webdriver.Firefox()
driver.get("http://10.10.17.130:11011/login")
driver.maximize_window()

driver.find_element(By.NAME, "username").send_keys("urvashi.aggarwal@99acres.com")
driver.find_element(By.NAME, "password").send_keys("Default!157")

driver.find_element(By.XPATH, '//button[text()="SUBMIT"]').click()
time.sleep(2)

driver.find_element(By.XPATH, '//a[text()= "Add Data Request"]').click()
time.sleep(2)

driver.find_element(By.ID, "title").send_keys("gerate-system-gen")
driver.find_element(By.ID, "type_of_request").click()
time.sleep(1)

elem = driver.find_element(By.XPATH, "/html/body/div/form/div[2]/div/ul/li[2]/span")
time.sleep(1)
elem.click()

driver.find_element(By.NAME, "description").send_keys("Download Sys Data")

file = open("sys-gen-query.txt", "r")
lines = file.readlines()
for line in lines:
    newalias = driver.find_element(By.ID, 'query')
    newalias.send_keys(line.strip())
    newalias.send_keys(" ")

time.sleep(15)

driver.find_element(By.NAME, 'submit').click()

timen = 0
while timen < 1500:
    try:
        # Wait for the status element to be present
        status_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div[5]/div[3]/div[2]/table/tbody/tr[1]/td[6]'))
        )
        status_text = status_element.text
        if status_text == "NONE":
            time.sleep(10)
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/table/tbody/tr[1]/td[8]/form/button"))
            ).click()
        elif status_text == "SUCCEEDED":
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/table/tbody/tr[1]/td[9]/form/button"))
            ).click()
            break
        else:
            timen += 10
            time.sleep(5)
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/table/tbody/tr[1]/td[8]/form/button"))
            ).click()
    except Exception as e:
        print(f"An error occurred: {e}")
        break

print("Data Download")
driver.quit()