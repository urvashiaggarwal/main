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

driver = webdriver.Chrome()
driver.get("http://10.10.17.130:11011/login")
driver.maximize_window()

driver.find_element(By.NAME, "username").send_keys("urvashi.aggarwal@99Acres.com")
driver.find_element(By.NAME, "password").send_keys("Default!157")

driver.find_element(By.XPATH,'//button[text()="SUBMIT"]').click()
time.sleep(2)

#driver.find_element(By.XPATH,'//button[text()="Dashboard"]').click()
#time.sleep(4)

driver.find_element(By.XPATH, '//a[text()= "Add Data Request"]').click()
time.sleep(2)

driver.find_element(By.ID, "title").send_keys("gerate-system-gen")
driver.find_element(By.ID, "type_of_request").click()
time.sleep(1)

elem = driver.find_element(By.XPATH,"/html/body/div/form/div[2]/div/ul/li[2]/span")
time.sleep(1)
elem.click()

driver.find_element(By.NAME, "description").send_keys("Download Sys Data")

file = open ("sys-gen-query.txt", "r")
print("File Opened")
lines = file.readlines()
print(lines)
for line in lines:
    newalias = driver.find_element(By.ID,'query')   
    print( line.strip())
    newalias.send_keys(line.strip())
    newalias.send_keys(" ")


time.sleep(15)

driver.find_element(By.NAME,'submit').click()
 
timen = 0
while timen < 1500 :
     if driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[6]/div/div/span').text=='NONE':
       time.sleep(10)
       driver.find_element(By.XPATH,'//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[1]').click()
     elif driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[6]/div/div/span').text=="SUCCEEDED":
       driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[2]').click()   
       break
     else:
       timen = timen + 10
       time.sleep(5)
       driver.find_element(By.XPATH,'//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[1]').click()
 
 
print("Data Download") 
