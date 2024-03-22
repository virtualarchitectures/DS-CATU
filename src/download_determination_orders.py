import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# get the current year
current_year = datetime.datetime.now().year
# generate the list of years from 2015
years_list = [year for year in range(2015, current_year + 1)]

# dictionary of order types
order_types = {
    "All": "adjudication_orders|tribunal_orders",
    "Tribunal Orders": "tribunal_orders",
    "Adjudcation Orders": "adjudication_orders",
}


# search url
search_url = "https://www.rtb.ie/search-results/listing"

# set options for running Selenium in headless mode
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_experimental_option("detach", True)

# initialise the Chrome webdriver
# driver = webdriver.Chrome()  # run with UI for debugging
driver = webdriver.Chrome(options=chrome_options)  # run headless


def get_search_items():
    # get items on the current page
    search_items = driver.find_elements(By.CLASS_NAME, "card-list--had-downloadable")

    for i in search_items:
        # get the card title
        try:
            dr_title = i.find_element(By.CLASS_NAME, "card-list__title").get_attribute(
                "innerText"
            )
        except:
            dr_title = None

        # get the card details
        text_elements = i.find_elements(By.CLASS_NAME, "card-list__text")
        # get the dispute resolution ID
        try:
            dr_id = text_elements[0].get_attribute("innerText")
            print(dr_id)
        except:
            dr_id = None
        # get the date
        try:
            dr_date = text_elements[1].get_attribute("innerText")
            print(dr_date)
        except:
            dr_date = None
        # get the subject
        try:
            dr_subject = text_elements[2].get_attribute("innerText")
            print(dr_subject)
        except:
            dr_subject = None

        # get pdfs
        download_cards = i.find_elements(
            By.CLASS_NAME, "download-card.download-card--in-card"
        )
        print(f"PDF Count: {len(download_cards)}")

        for card in download_cards:
            # get pdf links and types
            try:
                pdf_link = card.get_attribute("href")
                pdf_type = card.find_element(
                    By.CLASS_NAME, "download-card__title"
                ).get_attribute("innerText")
            except:
                pdf_link = None
                pdf_type = None

            print(f"{pdf_type}: {pdf_link}")


def get_search_results(url):
    # print url
    print(f"Querying URL: {url}")

    # open the web page
    driver.get(url)

    # wait for cookies notification
    time.sleep(2)

    try:
        # click on the privacy popup button
        privacy_button = driver.find_element(
            By.ID, "onetrust-accept-btn-handler"
        ).click()
        time.sleep(2)
    except:
        pass

    # get the search items for the current page
    get_search_items()

    driver.close()
    print("Closed Chromium Driver.")


get_search_results(search_url)
