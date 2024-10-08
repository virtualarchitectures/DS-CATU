import os
import re
import string
import csv
from dateutil import parser
import json
import ollama

input_folder = "data/converted_text/determinations"
keywords_file = "reference/keywords.txt"
csv_output_file_path = "data/summary/determination_details.csv"


def get_file_paths(input_folder):
    file_paths = []

    # Loop through the files in the input folder
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths


def read_keywords(file_path):
    with open(file_path, "r") as file:
        keywords = [line.strip() for line in file.readlines() if line.strip()]
    return keywords


def extract_names(text):
    tenant_name = None
    landlord_name = None
    tenant_role = None
    landlord_role = None
    # Define alternate regular expression patterns
    pattern1 = r"In the matter of (.+?) [\{\(\[]Applican. Tenan.(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden. Land.ord(?:s|\(s\))?[\)\}\]]"
    pattern2 = r"In the matter of (.+?) [\{\(\[]Applican. Land.ord(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden. Tenan.(?:s|\(s\))?[\)\}\]]"
    pattern3 = r"In the matter of (.+?) [\{\(\[]Applican./Responden. Tenan.(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden./Applicant Land.ord(?:s|\(s\))?[\)\}\]]"
    pattern4 = r"In the matter of (.+?) [\{\(\[]Applican./Responden. Land.ord(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden./Applican. Tenan.(?:s|\(s\))?[\)\}\]]"
    pattern5 = r"In the matter of (.+?) [\{\(\[]Tenan.(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Land.ord(?:s|\(s\))?[\)\}\]]"
    pattern6 = r"In the matter of (.+?) [\{\(\[]Land.ord(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Tenan.(?:s|\(s\))?[\)\}\]]"
    pattern7 = r"In the matter of (.+?) [\{\(\[]Appellan. Tenan.(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden. Land.ord(?:s|\(s\))?[\)\}\]]"
    pattern8 = r"In the matter of (.+?) [\{\(\[]Appellan. Land.ord(?:s|\(s\))?[\)\}\]](?: and )?(.+?) [\{\(\[]Responden. Tenan.(?:s|\(s\))?[\)\}\]]"

    # Try to find a match
    match1 = re.search(pattern1, text, re.IGNORECASE)
    match2 = re.search(pattern2, text, re.IGNORECASE)
    match3 = re.search(pattern3, text, re.IGNORECASE)
    match4 = re.search(pattern4, text, re.IGNORECASE)
    match5 = re.search(pattern5, text, re.IGNORECASE)
    match6 = re.search(pattern6, text, re.IGNORECASE)
    match7 = re.search(pattern7, text, re.IGNORECASE)
    match8 = re.search(pattern8, text, re.IGNORECASE)

    # If the first pattern doesn't match, try the second pattern
    if match1:
        # Extract the names for 'Applicant Tenant' and 'Respondent Landlord' using the first pattern
        tenant_name = match1.group(1).strip()
        landlord_name = match1.group(2).strip()
        tenant_role = "Applicant"
        landlord_role = "Respondent"
    elif match2:
        # Extract the names for 'Applicant Landlord' and 'Respondent Tenant' using the second pattern
        landlord_name = match2.group(1).strip()
        tenant_name = match2.group(2).strip()
        tenant_role = "Respondent"
        landlord_role = "Applicant"
    elif match3:
        # Extract the names for 'Applicant/Respondent Tenant' and 'Respondent/Applicant Landlord' using the third pattern
        tenant_name = match3.group(1).strip()
        landlord_name = match3.group(2).strip()
        tenant_role = "Applicant (Assumed)"
        landlord_role = "Respondent (Assumed)"
    elif match4:
        # Extract the names for 'Respondent/Applicant Landlord' and 'Applicant/Respondent Tenant' using the fourth pattern
        landlord_name = match4.group(1).strip()
        tenant_name = match4.group(2).strip()
        tenant_role = "Respondent (Assumed)"
        landlord_role = "Applicant (Assumed)"
    elif match5:
        # Extract the names for 'Tenant' and 'Landlord' using the fifth pattern
        tenant_name = match5.group(1).strip()
        landlord_name = match5.group(2).strip()
        tenant_role = "Applicant (Assumed)"
        landlord_role = "Respondent (Assumed)"
    elif match6:
        # Extract the names for 'Landlord' and 'Tenant' using the sixth pattern
        landlord_name = match6.group(1).strip()
        tenant_name = match6.group(2).strip()
        tenant_role = "Respondent (Assumed)"
        landlord_role = "Applicant (Assumed)"
    elif match7:
        # Extract the names for 'Appellant Tenant' and 'Respondent Landlord' using the first pattern
        tenant_name = match7.group(1).strip()
        landlord_name = match7.group(2).strip()
        tenant_role = "Applicant"
        landlord_role = "Respondent"
    elif match8:
        # Extract the names for 'Appellant Landlord' and 'Respondent Tenant' using the second pattern
        landlord_name = match8.group(1).strip()
        tenant_name = match8.group(2).strip()
        tenant_role = "Respondent"
        landlord_role = "Applicant"
    else:
        print("Unable to identify applicant and respondent!")

    print(f"Tenant: {tenant_name} / {tenant_role}")
    print(f"Landlord: {landlord_name} / {landlord_role}")

    return tenant_name, tenant_role, landlord_name, landlord_role


