import os
from pdf2image import convert_from_path
import pytesseract

input_folder = "data/input/"
output_folder = "data/output/"


def get_file_paths(input_folder):
    file_paths = []

    # Loop through the files in the input folder
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths


def pdf2text(file_path, output_folder, page_numbers=False):
    images = convert_from_path(file_path)

    # Extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

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

    # Write combined text to a file
    output_file_path = os.path.join(output_folder, f"{base_name}.txt")
    with open(output_file_path, mode="w") as f:
        f.write(combined_text)


def process_determination_orders(input_folder, output_folder, page_numbers=False):
    file_paths = get_file_paths(input_folder)

    for file_path in file_paths:
        pdf2text(file_path, output_folder, page_numbers)
        print(f"Processed: {file_path}")


process_determination_orders(input_folder, output_folder, page_numbers=False)
