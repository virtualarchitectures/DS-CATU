import csv
import datetime
import os
import time

import requests
from dateutil import parser
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from requests.adapters import HTTPAdapter, Retry

pdf_folder = "data/downloaded_pdfs/"
csv_output_file_path = "data/summary/case_metadata.csv"

# First year of available data
start_year = 2015
# Get the current year for year list
current_year = datetime.datetime.now().year


def get_user_preferences():
    print(
        f"Select a year from {start_year}-{current_year} or enter 'All' for all years."
    )
    selected_year = input("Enter your choice and press return: ").strip().capitalize()

    # Validate user input for time period
    if selected_year != "All" and (
        not selected_year.isdigit()
        or int(selected_year) < start_year
        or int(selected_year) > current_year
    ):
        print("Invalid time period selected.")
        exit()

    # Reference list for user input options
    order_types = {
        "Adjudication": "adjudication-order",
        "Tribunal": "tribunal-order",
        "All": "adjudication-order|tribunal-order",
    }

    # Prompt the user to select the dispute outcome type
    options_text = " | ".join(order_types.keys())
    print(f"Select the dispute outcome type ({options_text}).")
    selected_option = input("Enter your choice and press return: ").strip().capitalize()

    # Validate user input
    if selected_option not in order_types:
        print("Invalid option selected.")
        exit()

    if selected_year == "All" and selected_option == "All":
        print("Error: Cannot select 'All' for both year and type. Please select at least one specific filter.")
        exit()
    
    selected_type = order_types[selected_option]

    # Prompt for file download preference
    print("Download document files? (Yes | No)")
    download_input = input("Enter your choice and press return: ").strip().capitalize()
    download_files = download_input in ["Yes", "Y"]

    return selected_year, selected_type, download_files


SUPPORTED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def download_file(file_link, output_folder, max_retries=2):
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
        # Check if the file link returns a valid response
        response = session.head(file_link)
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if response.status_code != 200:
            error = (
                f"Error: Unable to download file.\nStatus Code: {response.status_code}"
            )
            print(error)
            return error

        if content_type not in SUPPORTED_CONTENT_TYPES:
            error = f"Error: Unsupported content type: {content_type}"
            print(error)
            return error

        # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Download the file to the specified folder
        filename = file_link.split("/")[-1]
        filepath = os.path.join(output_folder, filename)

        # Use requests to download the file
        response = session.get(file_link)
        with open(filepath, "wb") as f:
            f.write(response.content)

        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None