def extract_address_regex(text):
    addresses = []

    # Regular expression pattern to match addresses
    address_pattern = r"(?:tenancy|occupation|dwelling|dweding|dweiling|property)(?: of | at |(?! by | in | and| shall| agreement| within|[:;.]))(?:.|)(?:the dwelling|the dweding|the dweiling|the property|)(?: of | at |\s)(.*?)(?: is | as | has | also | within | plus | being | to |\n)"

    # Find match for address in the text (case-insensitive)
    match = re.search(address_pattern, text, re.IGNORECASE)
    if match:
        address = match.group(1)
        # Remove leading and trailing whitespace
        address = address.strip()
        # Remove punctuation at the end
        address = address.rstrip(string.punctuation)
        print(f"Address: {address}")
    else:
        address = None
        print("Unable to identify address!")

    return address


def extract_address_ollama(text):
    # Calling for additional information stabilises the model output
    schema = """{
        "Landlord Name(s)": "",
        "Tenant Name(s)": "",
        "Address": "",
        }"""

    payload = f"""
        The following instructions are important and MUST be followed. Please read the following text and fill in the blanks in the JSON schema provided. Please do not respond conversationally. Please do not comment. You should respond with JSON like a REST API. Only return the JSON between curly braces. Respond strictly with valid JSON as this will be parsed directly with the python function json.loads().

        text = ""{text}""

        schema = ""{schema}"" 
        """

    try:
        # Initialise and call Ollama
        response = ollama.generate(
            model="llama3",
            prompt=f"{payload}",
            format="json",
        )

        # Clean and parse response
        response_json = json.loads(re.sub(r"`", "", response["response"]))
        address = response_json.get("Address")
        # Remove leading and trailing whitespace
        address = address.strip()
        # Remove punctuation at the end
        address = address.rstrip(string.punctuation)
        print(f"Address: {address}")
    except:
        address = None
        print("Unable to identify address!")

    return address


def extract_date(text):
    dates = []

    # Regular_expression pattern to match determination date
    date_pattern = (
        r"(?:residential tenancies board on|determination made on)(.*?)(?:\n)"
    )

    # Find match for address in the text (case-insensitive)
    match = re.search(date_pattern, text, re.IGNORECASE)
    if match:
        date = match.group(1)
        # Remove leading and trailing whitespace
        date = date.strip()
        # Remove punctuation at the end
        date = date.rstrip(string.punctuation)
        # Standardise date
        try:
            parsed_date = parser.parse(date)
            date = parsed_date.strftime("%d/%m/%Y")
            print(f"Determination Date: {date}")
        except:
            print("Unable to parse date!")
            date = None
    else:
        date = None
        print("Unable to identify determination date!")

    return date


def find_keywords(text):
    matches = []

    # Read the keywords file
    keywords = read_keywords(keywords_file)

    # Convert the text to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Split the text into words
    words = text_lower.split()

    # Search for matching words and phrases
    for keyword in keywords:
        if re.search(r"\b" + re.escape(keyword).lower() + r"\b", " ".join(words)):
            matches.append(keyword)

    print(f"Keyword matches: {matches}")

    return matches


def read_determination_orders(file_path, address_method):
    # Extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

    # Read the file contents
    with open(file_path, "r") as file:
        text = file.read()

        # Extract Landlord and Tenant Names
        tenant_name, tenant_role, landlord_name, landlord_role = extract_names(text)

        # Extract addresses based on the selected method
        if address_method == "ollama":
            address = extract_address_ollama(text)
        else:
            address = extract_address_regex(text)

        # Extract date
        date = extract_date(text)

        # List determination keywords
        keywords_list = find_keywords(text)

        # Write to CSV file
        with open(csv_output_file_path, mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(
                [
                    file_name,
                    date,
                    keywords_list,
                    address,
                    tenant_name,
                    tenant_role,
                    landlord_name,
                    landlord_role,
                ]
            )


def process_determination_orders(input_folder, address_method):
    file_paths = get_file_paths(input_folder)

    # Write CSV header
    with open(csv_output_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                "Text Filename",
                "Determination Date",
                "Keywords",
                "Address",
                "Tenant Name(s)",
                "Tenant Role",
                "Landlord Name(s)",
                "Landlord Role",
            ]
        )

    for file_path in file_paths:
        print(f"Processing: {file_path}")
        read_determination_orders(file_path, address_method)


process_determination_orders(input_folder, address_method="regex")
