from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import uuid
import pandas as pd
import time

service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service)

url = 'https://docs.oracle.com/en/cloud/saas/financials/24c/oedmf/'
driver.get(url)

table_data = []

wait = WebDriverWait(driver, 10)

tables_link = wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@href='#Tables-2']//span[text()='Tables']")))
tables_link.click()

for i in range(2,211):
    try:
        table_xpath = '//*[@id="treeview6_'+str(i)+'"]/div/a/span'
        table = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))
        table_name = table.text
        table_id = str(uuid.uuid4())
        table_content_xpath = '//*[@id="treeview6_'+str(i)+'"]/div/a/span'
        table_conent_link = wait.until(EC.element_to_be_clickable((By.XPATH, table_content_xpath)))
        table_conent_link.click()
        time.sleep(1)
        primary_key = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="contentContainer"]/article/div/div/div/section[2]/div/table/tbody/tr/td[1]/p')))
        primary_key_name = primary_key.text
        primary_key_columns = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="contentContainer"]/article/div/div/div/section[2]/div/table/tbody/tr/td[2]/p')))
        primary_key_column_names = primary_key_columns.text
        primary_key_column_names_list = [c.strip() for c in primary_key_column_names.split(",")]
        table_body = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="contentContainer"]/article/div/div/div/section[3]/div/table/tbody')))
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 6:
                table_name_temp = table_name
                column_id = str(uuid.uuid4())
                column_name = cols[0].text
                data_type = cols[1].text
                length = cols[2].text
                precision = cols[3].text
                not_null = cols[4].text
                primary_k = ''
                if column_name in primary_key_column_names_list:
                    primary_k = primary_key_name
            table_data.append([table_id, table_name_temp, column_id, column_name, data_type, length, precision, not_null, primary_k])
    except StaleElementReferenceException:
        print(f"StaleElementReferenceException at index {i}")
        continue
    except TimeoutException:
        print(f"TimeoutException at index {i}")
        continue
    except Exception:
        continue
    
columns = ['Table Id', 'Table', 'Column Id', 'Column', 'DataType', 'Length', 'Precision', 'NotNull', 'Primary Key']
df = pd.DataFrame(table_data, columns=columns)
df.to_excel("table_data.xlsx", index=False)
   
driver.quit()

print("Data Extraction Complete")