def clean_data(data):
    cleaned_data = []
    for item in data:
        cleaned_item = {
            key: (
                # Replace hidden characters
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

    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(csv_output_file_path), exist_ok=True)

    # Write data to CSV file
    with open(csv_output_file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Title",
            "Upload Date",
            "Subject",
            "Determination",
            "DR No.",
            "Determination Doc",
            "Tribunal",
            "TR No.",
            "Tribunal Doc",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)

def build_search_url(selected_year, selected_type):
    """Build search URL based on selected filters"""
    base_url = "https://rtb.ie/disputes/dispute-outcomes-and-orders/adjudication-and-tribunal-orders/"
    
    params = []
    
    # Add year parameter if not "All"
    if selected_year != "All":
        params.append(f"_adjudication_orders_and_tribunal_orders_date={selected_year}")
    
    # Add type parameter if not "all"
    if selected_type != "all":
        params.append(f"_adjudication_orders_and_tribunal_orders_post_type={selected_type}")
    
    # Build final URL
    if params:
        return base_url + "?" + "&".join(params)
    else:
        return base_url 

def build_search_url(selected_year, order_type):
    """Build search URL based on selected filters"""
    base_url = "https://rtb.ie/disputes/dispute-outcomes-and-orders/adjudication-and-tribunal-orders/"

    params = []

    # Add year parameter if not "All"
    if selected_year != "All":
        params.append(f"_adjudication_orders_and_tribunal_orders_date={selected_year}")
    params.append(f"_adjudication_orders_and_tribunal_orders_post_type={order_type}")

    search_url = base_url + "?" + "&".join(params)
    return search_url


def extract_search_items(page, download_files=False):
    """Extract data from all article elements on current page"""
    data = []
    print(f"Extracting data from: {page.url}")

    # Find the container with search results using Locator API
    container = page.locator(
        'div[data-name="adjudication_orders_and_tribunal_orders_listing"]'
    )

    # Get all article elements
    articles = container.locator("article").all()

    locator_timeout = 10
    for article in articles:
        item_data = {
            "Determination": False,
            "Determination Doc": None,
            "Tribunal": False,
            "Tribunal Doc": None,
        }

        # Extract Title from h3
        heading = article.get_by_role("heading")
        if heading.count() > 0:
            item_data["Title"] = heading.inner_text(timeout=locator_timeout).strip()
        else:
            item_data["Title"] = None
        
        # Extract Subject
        try:
            subject_span = article.locator('span:has-text("Subject of Dispute") + span')
            item_data["Subject"] = subject_span.inner_text(timeout=locator_timeout).strip()

        # Extract Subject
        subject_span = article.locator('span:has-text("Subject of Dispute") + span')
        if subject_span.count() > 0:
            item_data["Subject"] = subject_span.inner_text(timeout=locator_timeout).strip()
        else:
            item_data["Subject"] = None

        # Extract DR No.
        dr_span = article.locator('span:has-text("DR No.") + span')
        if dr_span.count() > 0:
            item_data["DR No."] = dr_span.inner_text(timeout=locator_timeout).strip()
        else:
            item_data["DR No."] = None

        # Extract TR No.
        tr_span = article.locator('span:has-text("TR No.") + span')
        if tr_span.count() > 0:
            item_data["TR No."] = tr_span.inner_text(timeout=locator_timeout).strip()
        else:
            item_data["TR No."] = None

        # Extract Upload Date
        time_elem = article.get_by_role("time")
        if time_elem.count() > 0:
            datetime_text = time_elem.inner_text(timeout=locator_timeout).strip()
            parsed_date = parser.parse(datetime_text)
            item_data["Upload Date"] = parsed_date.strftime("%d/%m/%Y")
        else:
            item_data["Upload Date"] = None

        # Extract document links (PDF and DOCX)
        doc_links = article.locator("a[href]").all()

        for link in doc_links:
            href = link.get_attribute("href")
            link_text = link.inner_text().lower()
            if href and "determination" in link_text:
                item_data["Determination"] = True
                item_data["Determination Doc"] = href
                if download_files:
                    output_folder = os.path.join(pdf_folder, "determinations")
                    print(f"Downloading file: {href}")
                    download_file(href, output_folder)

            elif href and "tribunal" in link_text:
                item_data["Tribunal"] = True
                item_data["Tribunal Doc"] = href
                if download_files:
                    output_folder = os.path.join(pdf_folder, "tribunals")
                    print(f"Downloading file: {href}")
                    download_file(href, output_folder)

        if (
            item_data.get("Title")
            or item_data.get("Determination Doc")
            or item_data.get("Tribunal Doc")
        ):
            data.append(item_data)

    return data


def has_next_page(page):
    """Check if there's a next page link"""
    next_link = page.locator("a.facetwp-page.next")
    return next_link.count() > 0


def go_to_next_page(page):
    """Navigate to next page by clicking next link"""
    try:
        current_url = page.url
        # Set up listener for the 'refresh' request
        with page.expect_response(
            lambda response: "refresh" in response.url and response.status == 200,
            timeout=10000,
        ) as response_info:
            next_link = page.locator("a.facetwp-page.next")
            next_link.click()

        response_info.value

        page.wait_for_url(lambda url: url != current_url, timeout=10000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        return True
    except Exception as e:
        print(f"Error navigating to next page: {e}")
        return False


def get_search_results():
    """Main function to scrape RTB website"""
    results = []

    # Get user input
    selected_year, selected_type, download_files = get_user_preferences()

    # Disaggregate searches for 'All' years
    if selected_year == "All":
        year_list = [year for year in range(start_year, current_year + 1)]
    else:
        year_list = [selected_year]

    # NOTE: Previous version of the website didn't return all results
    # TODO: Check if site returns ALL results or if search disaggregation still required
    # disaggregate searches for 'All' order types
    if selected_type == "adjudication-order|tribunal-order":
        order_list = ["adjudication-order", "tribunal-order"]
    else:
        order_list = [selected_type]

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(bypass_csp=True, ignore_https_errors=True)
        page = context.new_page()
        start_time = time.time()

        try:
            for year in year_list:
                selected_year = year

                for order_type in order_list:
                    url = build_search_url(selected_year, order_type)
                    print(f"Search URL: {url}")
                    page.goto(url)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(1)

                    # Handle cookie consent if present
                    cookie_button = page.locator("#onetrust-accept-btn-handler")
                    if cookie_button.count() > 0:
                        cookie_button.click()
                        time.sleep(1)

                    try:
                        # wait for result items to be present
                        page.wait_for_selector(
                            ".adjudication-orders-and-tribunal-orders-item",
                            timeout=20000,
                        )
                    except PlaywrightTimeoutError:
                        # no results found, move to next year/order_type
                        print("No results found.")
                        continue

                    # get total pages from pager using Locator API
                    last_page_elem = page.locator("a.facetwp-page.last")
                    if last_page_elem.count() > 0:
                        total_pages = int(last_page_elem.inner_text())
                    else:
                        total_pages = 1
                    print(f"Total pages: {total_pages}")

                    current_page = 1
                    while True:
                        print(f"Processing page {current_page} of {total_pages}")

                        # Extract data from current page
                        data = extract_search_items(page, download_files)
                        results.extend(data)

                        # Write results incrementally
                        write_to_csv(results)
                        print(f"Extracted {len(data)} entries. Total: {len(results)}")

                        # Check if there's a next page
                        if has_next_page(page):
                            if go_to_next_page(page):
                                current_page += 1
                            else:
                                break
                        else:
                            print("No more pages for this search.")
                            break

        except Exception as e:
            print(f"Error during scraping: {e}")

        finally:
            print(f"Total entries scraped: {len(results)}")
            # Validate results count against expected total
            expected_total_elem = page.locator("span[data-facetwp-total]")
            if expected_total_elem.count() > 0:
                expected_total = int(expected_total_elem.inner_text())
                if len(results) != expected_total:
                    print(
                        f"Warning: Scraped {len(results)} entries but expected {expected_total}"
                    )

            browser.close()
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(
                f"Finished in: {elapsed_time:.2f} seconds ({elapsed_time / 60:.2f} minutes)"
            )

    print(f"Results saved to: {csv_output_file_path}")


if __name__ == "__main__":
    get_search_results()
