from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
 
# Step 1: Setup the WebDriver
driver = webdriver.Chrome()
 
# Step 2: Open the webpage
url = "https://maharera.maharashtra.gov.in/projects-search-result"  # Replace with your desired URL
driver.get(url)
start_time = time.time()
# Step 3: Wait for the page to load (adjust the time as necessary)
time.sleep(3)  # You can also use WebDriverWait for more efficient waiting
 
 
# Step 6: Iterate through each row and extract column data
all_data = []
while True:
    # Step 6: Locate the table and extract rows
     
    #rows = driver.find_elements(By.CSS_SELECTOR, '#content > div > div.row > div.col-md-9.fullShow.col-lg-12 > div.container > div')
   
    try:
    # Wait for the div with class 'row' to be present (replace with the actual class, id, or XPath)
        rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div.row > div.col-md-9.fullShow.col-lg-12 > div.container > div'))
        )
        print("Divs loaded successfully!")
    except:
        print("Timeout: The div elements did not load in time!")
    for row in rows:
        cells = row.find_elements(By.XPATH, "div[1]/p[1]")  # Find all cells within the current row
        row_data = [cell.text for cell in cells]  # Extract text from each cell
        print(row_data)
        all_data.append(row_data)  # Add the row's data to the list
         
   
    # Step 8: Try to locate and click the "Next" button
    try:
        time.sleep(1)
 
        next_button =WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next")))
 
        disabled_class = 'disabled'  # The class that indicates the button is disabled (adjust if needed)
        aria_disabled = 'true'  # The attribute value indicating the button is disabled
 
 
        if disabled_class in next_button.get_attribute('class') or next_button.get_attribute('aria-disabled') == aria_disabled:
            print("Pagination has ended or no more pages.")
            break
 
        try:
            next_button.click()
        except:
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, "next"))).click()
             
 
       
    except Exception as e:
        # If there's an issue (e.g., no "Next" button), break the loop
        print("Error or no more pages:", e)
        break
end_time = time.time()
 
# Calculate the total crawl time
total_crawl_time = end_time - start_time
print(f"Total crawl time: {total_crawl_time:.2f} seconds")
 
# Step 8: Close the WebDriver
 
df = pd.DataFrame(all_data)
df.to_csv('maharera-reg-no-only-data.csv', mode='a', header=False, index=False)