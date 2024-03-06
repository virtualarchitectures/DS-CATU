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


def pdf2text(file_path):
    # convert the pages of the PDF to a list of PIL images
    images = convert_from_path(file_path)

    # extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

    # loop through document pages
    for page_number, image_data in enumerate(images):
        # extract text from image
        txt = pytesseract.image_to_string(image_data)

        print(f"Page # {str(page_number)}\n\n{txt}")

    # TODO: Combine text from multiple pages

    # write text to file
    with open(f"{output_folder}{base_name}.txt", mode="w") as f:
        f.write(txt)


def process_determination_orders():
    file_paths = get_file_paths(input_folder)

    for file_path in file_paths:
        pdf2text(file_path)
        print(file_paths)


process_determination_orders()
