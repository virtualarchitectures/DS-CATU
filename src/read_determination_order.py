import os
import re
import csv
from pdf2image import convert_from_path
import pytesseract

# input_folder = "data/downloaded_pdfs/"
# output_folder = "data/converted_text/"

input_folder = "data/input/"
output_folder = "data/output/"

keywords_file = "reference/keywords.txt"

csv_output_file_path = "data/summary/case_details.csv"


def read_keywords(file_path):
    with open(file_path, "r") as file:
        keywords = [line.strip() for line in file.readlines() if line.strip()]
    return keywords


def get_file_paths(input_folder):
    file_paths = []

    # Loop through the files in the input folder
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths


def join_rows(text):
    # Store the result
    result = []

    # Split multiline strings into a list of lines
    lines = text.split("\n")

    # Accumulate lines into paragraphs
    current_paragraph = ""
    for line in lines:
        # If the line is not empty
        if line.strip():
            # Add the line to the current paragraph
            current_paragraph += line + " "
            # If the line ends with a colon or full stop, start a new paragraph
            if line.strip().endswith(":") or line.strip().endswith("."):
                result.append(current_paragraph.strip())
                current_paragraph = ""
        else:
            # Add the current paragraph to the result if not empty
            if current_paragraph:
                result.append(current_paragraph.strip())
                current_paragraph = ""

    # Add the remaining paragraph to the result if not empty
    if current_paragraph:
        result.append(current_paragraph.strip())

    # Join the paragraphs with newlines and return the result
    return "\n".join(result)


def extract_names(text):
    tenant_name = None
    landlord_name = None
    tenant_role = None
    landlord_role = None

    # Define two alternate regular expression patterns
    pattern1 = (
        r"In the matter of (.+?) \[Applicant Tenant\] and (.+?) \[Respondent Landlord\]"
    )
    pattern2 = (
        r"In the matter of (.+?) \[Applicant Landlord\] and (.+?) \[Respondent Tenant\]"
    )

    # Try to find a match using the first pattern
    match1 = re.search(pattern1, text)

    # If the first pattern doesn't match, try the second pattern
    if match1:
        # Extract the names for 'Applicant Tenant' and 'Respondent Landlord' using the first pattern
        tenant_name = match1.group(1)
        landlord_name = match1.group(2)
        tenant_role = "Applicant"
        landlord_role = "Respondent"
        print(f"Tenant: {tenant_name} / {tenant_role}")
        print(f"Landlord: {landlord_name} / {landlord_role}")
    else:
        match2 = re.search(pattern2, text)
        if match2:
            # Extract the names for 'Applicant Landlord' and 'Respondent Tenant' using the second pattern
            landlord_name = match2.group(1)
            tenant_name = match2.group(2)
            landlord_role = "Applicant"
            tenant_role = "Respondent"
            print(f"Tenant: {tenant_name} / {tenant_role}")
            print(f"Landlord: {landlord_name} / {landlord_role}")
        else:
            print("Unable to identify applicant and respondent!")

    return tenant_name, tenant_role, landlord_name, landlord_role


def extract_address(text):
    addresses = []

    # Regular expression pattern to match addresses
    address_pattern = r"(?:tenancy|occupation) of the dwelling at (.*?)(?: is| as|\n)"

    # Find match for address in the text (case-insensitive)
    match = re.search(address_pattern, text, re.IGNORECASE)
    address = match.group(1)
    print(f"Address: {address}")

    return address


def find_keywords(text):
    matches = []

    # Read the keywords file
    keywords = read_keywords(keywords_file)

    # Convert the text to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Search file for matches in keywords
    for keyword in keywords:
        # Check if the lowercase keyword exists in the lowercase text
        if keyword.lower() in text_lower:
            matches.append(keyword)

    print(f"Keyword matches: {matches}")

    return matches


def pdf2text(file_path, output_folder, page_numbers=False):
    images = convert_from_path(file_path)

    # Extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

    # Get the number of pages
    page_count = len(images)
    print(f"Pages: {page_count}")

    # Combine text from multiple pages
    combined_text = ""

    # Iterate through pages
    for page_number, image_data in enumerate(images, start=1):
        txt = pytesseract.image_to_string(image_data)

        # Remove form feed character
        txt = txt.replace("\x0c", "")

        # Combine pages and add page numbers if requested
        if page_numbers:
            combined_text += f"Page # {str(page_number)}\n\n"
            combined_text += f"{txt}\n\n"
        else:
            combined_text += f"{txt}"

    # Join lines that don't end with a full stop
    combined_text = join_rows(combined_text)

    # Extract Landlord and Tenant Names
    tenant_name, tenant_role, landlord_name, landlord_role = extract_names(
        combined_text
    )

    # Extract addresses
    address = extract_address(combined_text)

    # TODO: Should this be using combined_text?
    # List determination keywords
    keywords_list = find_keywords(txt)

    # Write combined text to a file
    output_file_path = os.path.join(output_folder, f"{base_name}.txt")
    with open(output_file_path, mode="w") as f:
        f.write(combined_text)

    # Write to CSV file
    with open(csv_output_file_path, mode="a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                file_name,
                page_count,
                os.path.basename(output_file_path),
                keywords_list,
                address,
                tenant_name,
                tenant_role,
                landlord_name,
                landlord_role,
            ]
        )


def process_determination_orders(input_folder, output_folder, page_numbers=False):
    file_paths = get_file_paths(input_folder)

    # Write CSV header
    with open(csv_output_file_path, mode="w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                "Input Filename",
                "Page Count",
                "Output Filename",
                "Keywords",
                "Address",
                "Tenant Name",
                "Tenant Role",
                "Landlord Name",
                "Landlord Role",
            ]
        )

    for file_path in file_paths:
        print(f"Processing: {file_path}")
        pdf2text(file_path, output_folder, page_numbers)


process_determination_orders(input_folder, output_folder, page_numbers=False)
