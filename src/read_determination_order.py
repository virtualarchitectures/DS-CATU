import os
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
import pytesseract

file_path = "data/DR1022-80447_Determination_ORder.pdf"

# load the pdf document
doc = convert_from_path(file_path)

path, file_name = os.path.split(file_path)
base_name, extension = os.path.splitext(file_name)

# loop through document pages
for page_number, page_data in enumerate(doc):
    # image_bytes = page_data.tobytes()
    a = np.asarray(page_data)
    img = Image.fromarray(a)
    txt = pytesseract.image_to_string(img)

    print(f"Page # {str(page_number)}\n\n{txt}")

    with open(f"{base_name}.txt", mode="w") as f:
        f.write(txt)
