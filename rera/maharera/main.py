from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

url = "https://maharera.maharashtra.gov.in/projects-search-result"  
driver.get(url)
start_time = time.time()

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.container")))
all_data = []

while True:
    # Extract rows from the table
    try:
        rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#content > div > div.row > div.col-md-9.fullShow.col-lg-12 > div.container > div'))
        )
        print("Divs loaded successfully!")
    except:
        print("Timeout: The div elements did not load in time!")
        break

    for row in rows:
        cells = row.find_elements(By.XPATH, ".//p")  # Extract text from paragraph elements
        row_data = [cell.text for cell in cells]  
        print(row_data)
        all_data.append(row_data)

    # Navigate to the next page
    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.next"))
        )

        
        next_href = next_button.get_attribute("href")
        if not next_href:
            print("No more pages to navigate.")
            break

        driver.get(next_href)  

    except Exception as e:
        print("Error or no more pages:", e)
        break

end_time = time.time()
print(f"Total crawl time: {end_time - start_time:.2f} seconds")

# Save data to CSV
df = pd.DataFrame(all_data)
df.to_csv('maharera-reg-no-only-data.csv', mode='a', header=False, index=False)

driver.quit()
