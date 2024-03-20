from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# search url
search_url = "https://www.rtb.ie/search-results/listing"

# set options for running Selenium in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")

# Initialise the Chrome webdriver
driver = webdriver.Chrome()  # run with UI for debugging
# driver = webdriver.Chrome(options=chrome_options)  # run headless

driver.get(search_url)

driver.close()
