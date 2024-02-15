import os
from pdf2image import convert_from_path
import pytesseract

file_path = "data/DR1022-80447_Determination_ORder.pdf"


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
    with open(f"data/{base_name}.txt", mode="w") as f:
        f.write(txt)


pdf2text(file_path)
