import os
import time
import datetime
from dateutil import parser
import csv
import requests
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
        "All": "all",
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
        os.makedirs(output_folder, exist_ok=True)

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

    # Create directory if it doesn't exist
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

def extract_search_items(page):
    """Extract data from all article elements on current page"""
    data = []
    print("Extracting data from current page.")
    
    # Find the container with search results
    container = page.locator('div[data-name="adjudication_orders_and_tribunal_orders_listing"]')
    
    # Get all article elements
    articles = container.locator("article").all()
    
    locator_timeout=500
    for article in articles:
        item_data = {
            "Determination": False,
            "Determination PDF": None,
            "Tribunal": False,
            "Tribunal PDF": None,
        }
        
        # Extract Title from h3
        try:
            item_data["Title"] = article.get_by_role("heading").inner_text(timeout=locator_timeout).strip()
        except:
            item_data["Title"] = None
        
        # Extract Subject
        try:
            subject_span = article.locator('span:has-text("Subject of Dispute") + span')
            item_data["Subject"] = subject_span.inner_text(timeout=locator_timeout).strip()

        except:
            item_data["Subject"] = None
        
        # Extract DR No.
        try:
            dr_span = article.locator('span:has-text("DR No.") + span')
            item_data["DR No."] = dr_span.inner_text(timeout=locator_timeout).strip()

        except:
            item_data["DR No."] = None
        
        # Extract TR No.
        try:
            tr_span = article.locator('span:has-text("TR No.") + span')
            item_data["TR No."] = tr_span.inner_text(timeout=locator_timeout).strip()
        except:
            item_data["TR No."] = None
        
        # Extract Upload Date
        try:
            datetime = article.get_by_role('time').inner_text(timeout=locator_timeout).strip()
            parsed_date = parser.parse(datetime)
            item_data["Upload Date"] = parsed_date.strftime("%d/%m/%Y")
        except:
            item_data["Upload Date"] = None
        
        # Extract PDF links
        pdf_links = article.locator("a[href]").all()
        
        for link in pdf_links:
            href = link.get_attribute("href")
            link_text = link.inner_text()
            if href and "determination" in link_text.lower():
                item_data["Determination"] = True
                item_data["Determination PDF"] = href
                output_folder = os.path.join(pdf_folder, "determinations")
                print(f"Downloading Determination PDF: {href}")
                download_pdf(href, output_folder)

            elif href and "tribunal" in link_text.lower():
                item_data["Tribunal"] = True
                item_data["Tribunal PDF"] = href
                output_folder = os.path.join(pdf_folder, "tribunals")
                print(f"Downloading Tribunal PDF: {href}")
                download_pdf(href, output_folder)
        
        if item_data.get("Title") or item_data.get("Determination PDF") or item_data.get("Tribunal PDF"):
            data.append(item_data)
    
    return data


def has_next_page(page):
    """Check if there's a next page by looking for '>>' link"""
    try:
        next_link = page.get_by_text(">>")
        return next_link.count() > 0
    except:
        return False


def go_to_next_page(page):
    """Navigate to next page by clicking '>>' link"""
    try:
        next_link = page.get_by_text(">>")
        next_link.click()
        page.wait_for_load_state("domcontentloaded")

        return True
    except Exception as e:
        print(f"Error navigating to next page: {e}")
        return False


def get_search_results():
    """Main function to scrape RTB website"""
    results = []
    
    # Get user preferences
    selected_year, selected_type = get_user_preferences()
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
                headless=False,
                slow_mo=1
            )
        context = browser.new_context(
            bypass_csp=True,
            ignore_https_errors=True
        )
        page = context.new_page()

        try:
            search_url=build_search_url(selected_year, selected_type)
            print(f"Search URL: {search_url}")
            page.goto(search_url)
            page.wait_for_load_state("domcontentloaded")
            # Handle cookie consent if present (unsure if this is still required)
            try:
                cookie_button = page.locator("#onetrust-accept-btn-handler")
                if cookie_button.count() > 0:
                    cookie_button.click()
                    time.sleep(1)
            except:
                pass

            # Process pages
            page_count = 1
            while True:
                print(f"Processing page {page_count}")
                
                # Extract data from current page
                data = extract_search_items(page)
                results.extend(data)
                
                # Write results incrementally
                write_to_csv(results)
                print(f"Extracted {len(data)} items. Total: {len(results)}")
                
                # Check for next page
                if has_next_page(page):
                    print("Navigating to next page...")
                    if not go_to_next_page(page):
                        break
                    page_count += 1
                else:
                    print("No more pages. Scraping complete.")
                    break
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        
        finally:
            browser.close()
            print("Browser closed.")
    
    print(f"Total items scraped: {len(results)}")
    print(f"Results saved to: {csv_output_file_path}")


if __name__ == "__main__":
    get_search_results()