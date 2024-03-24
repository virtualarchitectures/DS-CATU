import os
import time
import datetime
import csv
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

output_folder = "data/downloaded_pdfs/"

csv_output_file_path = "data/summary/case_metadata.csv"


def get_user_preferences():
    # first year of available data
    start_year = 2015
    # get the current year for year list
    current_year = datetime.datetime.now().year

    print(
        f"Select a year from {start_year}-{current_year} or enter 'All' for all years."
    )
    selected_year = input("Enter your choice and press return: ")

    # Validate user input for time period
    if selected_year != "All" and (
        not selected_year.isdigit()
        or int(selected_year) < start_year
        or int(selected_year) > current_year
    ):
        print("Invalid time period selected.")
        exit()

    # reference list for user input options
    order_types = {
        "All": "adjudication_orders|tribunal_orders",
        "Tribunal": "tribunal_orders",
        "Adjudication": "adjudication_orders",
    }

    # Prompt the user to select the dispute outcome type
    options_text = " | ".join(order_types.keys())
    print(f"Select the dispute outcome type ({options_text}).")
    selected_option = input("Enter your choice and press return: ")

    # Validate user input
    if selected_option not in order_types:
        print("Invalid option selected.")
        exit()

    order_type = order_types[selected_option]

    return selected_year, order_type


def generate_search_url(page_no, selected_year, order_type):
    # convert string to int
    page = str(page_no)

    # Generate the search URL based on the selected option and time period
    if selected_year == "All":
        search_url = (
            f"https://www.rtb.ie/search-results/listing/P{page}?collection={order_type}"
        )
    else:
        search_url = f"https://www.rtb.ie/search-results/listing/P{page}?year={selected_year}&collection={order_type}"

    return search_url


def download_pdf(pdf_link):
    if pdf_link:
        # Check if the PDF link returns a valid response
        response = requests.head(pdf_link)
        if (
            response.status_code != 200
            or "application/pdf" not in response.headers.get("content-type", "")
        ):
            print(f"Error downloading PDF from {pdf_link}. Invalid PDF link.")
            # TODO: Write message to comments column
            return None

        # Create the downloaded_pdfs folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Download the PDF to the specified folder
        filename = pdf_link.split("/")[-1]
        filepath = os.path.join(output_folder, filename)

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
            if key not in ["PDF Type", "PDF Link", "PDF Path"]
        }
        cleaned_data.append(cleaned_item)
    return cleaned_data


def write_to_csv(data):
    # Clean the data
    cleaned_data = clean_data(data)

    # Write data to CSV file
    with open(csv_output_file_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Title",
            "Date",
            "Subject",
            "Determination",
            "DR No.",
            "Determination_PDF",
            "Tribunal",
            "TR No.",
            "Tribunal_PDF",
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
        item_data["Determination_PDF"] = None
        item_data["Tribunal"] = False
        item_data["Tribunal_PDF"] = None

        # get the card title
        try:
            item_data["Title"] = i.find_element(
                By.CLASS_NAME, "card-list__title"
            ).get_attribute("innerText")
        except:
            item_data["Title"] = None

        # get the card details
        text_elements = i.find_elements(By.CLASS_NAME, "card-list__text")
        for element in text_elements:
            heading = element.find_element(
                By.XPATH, "./preceding-sibling::p[@class='card-list__heading']"
            ).get_attribute("innerText")
            value = element.get_attribute("innerText")
            if heading == "DR No.":
                item_data["DR No."] = value
            elif heading == "TR No.":
                item_data["TR No."] = value
            elif heading == "Date":
                item_data["Date"] = value
            elif heading == "Subject":
                item_data["Subject"] = value

        # get pdfs
        download_cards = i.find_elements(
            By.CLASS_NAME, "download-card.download-card--in-card"
        )
        for card in download_cards:
            pdf_link = card.get_attribute("href")
            pdf_type = card.find_element(
                By.CLASS_NAME, "download-card__title"
            ).get_attribute("innerText")

            # Extract determination and tribunal order information
            if "determination" in pdf_type.lower():
                item_data["Determination"] = True
                item_data["Determination_PDF"] = pdf_link
            elif "tribunal" in pdf_type.lower():
                item_data["Tribunal"] = True
                item_data["Tribunal_PDF"] = pdf_link

            # Download pdf
            print(f"Downloading PDF: {pdf_link}")
            download_pdf(pdf_link)

        # Append the data to the list
        data.append(item_data)

    return data


def get_search_results():
    results = []
    # inital page
    page_no = 0

    # get user input
    selected_year, order_type = get_user_preferences()

    # set options for running Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("detach", True)

    # initialise the Chrome webdriver
    # driver = webdriver.Chrome()  # run with UI for debugging
    driver = webdriver.Chrome(options=chrome_options)  # run headless

    while True:
        # generate search url from user input
        url = generate_search_url(page_no, selected_year, order_type)

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

        # Get the search items for the current page
        data = get_search_items(driver)
        # Add the data to the results
        results.extend(data)

        # Incrementally write results to CSV
        write_to_csv(results)

        # Increment the page number by 10 for the next page
        page_no += 10

        # Check if there are more pages to process
        if not data:
            break

    driver.close()
    print("Closed Chromium Driver.")


get_search_results()
