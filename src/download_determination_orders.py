import os
import time
import datetime
from dateutil import parser
import csv
import requests
import requests.utils
from requests.adapters import HTTPAdapter, Retry
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
        "Adjudication": "adjudication-order",
        "Tribunal": "tribunal-order",
        "All": "adjudication-order|tribunal-order",
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
    base_url = "https://rtb.ie/disputes/dispute-outcomes-and-orders/adjudication-and-tribunal-orders/"

    # build query parameters
    params = []
    if selected_year != "All":
        params.append(f"_adjudication_orders_and_tribunal_orders_date={selected_year}")
    params.append(f"_adjudication_orders_and_tribunal_orders_post_type={order_type}")
    params.append(f"_paged={page_no}")

    search_url = base_url + "?" + "&".join(params)
    return search_url


def download_pdf(pdf_link, output_folder, max_retries=2):
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
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

    # create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_output_file_path), exist_ok=True)

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


def get_search_items(page):
    data = []
    print("Extracting data.")
    # get items on the current page
    search_items = page.query_selector_all(".adjudication-orders-and-tribunal-orders-item")

    for i in search_items:
        # initialise variable defaults
        item_data = {}
        item_data["Determination"] = False
        item_data["Determination PDF"] = None
        item_data["Tribunal"] = False
        item_data["Tribunal PDF"] = None

        # get the card title
        try:
            title_elem = i.query_selector("h3.heading-xs")
            item_data["Title"] = title_elem.inner_text().strip() if title_elem else None
        except:
            item_data["Title"] = None

        # get the card details from field elements
        fields = i.query_selector_all(".field")
        for field in fields:
            try:
                label_elem = field.query_selector(".data.label")
                if not label_elem:
                    continue
                label_text = label_elem.inner_text().strip()

                if label_text == "Subject of Dispute":
                    value_elem = field.query_selector(".data:not(.label)")
                    item_data["Subject"] = value_elem.inner_text().strip() if value_elem else None

                elif label_text == "DR No.":
                    value_elem = field.query_selector(".data:not(.label)")
                    item_data["DR No."] = value_elem.inner_text().strip() if value_elem else None

                elif label_text == "TR No.":
                    value_elem = field.query_selector(".data:not(.label)")
                    item_data["TR No."] = value_elem.inner_text().strip() if value_elem else None

                elif label_text == "Date":
                    # Date is in a <time> element
                    time_elem = field.query_selector("time")
                    if time_elem:
                        value = time_elem.inner_text().strip()
                        # Standardize date format using dateutil parser
                        parsed_date = parser.parse(value)
                        item_data["Upload Date"] = parsed_date.strftime("%d/%m/%Y")
            except:
                pass

        # get pdf information
        download_links = i.query_selector_all("a.download-link")
        for link in download_links:
            pdf_link = link.get_attribute("href")
            link_text = link.inner_text().lower()

            # extract determination and tribunal order information
            if "determination" in link_text:
                item_data["Determination"] = True
                item_data["Determination PDF"] = pdf_link
                output_folder = os.path.join(pdf_folder, "determinations")
                # download pdf
                print(f"Downloading PDF: {pdf_link}")
                download_pdf(pdf_link, output_folder)
                time.sleep(1)
            elif "tribunal" in link_text:
                item_data["Tribunal"] = True
                item_data["Tribunal PDF"] = pdf_link
                output_folder = os.path.join(pdf_folder, "tribunals")
                # download pdf
                print(f"Downloading PDF: {pdf_link}")
                download_pdf(pdf_link, output_folder)
                time.sleep(1)

        # append the data to the list
        data.append(item_data)

    return data


def get_search_results():
    results = []

    # get user input
    selected_year, selected_type = get_user_preferences()

    # disaggregate searches for 'All' years
    if selected_year == "All":
        year_list = [year for year in range(start_year, current_year + 1)]
    else:
        year_list = [selected_year]

    # disaggregate searches for 'All' order types
    if selected_type == "adjudication-order|tribunal-order":
        order_list = ["adjudication-order", "tribunal-order"]
    else:
        order_list = [selected_type]

    with sync_playwright() as p:
        # launch Chromium browser (headless=False to see the browser)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for year in year_list:
            selected_year = year

            for order_type in order_list:

                # load initial search page for this year/order_type
                url = generate_search_url(1, selected_year, order_type)
                print(f"Querying URL: {url}")
                page.goto(url)

                try:
                    # wait for result items to be present
                    page.wait_for_selector(".adjudication-orders-and-tribunal-orders-item", timeout=20000)
                except PlaywrightTimeoutError:
                    # no results found, move to next year/order_type
                    print("No results found.")
                    continue

                # wait for cookies notification
                time.sleep(2)

                try:
                    # click on the privacy popup button
                    page.click("#onetrust-accept-btn-handler", timeout=2000)
                    time.sleep(2)
                except:
                    pass

                # get total pages from pager
                last_page_elem = page.query_selector(".facetwp-page.last")
                if last_page_elem:
                    total_pages = int(last_page_elem.get_attribute("data-page"))
                    print(f"Total pages: {total_pages}")
                else:
                    total_pages = 1

                current_page = 1
                while True:
                    print(f"Processing page {current_page} of {total_pages}")

                    # Get the search items for the current page
                    data = get_search_items(page)
                    # Add the data to the results
                    results.extend(data)

                    # Incrementally write results to CSV
                    write_to_csv(results)

                    # Check if there's a next page
                    next_button = page.query_selector(".facetwp-page.next")
                    if not next_button or current_page >= total_pages:
                        break

                    # Click next button and wait for content to update
                    next_button.click()
                    time.sleep(2)
                    # Wait for the page content to refresh
                    page.wait_for_selector(".adjudication-orders-and-tribunal-orders-item", timeout=20000)
                    current_page += 1

        browser.close()
        print("Closed Chromium browser.")


if __name__ == "__main__":
    get_search_results()
