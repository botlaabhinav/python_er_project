from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import time

service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service)

url = 'https://docs.oracle.com/en/cloud/saas/financials/24c/oedmf/'
driver.get(url)


# assets_section = driver.find_elements(By.XPATH,"//*[@id='TreeViewListWrapper']/div[4]")
# driver.f
# # assets_section.click()
# print(assets_section)

# time.sleep(3)

wait = WebDriverWait(driver, 10)
# asset_sections = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='TreeViewListWrapper']/div[4]")))
# print(asset_sections.text)

tables_link = wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@href='#Tables-2']//span[text()='Tables']")))
print("----------------")
print(tables_link.click())
print("----------------")
ul_block = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="treeview6_0"]/ul')))
table_name = ul_block.find_elements(By.XPATH, './/li[@class="oj-treeview-item"]//span[@class="oj-treeview-item-text"]')
table_names = [item.text for item in table_name]
for name in table_names:
    print(name)
# table = table_name.text
# print(table)
# table_names = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.oj-treeview-item .oj-treeview-item-text')))

# for table in table_name:
#     print(table.text)
driver.quit()




print("Data Extraction Complete")