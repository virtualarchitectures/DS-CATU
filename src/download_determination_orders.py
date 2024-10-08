import os
import time
import datetime
from dateutil import parser
import csv
import requests
import requests.utils
from requests.adapters import HTTPAdapter, Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

pdf_folder = "data/downloaded_pdfs/"

csv_output_file_path = "data/summary/case_metadata.csv"

# first year of available data
start_year = 2015
# get the current year for year list
current_year = datetime.datetime.now().year


def get_user_preferences():
    print(
        f"Select a year from {start_year}-{current_year} or enter 'All' for all years."
    )
    selected_year = input("Enter your choice and press return: ").strip().capitalize()

    # validate user input for time period
    if selected_year != "All" and (
        not selected_year.isdigit()
        or int(selected_year) < start_year
        or int(selected_year) > current_year
    ):
        print("Invalid time period selected.")
        exit()

    # reference list for user input options
    order_types = {
        "Adjudication": "adjudication_orders",
        "Tribunal": "tribunal_orders",
        "All": "adjudication_orders|tribunal_orders",
    }

    # prompt the user to select the dispute outcome type
    options_text = " | ".join(order_types.keys())
    print(f"Select the dispute outcome type ({options_text}).")
    selected_option = input("Enter your choice and press return: ").strip().capitalize()

    # validate user input
    if selected_option not in order_types:
        print("Invalid option selected.")
        exit()

    selected_type = order_types[selected_option]

    return selected_year, selected_type


def generate_search_url(page_no, selected_year, order_type):
    # convert string to int
    page = str(page_no)

    # generate the search URL based on the selected option and time period
    if selected_year == "All":
        search_url = (
            f"https://www.rtb.ie/search-results/listing/P{page}?collection={order_type}"
        )
    else:
        search_url = f"https://www.rtb.ie/search-results/listing/P{page}?year={selected_year}&collection={order_type}"

    return search_url


def download_pdf(pdf_link, output_folder, max_retries=2):
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["HEAD", "GET"],
        backoff_factor=2,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        # check if the PDF link returns a valid response
        response = session.head(pdf_link)
        if (
            response.status_code != 200
            or "application/pdf" not in response.headers.get("content-type", "")
        ):
            error = "Error: Unable to download PDF."
            print(error)
            return error

        # create the downloaded_pdfs folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # download the PDF to the specified folder
        filename = pdf_link.split("/")[-1]
        filepath = os.path.join(output_folder, filename)

        # use requests to download the PDF
        response = session.get(pdf_link)
        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
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
            if key not in ["PDF Type", "PDF Link", "PDF Path"]
        }
        cleaned_data.append(cleaned_item)
    return cleaned_data


def write_to_csv(data):
    # clean the data
    cleaned_data = clean_data(data)

    # write data to CSV file
    with open(csv_output_file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Title",
            "Upload Date",
            "Subject",
            "Determination",
            "DR No.",
            "Determination PDF",
            "Tribunal",
            "TR No.",
            "Tribunal PDF",
            "Comments",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)


def get_search_items(driver):
    data = []
    print("Extracting data.")
    # get items on the current page
    search_items = driver.find_elements(By.CLASS_NAME, "card-list--had-downloadable")

    for i in search_items:
        # initialise variable defaults
        item_data = {}
        item_data["Determination"] = False
        item_data["Determination PDF"] = None
        item_data["Tribunal"] = False
        item_data["Tribunal PDF"] = None

        # get the card title
        try:
            item_data["Title"] = i.find_element(
                By.CLASS_NAME, "card-list__title"
            ).text.strip()
        except:
            item_data["Title"] = None

        # get the card details
        headings = i.find_elements(By.CLASS_NAME, "card-list__heading")
        # loop through headings
        for heading in headings:
            heading_text = heading.text.strip()

            if heading_text == "Subject of Dispute":
                try:
                    item_data["Subject"] = heading.find_element(
                        By.XPATH, "following-sibling::p"
                    ).text.strip()
                except:
                    item_data["Subject"] = None

            elif heading_text == "DR No.":
                try:
                    item_data["DR No."] = heading.find_element(
                        By.XPATH, "following-sibling::p"
                    ).text.strip()
                except:
                    item_data["DR No."] = None

            elif heading_text == "TR No.":
                try:
                    item_data["TR No."] = heading.find_element(
                        By.XPATH, "following-sibling::p"
                    ).text.strip()
                except:
                    item_data["TR No."] = None

            elif heading_text == "Date":
                try:
                    value = heading.find_element(
                        By.XPATH, "following-sibling::p"
                    ).text.strip()
                    # Standardize date format using dateutil parser
                    parsed_date = parser.parse(value)
                    item_data["Upload Date"] = parsed_date.strftime("%d/%m/%Y")
                except:
                    item_data["Upload Date"] = None

        # get pdf information
        download_cards = i.find_elements(
            By.CLASS_NAME, "download-card.download-card--in-card"
        )
        for card in download_cards:
            pdf_link = card.get_attribute("href")
            pdf_type = card.find_element(
                By.CLASS_NAME, "download-card__title"
            ).get_attribute("innerText")

            # extract determination and tribunal order information
            if "determination" in pdf_type.lower():
                item_data["Determination"] = True
                item_data["Determination PDF"] = pdf_link
                output_folder = os.path.join(pdf_folder, "determinations")
            elif "tribunal" in pdf_type.lower():
                item_data["Tribunal"] = True
                item_data["Tribunal PDF"] = pdf_link
                output_folder = os.path.join(pdf_folder, "tribunals")

            # download pdf
            print(f"Downloading PDF: {pdf_link}")
            download_pdf(pdf_link, output_folder)
            # pause between downloads
            time.sleep(1)

        # append the data to the list
        data.append(item_data)

    return data


def get_search_results(starting_page=0):
    results = []
    # set starting page number
    page_no = starting_page

    # get user input
    selected_year, selected_type = get_user_preferences()

    # set options for running Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("detach", True)

    # initialise the Chrome webdriver
    driver = webdriver.Chrome(options=chrome_options)

    # disaggregate searches for 'All' years
    if selected_year == "All":
        year_list = [year for year in range(start_year, current_year + 1)]
    else:
        year_list = [selected_year]

    # disaggregate searches for 'All' order types
    if selected_type == "adjudication_orders|tribunal_orders":
        order_list = ["adjudication_orders", "tribunal_orders"]
    else:
        order_list = [selected_type]

    for year in year_list:
        selected_year = year

        for order_type in order_list:

            while True:
                # generate search url from user input
                url = generate_search_url(page_no, selected_year, order_type)

                # print url
                print(f"Querying URL: {url}")

                # open the web page
                driver.get(url)

                # wait for the page to load completely
                wait = WebDriverWait(driver, 20)
                try:
                    # check for downloadable data
                    wait.until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "card-list--had-downloadable")
                        )
                    )
                except TimeoutException:
                    # reset page number and break
                    page_no = 0
                    break

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

                # Get the search items for the current page
                data = get_search_items(driver)
                # Add the data to the results
                results.extend(data)

                # Incrementally write results to CSV
                write_to_csv(results)

                # Increment the page number by 10 for the next page
                page_no += 10

    driver.close()
    print("Closed Chromium Driver.")


get_search_results(starting_page=0)
