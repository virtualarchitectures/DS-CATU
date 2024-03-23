import os
import time
import datetime
import csv
import requests
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
    "Adjudication Orders": "adjudication_orders",
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


def download_pdf(pdf_link):
    if pdf_link:
        # Create the downloaded_pdfs folder if it doesn't exist
        if not os.path.exists("data/downloaded_pdfs"):
            os.makedirs("data/downloaded_pdfs")

        # Download the PDF to the specified folder
        filename = pdf_link.split("/")[-1]
        filepath = os.path.join("data/downloaded_pdfs", filename)

        # Use requests to download the PDF
        response = requests.get(pdf_link)
        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath
    else:
        return None


def clean_data(data):
    cleaned_data = []
    for item in data:
        cleaned_item = {
            key: (
                # replace hidden characters
                value.replace("\xa0", " ").replace("\u2019", "'")
                if isinstance(value, str)
                else value
            )
            for key, value in item.items()
        }
        cleaned_data.append(cleaned_item)
    return cleaned_data


def write_to_csv(data):
    # Create the output folder if it doesn't exist
    if not os.path.exists("data/output"):
        os.makedirs("data/output")

    # Clean the data
    cleaned_data = clean_data(data)

    # Write data to CSV file
    with open("data/output/scrapped.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Title",
            "ID",
            "Date",
            "Subject",
            "PDF Type",
            "PDF Link",
            "PDF Path",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)


def get_search_items():
    data = []
    # get items on the current page
    search_items = driver.find_elements(By.CLASS_NAME, "card-list--had-downloadable")

    for i in search_items:
        item_data = {}
        # get the card title
        try:
            item_data["Title"] = i.find_element(
                By.CLASS_NAME, "card-list__title"
            ).get_attribute("innerText")
        except:
            item_data["Title"] = None

        # get the card details
        text_elements = i.find_elements(By.CLASS_NAME, "card-list__text")
        # get the dispute resolution ID
        try:
            item_data["ID"] = text_elements[0].get_attribute("innerText")
        except:
            item_data["ID"] = None
        # get the date
        try:
            item_data["Date"] = text_elements[1].get_attribute("innerText")
        except:
            item_data["Date"] = None
        # get the subject
        try:
            item_data["Subject"] = text_elements[2].get_attribute("innerText")
        except:
            item_data["Subject"] = None

        # get pdfs
        download_cards = i.find_elements(
            By.CLASS_NAME, "download-card.download-card--in-card"
        )

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

            item_data["PDF Type"] = pdf_type
            item_data["PDF Link"] = pdf_link

            # Download the PDF and get the file path
            pdf_filepath = download_pdf(pdf_link)
            item_data["PDF Path"] = pdf_filepath

            # Append the data to the list
            data.append(item_data.copy())

    return data


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
    data = get_search_items()

    # Write the data to CSV
    write_to_csv(data)

    driver.close()
    print("Closed Chromium Driver.")


get_search_results(search_url)
